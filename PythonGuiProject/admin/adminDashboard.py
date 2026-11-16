"""
admin/adminDashboard.py

Upgraded Admin Dashboard connected to MySQL database through report_backend.py.

Features:
- Fullscreen admin dashboard
- KPI cards for sales, orders, items sold, average order, and pending orders
- Collapsible date filter for Day, Week, Month, and Year
- Sales records grouped by order_id
- Sales trend line graph
- Pie chart for completed vs pending orders
- Bar graph for top-selling products
- Quick insights panel
- Quick action buttons
- Searchable sales records table
- Uses only Tkinter Canvas for charts, no extra graph library needed
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from theme import *

from datetime import datetime, date
import calendar
from collections import defaultdict

from databases.report_backend import (
    get_dashboard_sales_records,
    get_pending_orders_count,
    get_sales_dates_for_month
)

ctk.set_appearance_mode("light")


MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

CURRENT_YEAR = datetime.now().year
YEARS = [str(y) for y in range(2004, CURRENT_YEAR + 6)]
MONTH_NUM = {month_name: index + 1 for index, month_name in enumerate(MONTHS)}

CHART_COLORS = [
    "#7B1E1E",
    "#D4A017",
    "#27AE60",
    "#6C3483",
    "#B03A2E",
    "#2874A6",
    "#CA6F1E",
    "#117864"
]


def format_money(value):
    try:
        return f"₱{float(value or 0):,.2f}"
    except Exception:
        return "₱0.00"


def safe_int(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


def safe_float(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def short_text(value, limit=42):
    value = str(value or "")

    if len(value) <= limit:
        return value

    return value[:limit - 1] + "…"


def get_week_ranges(year, month):
    _, days_in_month = calendar.monthrange(year, month)

    ranges = []
    starts = list(range(1, days_in_month + 1, 7))

    for index, start_day in enumerate(starts):
        end_day = min(start_day + 6, days_in_month)
        label = f"Week {index + 1} ({start_day}–{end_day})"
        ranges.append((label, start_day, end_day))

    return ranges


class AdminDashboard(ctk.CTk):
    def __init__(self, user_name="Admin"):
        super().__init__()

        self.user_name = user_name

        self.period_var = tk.StringVar(master=self, value="Day")
        self.search_var = tk.StringVar(master=self)

        now = datetime.now()
        self._cal_year = now.year
        self._cal_month = now.month
        self._sel_day = now.day
        self._sel_week = 0

        self._filter_open = False
        self.grouped_orders = []
        self.filtered_orders = []

        self.title("Admin — Dashboard")
        self.configure(fg_color=BG)
        self.attributes("-fullscreen", True)

        self._build()

    # ============================================================
    # DATE RANGE
    # ============================================================
    def _get_date_range(self):
        period = self.period_var.get()
        year = self._cal_year
        month = self._cal_month

        if period == "Day":
            start_date = date(year, month, self._sel_day)
            end_date = start_date

        elif period == "Week":
            week_ranges = get_week_ranges(year, month)

            if self._sel_week < len(week_ranges):
                _, start_day, end_day = week_ranges[self._sel_week]
            else:
                start_day, end_day = 1, 7

            start_date = date(year, month, start_day)
            end_date = date(year, month, end_day)

        elif period == "Month":
            _, days_in_month = calendar.monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, days_in_month)

        else:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

        return start_date, end_date

    def _get_sales_records(self):
        start_date, end_date = self._get_date_range()
        return get_dashboard_sales_records(start_date, end_date)

    def _get_pending_orders_count(self):
        return get_pending_orders_count()

    def _get_sales_dates_for_month(self):
        return get_sales_dates_for_month(self._cal_year, self._cal_month)

    # ============================================================
    # DATA PROCESSING
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
                    "total": 0.0,
                    "cashier_name": row.get("cashier_name"),
                    "sale_date": row.get("sale_date"),
                }

            product_name = str(row.get("product_name") or "Unnamed Product")
            quantity = safe_int(row.get("quantity"))
            subtotal = safe_float(row.get("subtotal"))

            grouped[order_id]["products"].append(f"{product_name} x{quantity}")
            grouped[order_id]["total_qty"] += quantity
            grouped[order_id]["total"] += subtotal

        return list(grouped.values())

    def _get_top_products(self, rows, limit=5):
        products = {}

        for row in rows:
            product_name = str(row.get("product_name") or "Unnamed Product")
            quantity = safe_int(row.get("quantity"))

            if product_name not in products:
                products[product_name] = 0

            products[product_name] += quantity

        sorted_products = sorted(
            products.items(),
            key=lambda item: item[1],
            reverse=True
        )

        return sorted_products[:limit]

    def _get_best_cashier(self, grouped_orders):
        cashier_sales = {}

        for order in grouped_orders:
            cashier = order.get("cashier_name") or "Unknown"
            total = safe_float(order.get("total"))

            if cashier not in cashier_sales:
                cashier_sales[cashier] = 0.0

            cashier_sales[cashier] += total

        if not cashier_sales:
            return "No sales yet", 0.0

        best_cashier = max(cashier_sales.items(), key=lambda item: item[1])
        return best_cashier[0], best_cashier[1]

    def _get_sales_trend(self, grouped_orders):
        trend = defaultdict(float)

        for order in grouped_orders:
            sale_date = order.get("sale_date")
            total = safe_float(order.get("total"))

            if not sale_date:
                continue

            sale_date_text = str(sale_date)

            try:
                sale_date_text = sale_date_text.split(" ")[0]
            except Exception:
                pass

            trend[sale_date_text] += total

        return sorted(trend.items(), key=lambda item: item[0])

    def _get_highest_order(self, grouped_orders):
        if not grouped_orders:
            return None

        return max(grouped_orders, key=lambda order: safe_float(order.get("total")))

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

        make_sidebar(self, self.user_name, "Administrator", nav, "dashboard")

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
            text="🏠 Admin Dashboard",
            font=F_TITLE,
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w")

        tk.Label(
            left_hdr,
            text=f"Welcome back, {self.user_name}. Monitor sales, products, and orders in one place.",
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
        # TOP CONTROL BAR
        # ========================================================
        ctrl = tk.Frame(self.main, bg=BG)
        ctrl.pack(fill="x", padx=22, pady=(12, 6))

        tk.Label(
            ctrl,
            text="View by:",
            font=F_BOLD,
            bg=BG,
            fg=TEXT
        ).pack(side="left")

        for period in ("Day", "Week", "Month", "Year"):
            tk.Radiobutton(
                ctrl,
                text=period,
                variable=self.period_var,
                value=period,
                font=F_BOLD,
                bg=BG,
                fg=DARK_RED,
                selectcolor=GOLD,
                activebackground=BG,
                activeforeground=DARK_RED,
                command=self._on_period
            ).pack(side="left", padx=8)

        self.range_lbl = tk.Label(
            ctrl,
            text="",
            font=("Segoe UI", 10, "italic"),
            bg=BG,
            fg=TEXT
        )
        self.range_lbl.pack(side="left", padx=18)

        self.filter_btn = tk.Button(
            ctrl,
            text="📅 Date Filter ▾",
            font=("Segoe UI", 10, "bold"),
            bg=GOLD,
            fg=DARK_RED,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=7,
            activebackground=SIDE_ACT,
            activeforeground=DARK_RED,
            command=self._toggle_filter_panel
        )
        self.filter_btn.pack(side="right", padx=4)

        primary_btn(
            ctrl,
            "🔄 Refresh",
            self._refresh,
            height=34
        ).pack(side="right", padx=4)

        # ========================================================
        # FILTER PANEL
        # ========================================================
        self.filter_panel = tk.Frame(
            self.main,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.filter_panel.pack_forget()

        # ========================================================
        # KPI CARDS
        # ========================================================
        self.kpi = tk.Frame(self.main, bg=BG)
        self.kpi.pack(fill="x", padx=22, pady=(8, 10))

        # ========================================================
        # QUICK ACTIONS
        # ========================================================
        self.quick_actions = tk.Frame(
            self.main,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.quick_actions.pack(fill="x", padx=22, pady=(0, 10))

        tk.Label(
            self.quick_actions,
            text="Quick Actions",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left", padx=14, pady=12)

        primary_btn(
            self.quick_actions,
            "📦 Manage Orders",
            lambda: self._nav("orders"),
            height=34,
            width=145
        ).pack(side="right", padx=(4, 12), pady=10)

        gold_btn(
            self.quick_actions,
            "📋 Manage Products",
            lambda: self._nav("products"),
            height=34,
            width=155
        ).pack(side="right", padx=4, pady=10)

        primary_btn(
            self.quick_actions,
            "📑 Open Reports",
            lambda: self._nav("report"),
            height=34,
            width=140
        ).pack(side="right", padx=4, pady=10)

        gold_btn(
            self.quick_actions,
            "👥 Accounts",
            lambda: self._nav("accounts"),
            height=34,
            width=120
        ).pack(side="right", padx=4, pady=10)

        # ========================================================
        # MAIN DASHBOARD GRID
        # ========================================================
        self.dashboard_grid = tk.Frame(self.main, bg=BG)
        self.dashboard_grid.pack(fill="x", padx=22, pady=(0, 10))

        left_column = tk.Frame(self.dashboard_grid, bg=BG)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 6))

        right_column = tk.Frame(self.dashboard_grid, bg=BG, width=380)
        right_column.pack(side="right", fill="both", padx=(6, 0))
        right_column.pack_propagate(False)

        self.trend_card = tk.Frame(
            left_column,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.trend_card.pack(fill="x", pady=(0, 10))

        lower_charts = tk.Frame(left_column, bg=BG)
        lower_charts.pack(fill="x")

        self.pie_card = tk.Frame(
            lower_charts,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.pie_card.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.bar_card = tk.Frame(
            lower_charts,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.bar_card.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.insight_card = tk.Frame(
            right_column,
            bg="#FFF8E1",
            highlightbackground=GOLD,
            highlightthickness=1
        )
        self.insight_card.pack(fill="both", expand=True)

        # ========================================================
        # SALES RECORDS TABLE
        # ========================================================
        table_title = tk.Frame(self.main, bg=BG)
        table_title.pack(fill="x", padx=22)

        tk.Label(
            table_title,
            text="Sales Records",
            font=F_HEAD,
            bg=BG,
            fg=DARK_RED
        ).pack(side="left")

        tk.Label(
            table_title,
            text="Grouped by Order ID",
            font=("Segoe UI", 10, "italic"),
            bg=BG,
            fg=TEXT
        ).pack(side="left", padx=10)

        search_box = tk.Frame(table_title, bg=BG)
        search_box.pack(side="right")

        tk.Label(
            search_box,
            text="🔍",
            font=("Segoe UI", 11),
            bg=BG,
            fg=TEXT
        ).pack(side="left", padx=(0, 4))

        self.search_entry = ctk.CTkEntry(
            search_box,
            textvariable=self.search_var,
            width=260,
            height=32,
            placeholder_text="Search order, product, cashier...",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=("Segoe UI", 10),
            corner_radius=8
        )
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", lambda event: self._apply_table_search())

        gold_btn(
            search_box,
            "Clear",
            self._clear_search,
            height=32,
            width=70
        ).pack(side="left", padx=4)

        tbl = tk.Frame(
            self.main,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        tbl.pack(fill="both", expand=True, padx=22, pady=(4, 18))

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Dash.Treeview",
            background=CARD_BG,
            fieldbackground=CARD_BG,
            foreground=TEXT,
            rowheight=38,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Dash.Treeview.Heading",
            background=SIDEBAR,
            foreground=WHITE,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )

        style.map(
            "Dash.Treeview",
            background=[("selected", GOLD)],
            foreground=[("selected", DARK_RED)]
        )

        cols = ("Order ID", "Products", "Total Qty", "Total", "Cashier", "Date")
        widths = [90, 430, 90, 120, 140, 160]

        self.tree = ttk.Treeview(
            tbl,
            columns=cols,
            show="headings",
            style="Dash.Treeview"
        )

        for col_name, width in zip(cols, widths):
            self.tree.heading(col_name, text=col_name)
            self.tree.column(col_name, width=width, anchor="center", minwidth=60)

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

        self._build_filter_panel()
        self._on_period()

    # ============================================================
    # FILTER PANEL
    # ============================================================
    def _toggle_filter_panel(self):
        self._filter_open = not self._filter_open

        if self._filter_open:
            self.filter_panel.pack(
                fill="x",
                padx=22,
                pady=(0, 8),
                after=self.filter_btn.master
            )
            self.filter_btn.config(text="📅 Date Filter ▴")
            self._build_filter_panel()
        else:
            self.filter_panel.pack_forget()
            self.filter_btn.config(text="📅 Date Filter ▾")

    def _build_filter_panel(self):
        for widget in self.filter_panel.winfo_children():
            widget.destroy()

        period = self.period_var.get()
        year = self._cal_year
        month = self._cal_month

        header = tk.Frame(self.filter_panel, bg=SIDEBAR)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Date Filter",
            font=("Georgia", 12, "bold"),
            bg=SIDEBAR,
            fg=CREAM
        ).pack(side="left", padx=12, pady=8)

        tk.Button(
            header,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            bg=SIDEBAR,
            fg=CREAM,
            activebackground=SIDE_HV,
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._toggle_filter_panel
        ).pack(side="right", padx=10)

        body = tk.Frame(self.filter_panel, bg=CARD_BG)
        body.pack(fill="x", padx=14, pady=12)

        tk.Label(
            body,
            text="Month:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

        self._mon_cb = ttk.Combobox(
            body,
            values=MONTHS,
            width=12,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self._mon_cb.set(MONTHS[month - 1])
        self._mon_cb.pack(side="left", padx=(4, 12))

        self._mon_cb.bind(
            "<<ComboboxSelected>>",
            lambda event: self._set_cal_month(MONTH_NUM[self._mon_cb.get()])
        )

        tk.Label(
            body,
            text="Year:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

        self._yr_cb = ttk.Combobox(
            body,
            values=YEARS,
            width=7,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self._yr_cb.set(str(year))
        self._yr_cb.pack(side="left", padx=(4, 12))

        self._yr_cb.bind(
            "<<ComboboxSelected>>",
            lambda event: self._set_cal_year(int(self._yr_cb.get()))
        )

        if period == "Day":
            days = [str(d) for d in range(1, calendar.monthrange(year, month)[1] + 1)]

            tk.Label(
                body,
                text="Day:",
                font=F_BOLD,
                bg=CARD_BG,
                fg=TEXT
            ).pack(side="left")

            self._day_cb = ttk.Combobox(
                body,
                values=days,
                width=5,
                state="readonly",
                font=("Segoe UI", 10)
            )
            self._day_cb.set(str(self._sel_day))
            self._day_cb.pack(side="left", padx=(4, 12))

            self._day_cb.bind(
                "<<ComboboxSelected>>",
                lambda event: self._select_day(int(self._day_cb.get()))
            )

        elif period == "Week":
            week_ranges = get_week_ranges(year, month)
            week_labels = [item[0] for item in week_ranges]

            tk.Label(
                body,
                text="Week:",
                font=F_BOLD,
                bg=CARD_BG,
                fg=TEXT
            ).pack(side="left")

            self._week_cb = ttk.Combobox(
                body,
                values=week_labels,
                width=18,
                state="readonly",
                font=("Segoe UI", 10)
            )

            if self._sel_week >= len(week_labels):
                self._sel_week = 0

            self._week_cb.set(week_labels[self._sel_week])
            self._week_cb.pack(side="left", padx=(4, 12))

            self._week_cb.bind(
                "<<ComboboxSelected>>",
                lambda event: self._select_week(self._week_cb.current())
            )

        elif period == "Month":
            tk.Label(
                body,
                text="Showing full selected month.",
                font=("Segoe UI", 10, "italic"),
                bg=CARD_BG,
                fg=TEXT
            ).pack(side="left", padx=10)

        else:
            tk.Label(
                body,
                text="Showing full selected year.",
                font=("Segoe UI", 10, "italic"),
                bg=CARD_BG,
                fg=TEXT
            ).pack(side="left", padx=10)

        hint = tk.Frame(self.filter_panel, bg=CARD_BG)
        hint.pack(fill="x", padx=14, pady=(0, 12))

        try:
            sales_days = self._get_sales_dates_for_month()
            sales_days_text = ", ".join(str(day) for day in sorted(sales_days)) if sales_days else "No sales days"
        except Exception:
            sales_days_text = "Unable to load sales days"

        tk.Label(
            hint,
            text=f"Days with sales this month: {sales_days_text}",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg=TEXT,
            wraplength=900,
            justify="left"
        ).pack(anchor="w")

    # ============================================================
    # FILTER ACTIONS
    # ============================================================
    def _set_valid_selected_day(self):
        _, days_in_month = calendar.monthrange(self._cal_year, self._cal_month)

        if self._sel_day > days_in_month:
            self._sel_day = days_in_month

        if self._sel_day < 1:
            self._sel_day = 1

    def _set_cal_month(self, selected_month):
        self._cal_month = selected_month
        self._sel_week = 0
        self._set_valid_selected_day()

        self._build_filter_panel()
        self._refresh()

    def _set_cal_year(self, selected_year):
        self._cal_year = selected_year
        self._sel_week = 0
        self._set_valid_selected_day()

        self._build_filter_panel()
        self._refresh()

    def _select_day(self, selected_day):
        self._sel_day = selected_day
        self._refresh()

    def _select_week(self, selected_week):
        self._sel_week = selected_week
        self._refresh()

    def _on_period(self):
        self._sel_week = 0
        self._set_valid_selected_day()

        if self._filter_open:
            self._build_filter_panel()

        self._refresh()

    # ============================================================
    # UI HELPERS
    # ============================================================
    def _clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

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

    # ============================================================
    # CHARTS
    # ============================================================
    def _draw_sales_trend_chart(self, trend_data):
        self._clear_frame(self.trend_card)

        header = tk.Frame(self.trend_card, bg=CARD_BG)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Sales Trend",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left", padx=14, pady=(10, 0))

        tk.Label(
            header,
            text="Total sales movement within the selected range",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=10, pady=(13, 0))

        canvas = tk.Canvas(
            self.trend_card,
            width=780,
            height=190,
            bg=CARD_BG,
            highlightthickness=0
        )
        canvas.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        if not trend_data:
            canvas.create_text(
                390,
                88,
                text="No sales trend data available",
                font=("Segoe UI", 12, "bold"),
                fill=TEXT
            )
            return

        width = 760
        height = 170
        left = 55
        right = width - 20
        top = 20
        bottom = height - 35

        canvas.create_line(left, bottom, right, bottom, fill=BORDER, width=2)
        canvas.create_line(left, top, left, bottom, fill=BORDER, width=2)

        max_sales = max(amount for _, amount in trend_data)

        if max_sales <= 0:
            canvas.create_text(
                390,
                88,
                text="No sales trend data available",
                font=("Segoe UI", 12, "bold"),
                fill=TEXT
            )
            return

        points = []
        count = len(trend_data)

        for index, (label, amount) in enumerate(trend_data):
            if count == 1:
                x = (left + right) / 2
            else:
                x = left + (index / (count - 1)) * (right - left)

            y = bottom - (amount / max_sales) * (bottom - top)
            points.append((x, y, label, amount))

        for i in range(len(points) - 1):
            x1, y1, _, _ = points[i]
            x2, y2, _, _ = points[i + 1]
            canvas.create_line(x1, y1, x2, y2, fill=DARK_RED, width=3, smooth=True)

        for index, (x, y, label, amount) in enumerate(points):
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=GOLD, outline=DARK_RED, width=2)

            if index == 0 or index == len(points) - 1 or len(points) <= 5:
                canvas.create_text(
                    x,
                    bottom + 14,
                    text=label[-5:],
                    font=("Segoe UI", 8),
                    fill=TEXT
                )

        canvas.create_text(
            left,
            top - 6,
            text=format_money(max_sales),
            anchor="w",
            font=("Segoe UI", 8, "bold"),
            fill=DARK_RED
        )

        total_trend_sales = sum(amount for _, amount in trend_data)

        canvas.create_text(
            right,
            top - 6,
            text=f"Total: {format_money(total_trend_sales)}",
            anchor="e",
            font=("Segoe UI", 9, "bold"),
            fill=DARK_RED
        )

    def _draw_pie_chart(self, completed_orders, pending_orders):
        self._clear_frame(self.pie_card)

        tk.Label(
            self.pie_card,
            text="Order Status",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(10, 0))

        tk.Label(
            self.pie_card,
            text="Accepted orders vs pending orders",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(anchor="w", padx=14, pady=(0, 4))

        canvas = tk.Canvas(
            self.pie_card,
            width=340,
            height=190,
            bg=CARD_BG,
            highlightthickness=0
        )
        canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        total = completed_orders + pending_orders

        if total <= 0:
            canvas.create_text(
                170,
                88,
                text="No order data",
                font=("Segoe UI", 12, "bold"),
                fill=TEXT
            )
            return

        x1, y1, x2, y2 = 35, 20, 175, 160
        start_angle = 90

        completed_extent = (completed_orders / total) * 360
        pending_extent = (pending_orders / total) * 360

        canvas.create_arc(
            x1,
            y1,
            x2,
            y2,
            start=start_angle,
            extent=completed_extent,
            fill="#27AE60",
            outline=CARD_BG
        )

        canvas.create_arc(
            x1,
            y1,
            x2,
            y2,
            start=start_angle + completed_extent,
            extent=pending_extent,
            fill="#B03A2E",
            outline=CARD_BG
        )

        canvas.create_oval(
            75,
            60,
            135,
            120,
            fill=CARD_BG,
            outline=CARD_BG
        )

        completed_percent = (completed_orders / total) * 100
        pending_percent = (pending_orders / total) * 100

        canvas.create_text(
            105,
            86,
            text=f"{completed_percent:.0f}%",
            font=("Georgia", 14, "bold"),
            fill=DARK_RED
        )

        canvas.create_rectangle(205, 45, 219, 59, fill="#27AE60", outline="#27AE60")
        canvas.create_text(
            228,
            52,
            text=f"Accepted: {completed_orders}",
            anchor="w",
            font=("Segoe UI", 10, "bold"),
            fill=TEXT
        )

        canvas.create_rectangle(205, 78, 219, 92, fill="#B03A2E", outline="#B03A2E")
        canvas.create_text(
            228,
            85,
            text=f"Pending: {pending_orders}",
            anchor="w",
            font=("Segoe UI", 10, "bold"),
            fill=TEXT
        )

        canvas.create_text(
            205,
            120,
            text=f"Pending rate: {pending_percent:.0f}%",
            anchor="w",
            font=("Segoe UI", 9, "italic"),
            fill=TEXT
        )

    def _draw_bar_chart(self, top_products):
        self._clear_frame(self.bar_card)

        tk.Label(
            self.bar_card,
            text="Top Products",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(10, 0))

        tk.Label(
            self.bar_card,
            text="Based on quantity sold",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(anchor="w", padx=14, pady=(0, 4))

        canvas = tk.Canvas(
            self.bar_card,
            width=430,
            height=190,
            bg=CARD_BG,
            highlightthickness=0
        )
        canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        if not top_products:
            canvas.create_text(
                215,
                88,
                text="No product sales data",
                font=("Segoe UI", 12, "bold"),
                fill=TEXT
            )
            return

        max_qty = max(qty for _, qty in top_products)

        if max_qty <= 0:
            canvas.create_text(
                215,
                88,
                text="No product sales data",
                font=("Segoe UI", 12, "bold"),
                fill=TEXT
            )
            return

        left_margin = 125
        top_margin = 18
        bar_height = 22
        gap = 10
        max_bar_width = 245

        for index, (name, qty) in enumerate(top_products):
            y = top_margin + index * (bar_height + gap)
            bar_width = int((qty / max_qty) * max_bar_width)

            short_name_value = short_text(name, 17)

            canvas.create_text(
                left_margin - 8,
                y + bar_height / 2,
                text=short_name_value,
                anchor="e",
                font=("Segoe UI", 9, "bold"),
                fill=TEXT
            )

            canvas.create_rectangle(
                left_margin,
                y,
                left_margin + max_bar_width,
                y + bar_height,
                fill="#F4EBD0",
                outline="#F4EBD0"
            )

            canvas.create_rectangle(
                left_margin,
                y,
                left_margin + bar_width,
                y + bar_height,
                fill=CHART_COLORS[index % len(CHART_COLORS)],
                outline=CHART_COLORS[index % len(CHART_COLORS)]
            )

            canvas.create_text(
                left_margin + bar_width + 8,
                y + bar_height / 2,
                text=str(qty),
                anchor="w",
                font=("Segoe UI", 9, "bold"),
                fill=DARK_RED
            )

    def _build_insights(self, total_sales, total_orders, total_items, pending_orders, top_products, grouped_orders):
        self._clear_frame(self.insight_card)

        best_cashier, best_cashier_sales = self._get_best_cashier(grouped_orders)
        highest_order = self._get_highest_order(grouped_orders)

        avg_order = total_sales / total_orders if total_orders > 0 else 0

        top_product_text = "No sales yet"
        if top_products:
            top_product_text = f"{top_products[0][0]} ({top_products[0][1]} sold)"

        highest_order_text = "No orders yet"
        if highest_order:
            highest_order_text = f"Order #{highest_order.get('order_id')} — {format_money(highest_order.get('total'))}"

        if total_orders > 0:
            items_per_order = total_items / total_orders
        else:
            items_per_order = 0

        tk.Label(
            self.insight_card,
            text="📌 Dashboard Insights",
            font=("Segoe UI", 13, "bold"),
            bg="#FFF8E1",
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(12, 6))

        insights = [
            ("Top Product", top_product_text),
            ("Highest Order", highest_order_text),
            ("Average Order", format_money(avg_order)),
            ("Items per Order", f"{items_per_order:.1f} item(s)"),
            ("Best Cashier", best_cashier),
            ("Cashier Sales", format_money(best_cashier_sales)),
            ("Pending Orders", str(pending_orders)),
        ]

        for title, value in insights:
            box = tk.Frame(
                self.insight_card,
                bg="#FFFDF2",
                highlightbackground="#E6C76E",
                highlightthickness=1
            )
            box.pack(fill="x", padx=12, pady=4)

            tk.Label(
                box,
                text=title,
                font=("Segoe UI", 9, "bold"),
                bg="#FFFDF2",
                fg=DARK_RED
            ).pack(anchor="w", padx=10, pady=(6, 0))

            tk.Label(
                box,
                text=value,
                font=("Segoe UI", 10),
                bg="#FFFDF2",
                fg=TEXT,
                wraplength=320,
                justify="left"
            ).pack(anchor="w", padx=10, pady=(0, 6))

    # ============================================================
    # TABLE SEARCH
    # ============================================================
    def _clear_search(self):
        self.search_var.set("")
        self._apply_table_search()

    def _apply_table_search(self):
        keyword = self.search_var.get().strip().lower()

        if not keyword:
            self.filtered_orders = self.grouped_orders[:]
        else:
            filtered = []

            for order in self.grouped_orders:
                products_text = ", ".join(order.get("products", []))

                searchable = " ".join([
                    str(order.get("order_id", "")),
                    products_text,
                    str(order.get("total_qty", "")),
                    str(order.get("total", "")),
                    str(order.get("cashier_name", "")),
                    str(order.get("sale_date", "")),
                ]).lower()

                if keyword in searchable:
                    filtered.append(order)

            self.filtered_orders = filtered

        self._load_sales_table(self.filtered_orders)

    # ============================================================
    # REFRESH DASHBOARD
    # ============================================================
    def _refresh(self):
        try:
            self._clear_frame(self.kpi)

            raw_data = self._get_sales_records()
            self.grouped_orders = self._group_sales_by_order(raw_data)
            self.filtered_orders = self.grouped_orders[:]

            pending_orders = self._get_pending_orders_count()

            total_sales = sum(safe_float(order["total"]) for order in self.grouped_orders)
            total_orders = len(self.grouped_orders)
            total_items = sum(safe_int(order["total_qty"]) for order in self.grouped_orders)
            average_order = total_sales / total_orders if total_orders > 0 else 0

            start_date, end_date = self._get_date_range()
            self.range_lbl.config(text=f"{start_date} to {end_date}")

            stats = [
                ("💰 Sales", format_money(total_sales), SIDEBAR, "Accepted orders only"),
                ("🧾 Orders", str(total_orders), "#27AE60", "Grouped by order ID"),
                ("🔢 Items Sold", str(total_items), GOLD, "Total product quantity"),
                ("📊 Avg. Order", format_money(average_order), "#6C3483", "Sales per order"),
                ("⏳ Pending", str(pending_orders), "#B03A2E", "Needs action"),
            ]

            for index, (label, value, color, subtext) in enumerate(stats):
                self._make_kpi_card(self.kpi, index, label, value, color, subtext)

            top_products = self._get_top_products(raw_data, limit=5)
            sales_trend = self._get_sales_trend(self.grouped_orders)

            self._draw_sales_trend_chart(sales_trend)
            self._draw_pie_chart(total_orders, pending_orders)
            self._draw_bar_chart(top_products)
            self._build_insights(
                total_sales,
                total_orders,
                total_items,
                pending_orders,
                top_products,
                self.grouped_orders
            )

            self._apply_table_search()

        except Exception as e:
            messagebox.showerror(
                "Dashboard Error",
                f"Unable to refresh dashboard.\n\n{e}",
                parent=self
            )

    def _load_sales_table(self, grouped_orders):
        self.tree.delete(*self.tree.get_children())

        if not grouped_orders:
            self.tree.insert(
                "",
                "end",
                values=("—", "No accepted orders found", "0", "₱0.00", "—", "—"),
                tags=("even",)
            )
            return

        for index, order in enumerate(grouped_orders):
            sale_date = order.get("sale_date")
            sale_date_text = str(sale_date) if sale_date else ""

            products_text = ", ".join(order.get("products", []))

            self.tree.insert(
                "",
                "end",
                values=(
                    order.get("order_id"),
                    products_text,
                    order.get("total_qty"),
                    format_money(order.get("total")),
                    order.get("cashier_name"),
                    sale_date_text
                ),
                tags=("odd" if index % 2 else "even",)
            )


if __name__ == "__main__":
    AdminDashboard("Admin").mainloop()