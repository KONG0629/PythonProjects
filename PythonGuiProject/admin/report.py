"""
admin/report.py

Admin Sales Reports page.

UI upgraded to match Admin Dashboard style.

Kept functions:
- Discount affects report revenue.
- Final Total is computed as subtotal - discount.
- Cash and Online sales use the discounted final total.
- Receipt selection shows discounted final total.
- Single receipt uses databases/pdf_receipt_backend.py with prepared discounted rows.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

from theme import *
from datetime import datetime, date, timedelta

from databases.db import get_connection
from databases.pdf_report_backend import generate_sales_report_pdf
from databases.pdf_receipt_backend import generate_receipt_pdf

ctk.set_appearance_mode("light")


MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

MONTH_NUM = {m: i + 1 for i, m in enumerate(MONTHS)}
CURRENT_YEAR = datetime.now().year
YEARS = [str(y) for y in range(2004, CURRENT_YEAR + 6)]


def format_money(value):
    try:
        return f"₱{float(value or 0):,.2f}"
    except Exception:
        return "₱0.00"


def safe_float(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def safe_int(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


def short_text(value, limit=45):
    value = str(value or "")

    if len(value) <= limit:
        return value

    return value[:limit - 1] + "…"


def compute_final_total(subtotal, discount, fallback_total=0):
    subtotal = safe_float(subtotal)
    discount = safe_float(discount)
    fallback_total = safe_float(fallback_total)

    if subtotal <= 0 and fallback_total > 0:
        subtotal = fallback_total + discount

    final_total = subtotal - discount

    if final_total < 0:
        final_total = 0.0

    return final_total


def get_month_last_day(year_value, month_value):
    if month_value == 12:
        return date(year_value, 12, 31)

    return date(year_value, month_value + 1, 1) - timedelta(days=1)


def get_weeks_in_month(year_value, month_value):
    first_day = date(year_value, month_value, 1)
    last_day = get_month_last_day(year_value, month_value)

    weeks = []
    current_start = first_day
    week_number = 1

    while current_start <= last_day:
        current_end = min(current_start + timedelta(days=6), last_day)

        label = (
            f"Week {week_number} "
            f"({current_start.strftime('%b %d')} - {current_end.strftime('%b %d')})"
        )

        weeks.append(label)
        current_start = current_end + timedelta(days=1)
        week_number += 1

    return weeks


def get_discounted_sales_records(start_date, end_date):
    connection = get_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                o.order_id,
                u.full_name AS cashier_name,

                COALESCE(o.subtotal_amount, 0) AS subtotal_amount,
                COALESCE(o.discount_type, 'No Discount') AS discount_type,
                COALESCE(o.discount_amount, 0) AS discount_amount,
                COALESCE(o.total_amount, 0) AS total_amount,

                o.order_status,
                o.created_at,
                o.accepted_at AS sale_date,

                COALESCE(p.amount_received, 0) AS amount_received,
                COALESCE(p.change_amount, 0) AS change_amount,
                COALESCE(p.payment_method, 'Cash') AS payment_method,
                COALESCE(p.online_reference, '') AS online_reference,

                oi.order_item_id,
                oi.product_id,
                oi.product_name,
                oi.price,
                oi.price AS unit_price,
                oi.quantity,
                oi.subtotal

            FROM orders o
            JOIN users u
                ON o.cashier_id = u.user_id
            LEFT JOIN payments p
                ON o.order_id = p.order_id
            JOIN order_items oi
                ON o.order_id = oi.order_id

            WHERE o.order_status = 'accepted'
            AND DATE(o.accepted_at) BETWEEN %s AND %s

            ORDER BY o.accepted_at DESC, o.order_id DESC, oi.order_item_id ASC
            """,
            (start_date, end_date)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


class AdminReport(ctk.CTk):
    def __init__(self, user_name="Admin"):
        super().__init__()

        self.user_name = user_name
        self.period_var = tk.StringVar(master=self, value="Week")
        self.search_var = tk.StringVar(master=self)

        self._raw_sales = []
        self._grouped_orders = []
        self._filtered_orders = []

        self.title("Admin — Sales Reports")
        self.configure(fg_color=BG)
        self.attributes("-fullscreen", True)

        self._build()

    # ============================================================
    # NAVIGATION
    # ============================================================
    def _nav(self, module):
        try:
            self.configure(cursor="watch")
            self.update_idletasks()

            app = None

            if module == "dashboard":
                from admin.adminDashboard import AdminDashboard
                app = AdminDashboard(self.user_name)
            elif module == "products":
                from admin.productsTotal import AdminProductsTotal
                app = AdminProductsTotal(self.user_name)
            elif module == "mostbuyed":
                from admin.mostBuyproduct import MostBuyedProducts
                app = MostBuyedProducts(self.user_name)
            elif module == "orders":
                from admin.orders import AdminOrders
                app = AdminOrders(self.user_name)
            elif module == "report":
                from admin.report import AdminReport
                app = AdminReport(self.user_name)
            elif module == "accounts":
                from admin.manageAccounts import ManageAccounts
                app = ManageAccounts(self.user_name)


            elif module == "history":

                from admin.adminHistory import AdminHistory

                app = AdminHistory(self.user_name)


            self.destroy()

            if app:
                app.mainloop()

        except Exception as e:
            self.configure(cursor="")
            messagebox.showerror(
                "Navigation Error",
                f"Unable to open module.\n\n{e}",
                parent=self
            )

    # ============================================================
    # UI HELPERS
    # ============================================================
    def _combo(self, parent, var, values, width_chars, command=None):
        cb = ttk.Combobox(
            parent,
            textvariable=var,
            values=values,
            width=width_chars,
            state="readonly",
            font=("Segoe UI", 10)
        )

        if command:
            cb.bind("<<ComboboxSelected>>", command)
        else:
            cb.bind("<<ComboboxSelected>>", lambda event: self._load())

        return cb

    def _make_kpi_card(self, parent, index, label, value, color, subtext=""):
        card = tk.Frame(parent, bg=color)
        card.grid(row=0, column=index, sticky="ew", padx=5)
        parent.columnconfigure(index, weight=1)

        tk.Label(
            card,
            text=label,
            font=("Segoe UI", 10, "bold"),
            bg=color,
            fg=CREAM
        ).pack(pady=(11, 1), padx=10)

        tk.Label(
            card,
            text=value,
            font=("Georgia", 17, "bold"),
            bg=color,
            fg=WHITE
        ).pack(pady=(0, 1))

        tk.Label(
            card,
            text=subtext,
            font=("Segoe UI", 8, "italic"),
            bg=color,
            fg=CREAM
        ).pack(pady=(0, 10), padx=10)

    def _clear_search(self):
        self.search_var.set("")
        self._apply_search()

    # ============================================================
    # BUILD UI
    # ============================================================
    def _build(self):
        nav = [
            ("dashboard", "🏠", "Dashboard", lambda: None),
            ("products", "📋", "Products", lambda: self._nav("products")),
            ("mostbuyed", "🏆", "Best Products", lambda: self._nav("mostbuyed")),
            ("orders", "📦", "Orders", lambda: self._nav("orders")),
            ("report", "📑", "Reports", lambda: self._nav("report")),
            ("accounts", "👥", "Manage Accounts", lambda: self._nav("accounts")),
            ("history", "🕘", "History", lambda: self._nav("history")),
        ]

        make_sidebar(self, self.user_name, "Administrator", nav, "report")

        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="right", fill="both", expand=True)

        # ========================================================
        # HEADER
        # ========================================================
        hdr = tk.Frame(self.main, bg=CREAM, height=74)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        left_hdr = tk.Frame(hdr, bg=CREAM)
        left_hdr.pack(side="left", padx=24, pady=10)

        tk.Label(
            left_hdr,
            text="📑 Sales Reports",
            font=F_TITLE,
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w")

        tk.Label(
            left_hdr,
            text="View accepted sales, discounted totals, payment breakdown, and export reports.",
            font=("Segoe UI", 10, "italic"),
            bg=CREAM,
            fg=TEXT
        ).pack(anchor="w")

        right_hdr = tk.Frame(hdr, bg=CREAM)
        right_hdr.pack(side="right", padx=20, pady=10)

        tk.Label(
            right_hdr,
            text=datetime.now().strftime("%B %d, %Y"),
            font=("Segoe UI", 11, "bold"),
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="e")

        tk.Label(
            right_hdr,
            text=datetime.now().strftime("%A"),
            font=F_SMALL,
            bg=CREAM,
            fg=TEXT
        ).pack(anchor="e")

        # ========================================================
        # KPI CARDS
        # ========================================================
        self.sum_f = tk.Frame(self.main, bg=BG)
        self.sum_f.pack(fill="x", padx=22, pady=(14, 10))

        # ========================================================
        # REPORT TOOLS
        # ========================================================
        action_card = tk.Frame(
            self.main,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        action_card.pack(fill="x", padx=22, pady=(0, 10))

        tk.Label(
            action_card,
            text="Report Tools",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left", padx=14, pady=12)

        tk.Label(
            action_card,
            text="Generate receipt for one order or export the full report as PDF.",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=10)

        gold_btn(
            action_card,
            "🧾 Generate Receipt",
            self._open_receipt_export_window,
            height=34,
            width=165
        ).pack(side="right", padx=(4, 12), pady=10)

        gold_btn(
            action_card,
            "⬇️ Report PDF",
            self._export_pdf,
            height=34,
            width=130
        ).pack(side="right", padx=4, pady=10)

        primary_btn(
            action_card,
            "🔄 Refresh",
            self._load,
            height=34,
            width=110
        ).pack(side="right", padx=4, pady=10)

        # ========================================================
        # FILTER CARD
        # ========================================================
        filter_card = tk.Frame(
            self.main,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        filter_card.pack(fill="x", padx=22, pady=(0, 10))

        tk.Label(
            filter_card,
            text="Filters",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left", padx=14, pady=12)

        tk.Label(
            filter_card,
            text="Period:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(8, 4))

        for period in ("Week", "Month", "Year"):
            tk.Radiobutton(
                filter_card,
                text=period,
                variable=self.period_var,
                value=period,
                font=F_BODY,
                bg=CARD_BG,
                fg=DARK_RED,
                selectcolor=GOLD,
                activebackground=CARD_BG,
                activeforeground=DARK_RED,
                command=self._on_period
            ).pack(side="left", padx=5)

        self.pick = tk.Frame(filter_card, bg=CARD_BG)
        self.pick.pack(side="left", padx=14)

        now = datetime.now()

        self.wk_f = tk.Frame(self.pick, bg=CARD_BG)
        self.wk_y = tk.StringVar(master=self, value=str(now.year))
        self.wk_m = tk.StringVar(master=self, value=MONTHS[now.month - 1])
        self.wk_w = tk.StringVar(master=self)

        current_week_values = get_weeks_in_month(now.year, now.month)
        self.wk_w.set(current_week_values[0])

        tk.Label(
            self.wk_f,
            text="Month:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

        self._combo(
            self.wk_f,
            self.wk_m,
            MONTHS,
            12,
            command=lambda event: self._refresh_week_choices()
        ).pack(side="left", padx=3)

        self._combo(
            self.wk_f,
            self.wk_y,
            YEARS,
            6,
            command=lambda event: self._refresh_week_choices()
        ).pack(side="left", padx=3)

        tk.Label(
            self.wk_f,
            text="Week:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(10, 0))

        self.week_combo = self._combo(
            self.wk_f,
            self.wk_w,
            current_week_values,
            24
        )
        self.week_combo.pack(side="left", padx=3)

        self.mo_f = tk.Frame(self.pick, bg=CARD_BG)
        self.mo_m = tk.StringVar(master=self, value=MONTHS[now.month - 1])
        self.mo_y = tk.StringVar(master=self, value=str(now.year))

        tk.Label(
            self.mo_f,
            text="Month:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

        self._combo(self.mo_f, self.mo_m, MONTHS, 12).pack(side="left", padx=3)
        self._combo(self.mo_f, self.mo_y, YEARS, 6).pack(side="left", padx=3)

        self.yr_f = tk.Frame(self.pick, bg=CARD_BG)
        self.yr_y = tk.StringVar(master=self, value=str(now.year))

        tk.Label(
            self.yr_f,
            text="Year:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

        self._combo(self.yr_f, self.yr_y, YEARS, 6).pack(side="left", padx=3)

        # ========================================================
        # RANGE + SEARCH CARD
        # ========================================================
        info_card = tk.Frame(
            self.main,
            bg="#FFF8E1",
            highlightbackground=GOLD,
            highlightthickness=1
        )
        info_card.pack(fill="x", padx=22, pady=(0, 10))

        self.range_lbl = tk.Label(
            info_card,
            text="",
            font=("Segoe UI", 10, "italic"),
            bg="#FFF8E1",
            fg=TEXT
        )
        self.range_lbl.pack(side="left", padx=14, pady=10)

        search_box = tk.Frame(info_card, bg="#FFF8E1")
        search_box.pack(side="right", padx=12, pady=8)

        tk.Label(
            search_box,
            text="🔍",
            font=("Segoe UI", 12),
            bg="#FFF8E1",
            fg=TEXT
        ).pack(side="left", padx=(0, 4))

        self.search_entry = ctk.CTkEntry(
            search_box,
            textvariable=self.search_var,
            width=280,
            height=34,
            placeholder_text="Search order, product, cashier, payment...",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=("Segoe UI", 10),
            corner_radius=8
        )
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", lambda event: self._apply_search())

        gold_btn(
            search_box,
            "Clear",
            self._clear_search,
            height=34,
            width=75
        ).pack(side="left", padx=4)

        # ========================================================
        # TABLE TITLE
        # ========================================================
        table_title = tk.Frame(self.main, bg=BG)
        table_title.pack(fill="x", padx=22)

        tk.Label(
            table_title,
            text="Accepted Sales Records",
            font=F_HEAD,
            bg=BG,
            fg=DARK_RED
        ).pack(side="left")

        self.result_lbl = tk.Label(
            table_title,
            text="",
            font=("Segoe UI", 10, "italic"),
            bg=BG,
            fg=TEXT
        )
        self.result_lbl.pack(side="left", padx=10)

        # ========================================================
        # TABLE
        # ========================================================
        tbl = tk.Frame(
            self.main,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        tbl.pack(fill="both", expand=True, padx=22, pady=(4, 20))

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "RPT.Treeview",
            background=CARD_BG,
            fieldbackground=CARD_BG,
            foreground=TEXT,
            rowheight=38,
            font=("Segoe UI", 10)
        )

        style.configure(
            "RPT.Treeview.Heading",
            background=SIDEBAR,
            foreground=WHITE,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )

        style.map(
            "RPT.Treeview",
            background=[("selected", GOLD)],
            foreground=[("selected", DARK_RED)]
        )

        cols = (
            "Order ID",
            "Products",
            "Total Qty",
            "Subtotal",
            "Discount",
            "Final Total",
            "Payment",
            "Cashier",
            "Date"
        )

        widths = [85, 350, 80, 110, 110, 120, 120, 140, 150]

        self.tree = ttk.Treeview(
            tbl,
            columns=cols,
            show="headings",
            style="RPT.Treeview",
            selectmode="extended"
        )

        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center", minwidth=60)

        vsb = ttk.Scrollbar(tbl, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbl, orient="horizontal", command=self.tree.xview)

        self.tree.configure(
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

        self.tree.tag_configure("odd", background=ODD_ROW)
        self.tree.tag_configure("even", background=CARD_BG)

        self._on_period()

    # ============================================================
    # FILTERS
    # ============================================================
    def _refresh_week_choices(self):
        year_value = int(self.wk_y.get())
        month_value = MONTH_NUM[self.wk_m.get()]

        week_values = get_weeks_in_month(year_value, month_value)

        self.week_combo.configure(values=week_values)
        self.wk_w.set(week_values[0])

        self._load()

    def _on_period(self):
        for f in (self.wk_f, self.mo_f, self.yr_f):
            f.pack_forget()

        if self.period_var.get() == "Week":
            self.wk_f.pack(side="left")
        elif self.period_var.get() == "Month":
            self.mo_f.pack(side="left")
        else:
            self.yr_f.pack(side="left")

        self._load()

    def _get_date_range(self):
        period = self.period_var.get()

        if period == "Week":
            year_value = int(self.wk_y.get())
            month_value = MONTH_NUM[self.wk_m.get()]
            selected_week = self.wk_w.get()

            week_number = int(selected_week.split()[1])

            month_start = date(year_value, month_value, 1)
            month_end = get_month_last_day(year_value, month_value)

            start_date = month_start + timedelta(days=(week_number - 1) * 7)
            end_date = min(start_date + timedelta(days=6), month_end)

            return start_date, end_date

        if period == "Month":
            month_value = MONTH_NUM[self.mo_m.get()]
            year_value = int(self.mo_y.get())

            start_date = date(year_value, month_value, 1)
            end_date = get_month_last_day(year_value, month_value)

            return start_date, end_date

        year_value = int(self.yr_y.get())
        return date(year_value, 1, 1), date(year_value, 12, 31)

    # ============================================================
    # GROUPING / SEARCH
    # ============================================================
    def _group_sales_by_order(self, rows):
        grouped = {}

        for row in rows:
            order_id = str(row.get("order_id"))

            if order_id not in grouped:
                grouped[order_id] = {
                    "order_id": order_id,
                    "products": [],
                    "total_qty": 0,
                    "item_subtotal": 0.0,
                    "discount": safe_float(row.get("discount_amount")),
                    "db_subtotal": safe_float(row.get("subtotal_amount")),
                    "db_total": safe_float(row.get("total_amount")),
                    "final_total": 0.0,
                    "cashier_name": row.get("cashier_name"),
                    "sale_date": row.get("sale_date") or row.get("created_at"),
                    "payment_method": row.get("payment_method") or "Cash",
                    "online_reference": row.get("online_reference") or "",
                    "amount_received": safe_float(row.get("amount_received")),
                    "change_amount": safe_float(row.get("change_amount")),
                    "discount_type": row.get("discount_type") or "No Discount",
                    "rows": []
                }

            product_name = str(row.get("product_name") or "")
            quantity = safe_int(row.get("quantity"))
            item_subtotal = safe_float(row.get("subtotal"))

            grouped[order_id]["products"].append(f"{product_name} x{quantity}")
            grouped[order_id]["total_qty"] += quantity
            grouped[order_id]["item_subtotal"] += item_subtotal
            grouped[order_id]["rows"].append(row)

        for order in grouped.values():
            subtotal = safe_float(order["item_subtotal"])

            if subtotal <= 0:
                subtotal = safe_float(order["db_subtotal"])

            if subtotal <= 0:
                subtotal = safe_float(order["db_total"]) + safe_float(order["discount"])

            discount = safe_float(order["discount"])

            final_total = compute_final_total(
                subtotal=subtotal,
                discount=discount,
                fallback_total=order["db_total"]
            )

            order["subtotal"] = subtotal
            order["final_total"] = final_total

        return list(grouped.values())

    def _order_matches_search(self, order, keyword):
        if not keyword:
            return True

        products_text = ", ".join(order.get("products", []))
        sale_date = order.get("sale_date")
        sale_date_text = str(sale_date)[:16] if sale_date else ""

        searchable = " ".join([
            str(order.get("order_id", "")),
            products_text,
            str(order.get("total_qty", "")),
            format_money(order.get("subtotal")),
            format_money(order.get("discount")),
            format_money(order.get("final_total")),
            str(order.get("payment_method", "")),
            str(order.get("cashier_name", "")),
            sale_date_text,
        ]).lower()

        return keyword.lower() in searchable

    def _apply_search(self):
        keyword = self.search_var.get().strip().lower()

        self._filtered_orders = [
            order for order in self._grouped_orders
            if self._order_matches_search(order, keyword)
        ]

        self._load_table(self._filtered_orders)

    # ============================================================
    # LOAD DATA
    # ============================================================
    def _load(self):
        try:
            start_date, end_date = self._get_date_range()

            self.range_lbl.config(
                text=f"Showing accepted orders from {start_date} to {end_date}"
            )

            self._raw_sales = get_discounted_sales_records(start_date, end_date)
            self._grouped_orders = self._group_sales_by_order(self._raw_sales)

            self._update_summary_cards(self._grouped_orders)
            self._apply_search()

        except Exception as e:
            messagebox.showerror(
                "Load Error",
                f"Unable to load reports.\n\n{e}",
                parent=self
            )

    def _update_summary_cards(self, grouped_orders):
        for w in self.sum_f.winfo_children():
            w.destroy()

        revenue = sum(safe_float(order["final_total"]) for order in grouped_orders)
        discounts = sum(safe_float(order["discount"]) for order in grouped_orders)
        transactions = len(grouped_orders)
        qty = sum(safe_int(order["total_qty"]) for order in grouped_orders)

        cash_sales = sum(
            safe_float(order["final_total"])
            for order in grouped_orders
            if str(order.get("payment_method") or "Cash").lower() == "cash"
        )

        online_sales = sum(
            safe_float(order["final_total"])
            for order in grouped_orders
            if str(order.get("payment_method") or "").lower() == "online payment"
        )

        avg_order = revenue / transactions if transactions > 0 else 0

        stats = [
            ("💰 Revenue", format_money(revenue), SIDEBAR, "After discounts"),
            ("🏷 Discounts", format_money(discounts), "#B03A2E", "Total discount"),
            ("🧾 Orders", str(transactions), "#27AE60", "Accepted only"),
            ("🔢 Items Sold", str(qty), GOLD, "Total quantity"),
            ("💵 Cash", format_money(cash_sales), "#6C3483", "Cash sales"),
            ("📱 Online", format_money(online_sales), "#2874A6", "Online sales"),
            ("📊 Avg. Order", format_money(avg_order), "#CA6F1E", "Revenue/order"),
        ]

        for i, (label, value, color, subtext) in enumerate(stats):
            self._make_kpi_card(self.sum_f, i, label, value, color, subtext)

    def _load_table(self, grouped_orders):
        self.tree.delete(*self.tree.get_children())

        self.result_lbl.configure(text=f"{len(grouped_orders)} order(s) shown")

        if not grouped_orders:
            self.tree.insert(
                "",
                "end",
                values=(
                    "—",
                    "No accepted orders found",
                    "0",
                    "₱0.00",
                    "₱0.00",
                    "₱0.00",
                    "—",
                    "—",
                    "—"
                ),
                tags=("even",)
            )
            return

        for i, order in enumerate(grouped_orders):
            sale_date = order.get("sale_date")
            sale_date_text = str(sale_date)[:16] if sale_date else ""
            products_text = ", ".join(order["products"])

            self.tree.insert(
                "",
                "end",
                iid=str(order["order_id"]),
                values=(
                    order["order_id"],
                    short_text(products_text, 80),
                    order["total_qty"],
                    format_money(order["subtotal"]),
                    format_money(order["discount"]),
                    format_money(order["final_total"]),
                    order.get("payment_method") or "Cash",
                    order["cashier_name"],
                    sale_date_text
                ),
                tags=("odd" if i % 2 else "even",)
            )

    # ============================================================
    # RECEIPT GROUPING / PREP
    # ============================================================
    def _group_receipt_orders(self, receipt_rows):
        grouped = {}

        for row in receipt_rows:
            order_id = str(row.get("order_id"))

            if order_id not in grouped:
                grouped[order_id] = {
                    "order_id": order_id,
                    "cashier_name": row.get("cashier_name"),
                    "sale_date": row.get("sale_date") or row.get("created_at"),
                    "subtotal_amount": 0.0,
                    "discount_type": row.get("discount_type") or "No Discount",
                    "discount_amount": safe_float(row.get("discount_amount")),
                    "total_amount": safe_float(row.get("total_amount")),
                    "payment_method": row.get("payment_method") or "Cash",
                    "online_reference": row.get("online_reference") or "",
                    "amount_received": safe_float(row.get("amount_received")),
                    "change_amount": safe_float(row.get("change_amount")),
                    "items_count": 0,
                    "rows": []
                }

            grouped[order_id]["items_count"] += safe_int(row.get("quantity"))
            grouped[order_id]["subtotal_amount"] += safe_float(row.get("subtotal"))
            grouped[order_id]["rows"].append(row)

        for info in grouped.values():
            info["final_total"] = compute_final_total(
                subtotal=info["subtotal_amount"],
                discount=info["discount_amount"],
                fallback_total=info["total_amount"]
            )

            payment_method = str(info.get("payment_method") or "Cash")

            if payment_method.lower() == "online payment":
                info["amount_received"] = info["final_total"]
                info["change_amount"] = 0.0
            else:
                if info["amount_received"] <= 0:
                    info["amount_received"] = info["final_total"]

                info["change_amount"] = info["amount_received"] - info["final_total"]

                if info["change_amount"] < 0:
                    info["change_amount"] = 0.0

        return grouped

    def _prepare_receipt_rows_for_pdf(self, order_info):
        prepared_rows = []

        subtotal_amount = safe_float(order_info.get("subtotal_amount"))
        discount_amount = safe_float(order_info.get("discount_amount"))
        final_total = safe_float(order_info.get("final_total"))

        payment_method = order_info.get("payment_method") or "Cash"
        amount_received = safe_float(order_info.get("amount_received"))
        change_amount = safe_float(order_info.get("change_amount"))

        if str(payment_method).lower() == "online payment":
            amount_received = final_total
            change_amount = 0.0
        else:
            if amount_received <= 0:
                amount_received = final_total

            change_amount = amount_received - final_total

            if change_amount < 0:
                change_amount = 0.0

        for row in order_info["rows"]:
            new_row = dict(row)

            new_row["unit_price"] = row.get("unit_price") or row.get("price")
            new_row["subtotal"] = safe_float(row.get("subtotal"))

            new_row["subtotal_amount"] = subtotal_amount
            new_row["discount_type"] = order_info.get("discount_type") or "No Discount"
            new_row["discount_amount"] = discount_amount

            new_row["total_amount"] = final_total
            new_row["final_total"] = final_total
            new_row["grand_total"] = final_total
            new_row["net_total"] = final_total

            new_row["payment_method"] = payment_method
            new_row["online_reference"] = order_info.get("online_reference") or ""

            new_row["amount_received"] = amount_received
            new_row["change_amount"] = change_amount

            prepared_rows.append(new_row)

        return prepared_rows

    # ============================================================
    # RECEIPT WINDOW
    # ============================================================
    def _open_receipt_export_window(self):
        try:
            start_date, end_date = self._get_date_range()
            receipt_rows = get_discounted_sales_records(start_date, end_date)

            if not receipt_rows:
                messagebox.showwarning(
                    "No Data",
                    "No receipt data available for this period.",
                    parent=self
                )
                return

            grouped_orders = self._group_receipt_orders(receipt_rows)

            win = tk.Toplevel(self)
            win.title("Generate Receipt")
            win.configure(bg=BG)
            win.geometry("1050x620")
            win.resizable(False, False)
            win.transient(self)
            win.grab_set()

            win.update_idletasks()
            x = (win.winfo_screenwidth() // 2) - (1050 // 2)
            y = (win.winfo_screenheight() // 2) - (620 // 2)
            win.geometry(f"1050x620+{x}+{y}")

            header = tk.Frame(win, bg=SIDEBAR, height=64)
            header.pack(fill="x")
            header.pack_propagate(False)

            tk.Label(
                header,
                text="🧾 Generate Receipt",
                font=("Georgia", 18, "bold"),
                bg=SIDEBAR,
                fg=CREAM
            ).pack(side="left", padx=22, pady=14)

            tk.Label(
                header,
                text="Select one accepted order to generate a receipt PDF.",
                font=("Segoe UI", 10, "italic"),
                bg=SIDEBAR,
                fg=WHITE
            ).pack(side="left", padx=10, pady=18)

            body = tk.Frame(win, bg=BG)
            body.pack(fill="both", expand=True, padx=24, pady=16)

            table_frame = tk.Frame(
                body,
                bg=CARD_BG,
                highlightbackground=BORDER,
                highlightthickness=1
            )
            table_frame.pack(fill="both", expand=True)

            order_cols = (
                "Order ID",
                "Products",
                "Items",
                "Subtotal",
                "Discount",
                "Final Total",
                "Payment",
                "Cashier",
                "Date"
            )

            order_tree = ttk.Treeview(
                table_frame,
                columns=order_cols,
                show="headings",
                style="RPT.Treeview",
                selectmode="browse"
            )

            widths = [75, 270, 60, 105, 105, 115, 110, 130, 135]

            for col, width in zip(order_cols, widths):
                order_tree.heading(col, text=col)
                order_tree.column(col, width=width, anchor="center")

            order_scroll = ttk.Scrollbar(
                table_frame,
                orient="vertical",
                command=order_tree.yview
            )
            order_hscroll = ttk.Scrollbar(
                table_frame,
                orient="horizontal",
                command=order_tree.xview
            )

            order_tree.configure(
                yscrollcommand=order_scroll.set,
                xscrollcommand=order_hscroll.set
            )

            order_scroll.pack(side="right", fill="y")
            order_hscroll.pack(side="bottom", fill="x")
            order_tree.pack(fill="both", expand=True, padx=4, pady=4)

            for order_id, info in grouped_orders.items():
                sale_date = info.get("sale_date")
                sale_date_text = str(sale_date)[:16] if sale_date else ""

                products_text = ", ".join(
                    f"{row.get('product_name')} x{safe_int(row.get('quantity'))}"
                    for row in info["rows"]
                )

                order_tree.insert(
                    "",
                    "end",
                    iid=str(order_id),
                    values=(
                        order_id,
                        short_text(products_text, 70),
                        info.get("items_count"),
                        format_money(info.get("subtotal_amount")),
                        format_money(info.get("discount_amount")),
                        format_money(info.get("final_total")),
                        info.get("payment_method") or "Cash",
                        info.get("cashier_name"),
                        sale_date_text
                    )
                )

            btns = tk.Frame(win, bg=BG)
            btns.pack(fill="x", padx=24, pady=(0, 18))

            tk.Label(
                btns,
                text="Tip: Select one order from the table above before generating a receipt.",
                font=("Segoe UI", 9, "italic"),
                bg=BG,
                fg=TEXT
            ).pack(side="left")

            def generate_selected_receipt():
                try:
                    selected = list(order_tree.selection())

                    if len(selected) != 1:
                        messagebox.showwarning(
                            "Select One Order",
                            "Please select one order first.",
                            parent=win
                        )
                        return

                    order_id = selected[0]
                    order_info = grouped_orders[order_id]

                    path = filedialog.asksaveasfilename(
                        parent=win,
                        defaultextension=".pdf",
                        filetypes=[("PDF files", "*.pdf")],
                        initialfile=f"Receipt_Order_{order_id}.pdf"
                    )

                    if not path:
                        return

                    if not path.lower().endswith(".pdf"):
                        path += ".pdf"

                    rows_to_print = self._prepare_receipt_rows_for_pdf(order_info)

                    generate_receipt_pdf(
                        rows=rows_to_print,
                        filename=path,
                        generated_by=self.user_name,
                        start_date=start_date,
                        end_date=end_date
                    )

                    win.destroy()

                    messagebox.showinfo(
                        "Exported",
                        f"Receipt PDF saved to:\n{path}",
                        parent=self
                    )

                except Exception as e:
                    messagebox.showerror(
                        "Receipt Failed",
                        f"Unable to generate receipt.\n\n{e}",
                        parent=win
                    )

            gold_btn(
                btns,
                "🧾 Generate Receipt",
                generate_selected_receipt,
                height=38,
                width=170
            ).pack(side="right", padx=5)

            danger_btn(
                btns,
                "Cancel",
                win.destroy,
                height=38,
                width=100
            ).pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror(
                "Receipt Window Error",
                f"Unable to open receipt generator.\n\n{e}",
                parent=self
            )

    # ============================================================
    # EXPORT REPORT PDF
    # ============================================================
    def _export_pdf(self):
        try:
            start_date, end_date = self._get_date_range()

            path = filedialog.asksaveasfilename(
                parent=self,
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"SalesReport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )

            if not path:
                return

            if not path.lower().endswith(".pdf"):
                path += ".pdf"

            generate_sales_report_pdf(
                start_date,
                end_date,
                filename=path,
                generated_by=self.user_name
            )

            messagebox.showinfo(
                "Exported",
                f"Sales report saved to:\n{path}",
                parent=self
            )

        except Exception as e:
            messagebox.showerror(
                "Export Failed",
                f"Unable to export PDF.\n\n{e}",
                parent=self
            )


if __name__ == "__main__":
    AdminReport("Admin").mainloop()