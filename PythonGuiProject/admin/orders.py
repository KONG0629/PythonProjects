"""
admin/orders.py

Admin Orders Management page.

UI upgraded to match Admin Dashboard style.

This page uses:
admin/orders.py
→ databases/order_backend.py
→ databases/db.py
→ MySQL

Features:
- Dashboard-style header
- KPI cards for total, pending, accepted, cancelled, and sales
- Cleaner filter/action card
- Search orders by ref, cashier, payment, status, date
- Order details panel
- Payment summary panel
- Order items with discount share
- Accept pending orders
- Cancel pending orders
"""

# ============================================================
# IMPORTS AND PROJECT PATH SETUP
# ============================================================
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from theme import *

from datetime import datetime

from databases.order_backend import (
    get_admin_orders,
    get_order_items,
    get_order_by_id,
    accept_order,
    cancel_order
)

ctk.set_appearance_mode("light")


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def db_status_to_display(status):
    status = str(status or "").lower().strip()

    if status == "pending":
        return "Pending"

    if status == "accepted":
        return "Accepted"

    if status in ("cancelled", "canceled"):
        return "Cancelled"

    return status.capitalize()


def make_order_ref(order_id):
    return f"ORD-{int(order_id):06d}"


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


def format_money(value):
    try:
        return f"₱{float(value or 0):,.2f}"
    except Exception:
        return "₱0.00"


def short_text(value, limit=38):
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


def compute_item_discount_share(item_subtotal, order_subtotal, order_discount):
    item_subtotal = safe_float(item_subtotal)
    order_subtotal = safe_float(order_subtotal)
    order_discount = safe_float(order_discount)

    if order_subtotal <= 0 or order_discount <= 0:
        return 0.0

    share = (item_subtotal / order_subtotal) * order_discount

    if share < 0:
        share = 0.0

    if share > item_subtotal:
        share = item_subtotal

    return share


# ============================================================
# ADMIN ORDERS CLASS
# ============================================================
class AdminOrders(ctk.CTk):

    def __init__(self, user_name="Admin", admin_id=None):
        super().__init__()

        self.user_name = user_name
        self.admin_id = admin_id
        self.sel_id = None

        self.current_orders = []
        self.filtered_orders = []

        self.filter_var = tk.StringVar(master=self, value="All")
        self.search_var = tk.StringVar(master=self)

        self.title("Admin — Orders")
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
                app = AdminOrders(self.user_name, self.admin_id)

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

        make_sidebar(self, self.user_name, "Administrator", nav, "orders")

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
            text="📦 Orders Management",
            font=F_TITLE,
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w")

        tk.Label(
            left_hdr,
            text="Review incoming orders, check payment details, and manage order status.",
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
        self.kpi_frame = tk.Frame(self.main, bg=BG)
        self.kpi_frame.pack(fill="x", padx=22, pady=(14, 10))

        # ========================================================
        # ACTION AND FILTER CARD
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
            text="Order Tools",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left", padx=14, pady=12)

        success_btn(
            action_card,
            "✅ Accept",
            self._accept,
            height=34,
            width=110
        ).pack(side="right", padx=(4, 12), pady=10)

        danger_btn(
            action_card,
            "❌ Cancel",
            self._cancel,
            height=34,
            width=110
        ).pack(side="right", padx=4, pady=10)

        primary_btn(
            action_card,
            "🔄 Refresh",
            self._load_orders,
            height=34,
            width=110
        ).pack(side="right", padx=4, pady=10)

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
            text="Status:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(8, 4))

        for status in ("All", "Pending", "Accepted", "Cancelled"):
            tk.Radiobutton(
                filter_card,
                text=status,
                variable=self.filter_var,
                value=status,
                font=F_BODY,
                bg=CARD_BG,
                fg=DARK_RED,
                selectcolor=GOLD,
                activebackground=CARD_BG,
                command=self._apply_filters
            ).pack(side="left", padx=5)

        search_box = tk.Frame(filter_card, bg=CARD_BG)
        search_box.pack(side="right", padx=12, pady=10)

        tk.Label(
            search_box,
            text="🔍",
            font=("Segoe UI", 12),
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(0, 4))

        self.search_entry = ctk.CTkEntry(
            search_box,
            textvariable=self.search_var,
            width=280,
            height=34,
            placeholder_text="Search ref, cashier, payment, status...",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=("Segoe UI", 10),
            corner_radius=8
        )
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", lambda event: self._apply_filters())

        gold_btn(
            search_box,
            "Clear",
            self._clear_search,
            height=34,
            width=70
        ).pack(side="left", padx=4)

        # ========================================================
        # BODY
        # ========================================================
        body = tk.Frame(self.main, bg=BG)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 20))

        # ========================================================
        # LEFT PANEL
        # ========================================================
        left = tk.Frame(
            body,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        left_header = tk.Frame(left, bg=CARD_BG)
        left_header.pack(fill="x")

        tk.Label(
            left_header,
            text="Incoming Orders",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left", padx=14, pady=(12, 6))

        self.result_lbl = tk.Label(
            left_header,
            text="",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg=TEXT
        )
        self.result_lbl.pack(side="left", padx=10, pady=(14, 6))

        # ========================================================
        # TABLE STYLE
        # ========================================================
        style = ttk.Style()
        style.theme_use("clam")

        for table_name in ("ORD", "ITM"):
            style.configure(
                f"{table_name}.Treeview",
                background=CARD_BG,
                fieldbackground=CARD_BG,
                foreground=TEXT,
                rowheight=38,
                font=("Segoe UI", 10)
            )

            style.configure(
                f"{table_name}.Treeview.Heading",
                background=SIDEBAR,
                foreground=WHITE,
                font=("Segoe UI", 10, "bold"),
                relief="flat"
            )

            style.map(
                f"{table_name}.Treeview",
                background=[("selected", GOLD)],
                foreground=[("selected", DARK_RED)]
            )

        # ========================================================
        # ORDERS TABLE
        # ========================================================
        ord_cols = (
            "ID",
            "Ref",
            "Cashier",
            "Subtotal",
            "Discount",
            "Final Total",
            "Payment",
            "Status",
            "Date"
        )

        ord_widths = [45, 105, 115, 95, 95, 110, 120, 90, 140]

        self.ord_tree = ttk.Treeview(
            left,
            columns=ord_cols,
            show="headings",
            style="ORD.Treeview"
        )

        for col_name, width in zip(ord_cols, ord_widths):
            self.ord_tree.heading(col_name, text=col_name)
            self.ord_tree.column(col_name, width=width, anchor="center", minwidth=40)

        vsb1 = ttk.Scrollbar(left, orient="vertical", command=self.ord_tree.yview)
        hsb1 = ttk.Scrollbar(left, orient="horizontal", command=self.ord_tree.xview)

        self.ord_tree.configure(
            yscrollcommand=vsb1.set,
            xscrollcommand=hsb1.set
        )

        vsb1.pack(side="right", fill="y")
        hsb1.pack(side="bottom", fill="x")
        self.ord_tree.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        self.ord_tree.tag_configure("Pending", foreground="#D68910")
        self.ord_tree.tag_configure("Accepted", foreground="#1E8449")
        self.ord_tree.tag_configure("Cancelled", foreground="#B03A2E")
        self.ord_tree.tag_configure("odd", background=ODD_ROW)
        self.ord_tree.tag_configure("even", background=CARD_BG)

        self.ord_tree.bind("<<TreeviewSelect>>", self._on_select)

        # ========================================================
        # RIGHT PANEL
        # ========================================================
        right = tk.Frame(
            body,
            bg=BG,
            width=530
        )
        right.pack(side="right", fill="both")
        right.pack_propagate(False)

        self.order_info_card = tk.Frame(
            right,
            bg="#FFF8E1",
            highlightbackground=GOLD,
            highlightthickness=1
        )
        self.order_info_card.pack(fill="x", pady=(0, 8))

        tk.Label(
            self.order_info_card,
            text="📌 Selected Order",
            font=("Segoe UI", 13, "bold"),
            bg="#FFF8E1",
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(10, 2))

        self.selected_order_lbl = tk.Label(
            self.order_info_card,
            text="Select an order from the table to view details.",
            font=("Segoe UI", 10),
            bg="#FFF8E1",
            fg=TEXT,
            wraplength=480,
            justify="left"
        )
        self.selected_order_lbl.pack(anchor="w", padx=14, pady=(0, 10))

        items_card = tk.Frame(
            right,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        items_card.pack(fill="both", expand=True, pady=(0, 8))

        tk.Label(
            items_card,
            text="Order Items",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(12, 6))

        itm_cols = (
            "Product",
            "Qty",
            "Unit Price",
            "Original",
            "Discount",
            "Final"
        )

        itm_widths = [150, 45, 85, 85, 85, 85]

        self.itm_tree = ttk.Treeview(
            items_card,
            columns=itm_cols,
            show="headings",
            style="ITM.Treeview",
            height=8
        )

        for col_name, width in zip(itm_cols, itm_widths):
            self.itm_tree.heading(col_name, text=col_name)
            self.itm_tree.column(col_name, width=width, anchor="center", minwidth=40)

        vsb2 = ttk.Scrollbar(items_card, orient="vertical", command=self.itm_tree.yview)
        hsb2 = ttk.Scrollbar(items_card, orient="horizontal", command=self.itm_tree.xview)

        self.itm_tree.configure(
            yscrollcommand=vsb2.set,
            xscrollcommand=hsb2.set
        )

        vsb2.pack(side="right", fill="y")
        hsb2.pack(side="bottom", fill="x")
        self.itm_tree.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        self.itm_tree.tag_configure("summary", background="#FFF3CD", foreground=DARK_RED)
        self.itm_tree.tag_configure("discount", background="#FDECEA", foreground="#B03A2E")
        self.itm_tree.tag_configure("final", background="#EAF7EA", foreground="#1E8449")
        self.itm_tree.tag_configure("odd", background=ODD_ROW)
        self.itm_tree.tag_configure("even", background=CARD_BG)

        # ========================================================
        # PAYMENT SUMMARY
        # ========================================================
        self.details = tk.Frame(
            right,
            bg=CREAM,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.details.pack(fill="x")

        tk.Label(
            self.details,
            text="Payment Summary",
            font=F_HEAD,
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w", padx=12, pady=(10, 6))

        self.summary_rows = tk.Frame(self.details, bg=CREAM)
        self.summary_rows.pack(fill="x", padx=12, pady=(0, 10))

        self.subtotal_lbl = self._summary_label("Subtotal: —", TEXT)
        self.discount_type_lbl = self._summary_label("Discount Type: —", TEXT)
        self.discount_lbl = self._summary_label("Discount Amount: —", "#B03A2E")
        self.total_lbl = self._summary_label("Final Total: —", DARK_RED, big=True)
        self.payment_lbl = self._summary_label("Payment Method: —", TEXT)
        self.received_lbl = self._summary_label("Amount Received: —", TEXT)
        self.change_lbl = self._summary_label("Change: —", "#1E8449")
        self.reference_lbl = self._summary_label("Reference No: —", TEXT)

        self._load_orders()

    # ============================================================
    # UI HELPERS
    # ============================================================
    def _summary_label(self, text, color, big=False):
        label = tk.Label(
            self.summary_rows,
            text=text,
            font=("Georgia", 14, "bold") if big else F_BOLD,
            bg=CREAM,
            fg=color,
            anchor="e"
        )
        label.pack(fill="x", pady=2)
        return label

    def _make_kpi_card(self, index, label, value, color, subtext=""):
        card = tk.Frame(self.kpi_frame, bg=color)
        card.grid(row=0, column=index, sticky="ew", padx=5)

        self.kpi_frame.columnconfigure(index, weight=1)

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

    def _update_kpis(self, orders):
        for widget in self.kpi_frame.winfo_children():
            widget.destroy()

        total_orders = len(orders)
        pending_count = 0
        accepted_count = 0
        cancelled_count = 0
        accepted_sales = 0.0

        for order in orders:
            display_status = db_status_to_display(order.get("order_status"))

            subtotal = safe_float(order.get("subtotal_amount"))
            discount = safe_float(order.get("discount_amount"))
            old_total = safe_float(order.get("total_amount"))
            final_total = compute_final_total(subtotal, discount, old_total)

            if display_status == "Pending":
                pending_count += 1
            elif display_status == "Accepted":
                accepted_count += 1
                accepted_sales += final_total
            elif display_status == "Cancelled":
                cancelled_count += 1

        stats = [
            ("📦 Total Orders", str(total_orders), SIDEBAR, "All records"),
            ("⏳ Pending", str(pending_count), GOLD, "Needs action"),
            ("✅ Accepted", str(accepted_count), "#27AE60", "Confirmed"),
            ("❌ Cancelled", str(cancelled_count), "#B03A2E", "Declined"),
            ("💰 Sales", format_money(accepted_sales), "#6C3483", "Accepted only"),
        ]

        for index, (label, value, color, subtext) in enumerate(stats):
            self._make_kpi_card(index, label, value, color, subtext)

    # ============================================================
    # SEARCH AND FILTER
    # ============================================================
    def _clear_search(self):
        self.search_var.set("")
        self._apply_filters()

    def _order_matches_search(self, order, keyword):
        if not keyword:
            return True

        order_id = order.get("order_id")
        display_status = db_status_to_display(order.get("order_status"))
        order_ref = make_order_ref(order_id)

        created_at = order.get("created_at")
        date_text = str(created_at)[:16] if created_at else ""

        subtotal = safe_float(order.get("subtotal_amount"))
        discount = safe_float(order.get("discount_amount"))
        old_total = safe_float(order.get("total_amount"))
        final_total = compute_final_total(subtotal, discount, old_total)

        searchable = " ".join([
            str(order_id),
            order_ref,
            str(order.get("cashier_name", "")),
            str(order.get("payment_method", "")),
            display_status,
            date_text,
            format_money(final_total),
        ]).lower()

        return keyword.lower() in searchable

    def _apply_filters(self):
        selected_filter = self.filter_var.get()
        keyword = self.search_var.get().strip().lower()

        filtered_orders = []

        for order in self.current_orders:
            display_status = db_status_to_display(order.get("order_status"))

            if selected_filter != "All" and display_status != selected_filter:
                continue

            if not self._order_matches_search(order, keyword):
                continue

            filtered_orders.append(order)

        self.filtered_orders = filtered_orders
        self._load_orders_table(filtered_orders)

    # ============================================================
    # CLEAR DETAILS
    # ============================================================
    def _clear_details(self):
        self.itm_tree.delete(*self.itm_tree.get_children())

        self.selected_order_lbl.configure(
            text="Select an order from the table to view details."
        )

        self.subtotal_lbl.configure(text="Subtotal: —")
        self.discount_type_lbl.configure(text="Discount Type: —")
        self.discount_lbl.configure(text="Discount Amount: —")
        self.total_lbl.configure(text="Final Total: —")
        self.payment_lbl.configure(text="Payment Method: —")
        self.received_lbl.configure(text="Amount Received: —")
        self.change_lbl.configure(text="Change: —")
        self.reference_lbl.configure(text="Reference No: —")

        self.sel_id = None

    # ============================================================
    # LOAD ORDERS
    # ============================================================
    def _load_orders(self):
        try:
            orders = get_admin_orders("All")
            self.current_orders = orders

            self._update_kpis(orders)
            self._apply_filters()
            self._clear_details()

        except Exception as e:
            messagebox.showerror(
                "Orders Error",
                f"Unable to load orders.\n\n{e}",
                parent=self
            )

    def _load_orders_table(self, orders):
        self.ord_tree.delete(*self.ord_tree.get_children())

        self.result_lbl.configure(text=f"{len(orders)} order(s) shown")

        selected_filter = self.filter_var.get()

        if not orders:
            self.ord_tree.insert(
                "",
                "end",
                values=(
                    "—",
                    "No orders",
                    "—",
                    "₱0.00",
                    "₱0.00",
                    "₱0.00",
                    "—",
                    selected_filter,
                    "—"
                ),
                tags=("even",)
            )
            return

        for index, order in enumerate(orders):
            order_id = order["order_id"]
            display_status = db_status_to_display(order["order_status"])
            order_ref = make_order_ref(order_id)

            created_at = order.get("created_at")
            date_text = str(created_at)[:16] if created_at else ""

            subtotal = safe_float(order.get("subtotal_amount"))
            discount = safe_float(order.get("discount_amount"))
            old_total = safe_float(order.get("total_amount"))

            final_total = compute_final_total(
                subtotal=subtotal,
                discount=discount,
                fallback_total=old_total
            )

            display_subtotal = subtotal

            if display_subtotal <= 0:
                display_subtotal = old_total + discount

            payment_method = order.get("payment_method") or "Cash"

            self.ord_tree.insert(
                "",
                "end",
                values=(
                    order_id,
                    order_ref,
                    short_text(order.get("cashier_name", "Cashier"), 18),
                    format_money(display_subtotal),
                    format_money(discount),
                    format_money(final_total),
                    payment_method,
                    display_status,
                    date_text
                ),
                tags=(display_status, "odd" if index % 2 else "even")
            )

    # ============================================================
    # INSERT ORDER ITEM SUMMARY ROWS
    # ============================================================
    def _insert_item_summary_rows(self, subtotal, discount_amount, final_total):
        self.itm_tree.insert(
            "",
            "end",
            values=("────────", "", "", "", "", ""),
            tags=("summary",)
        )

        self.itm_tree.insert(
            "",
            "end",
            values=(
                "ORDER SUBTOTAL",
                "",
                "",
                format_money(subtotal),
                "",
                format_money(subtotal)
            ),
            tags=("summary",)
        )

        self.itm_tree.insert(
            "",
            "end",
            values=(
                "ORDER DISCOUNT",
                "",
                "",
                "",
                f"-{format_money(discount_amount)}",
                ""
            ),
            tags=("discount",)
        )

        self.itm_tree.insert(
            "",
            "end",
            values=(
                "FINAL TOTAL",
                "",
                "",
                "",
                "",
                format_money(final_total)
            ),
            tags=("final",)
        )

    # ============================================================
    # SELECT ORDER
    # ============================================================
    def _on_select(self, event=None):
        selected_row = self.ord_tree.focus()

        if not selected_row:
            return

        values = self.ord_tree.item(selected_row, "values")

        if not values or values[0] == "—":
            return

        self.sel_id = int(values[0])

        self.itm_tree.delete(*self.itm_tree.get_children())

        items = get_order_items(self.sel_id)
        order = get_order_by_id(self.sel_id)

        item_subtotal_total = 0.0

        for item in items:
            item_subtotal_total += safe_float(item.get("subtotal"))

        if order:
            db_subtotal = safe_float(order.get("subtotal_amount"))
            discount_amount = safe_float(order.get("discount_amount"))
            db_total = safe_float(order.get("total_amount"))

            order_subtotal = item_subtotal_total

            if order_subtotal <= 0:
                order_subtotal = db_subtotal

            if order_subtotal <= 0:
                order_subtotal = db_total + discount_amount

            final_total = compute_final_total(
                subtotal=order_subtotal,
                discount=discount_amount,
                fallback_total=db_total
            )

            total_item_discount = 0.0
            total_item_final = 0.0

            for index, item in enumerate(items):
                price = safe_float(item.get("price"))
                item_original_subtotal = safe_float(item.get("subtotal"))
                quantity = safe_int(item.get("quantity"))

                item_discount = compute_item_discount_share(
                    item_subtotal=item_original_subtotal,
                    order_subtotal=order_subtotal,
                    order_discount=discount_amount
                )

                if index == len(items) - 1:
                    item_discount = discount_amount - total_item_discount

                    if item_discount < 0:
                        item_discount = 0.0

                    if item_discount > item_original_subtotal:
                        item_discount = item_original_subtotal

                item_final_subtotal = item_original_subtotal - item_discount

                if item_final_subtotal < 0:
                    item_final_subtotal = 0.0

                total_item_discount += item_discount
                total_item_final += item_final_subtotal

                self.itm_tree.insert(
                    "",
                    "end",
                    values=(
                        short_text(item["product_name"], 22),
                        quantity,
                        format_money(price),
                        format_money(item_original_subtotal),
                        f"-{format_money(item_discount)}",
                        format_money(item_final_subtotal)
                    ),
                    tags=("odd" if index % 2 else "even",)
                )

            if abs(total_item_final - final_total) > 0.05:
                total_item_final = final_total

            self._insert_item_summary_rows(
                subtotal=order_subtotal,
                discount_amount=discount_amount,
                final_total=final_total
            )

            amount_received = safe_float(order.get("amount_received"))
            payment_method = order.get("payment_method") or "Cash"

            if str(payment_method).lower() == "online payment":
                change_amount = 0.0
            else:
                change_amount = amount_received - final_total

                if change_amount < 0:
                    change_amount = 0.0

            display_status = db_status_to_display(order.get("order_status"))
            reference = order.get("online_reference") or "—"

            self.selected_order_lbl.configure(
                text=(
                    f"{make_order_ref(order['order_id'])} • {display_status}\n"
                    f"Cashier: {order.get('cashier_name', 'Cashier')}\n"
                    f"Payment: {payment_method}"
                )
            )

            self.subtotal_lbl.configure(
                text=f"Subtotal: {format_money(order_subtotal)}"
            )

            self.discount_type_lbl.configure(
                text=f"Discount Type: {order.get('discount_type') or 'No Discount'}"
            )

            self.discount_lbl.configure(
                text=f"Discount Amount: -{format_money(discount_amount)}"
            )

            self.total_lbl.configure(
                text=f"Final Total: {format_money(final_total)}"
            )

            self.payment_lbl.configure(
                text=f"Payment Method: {payment_method}"
            )

            self.received_lbl.configure(
                text=f"Amount Received: {format_money(amount_received)}"
            )

            self.change_lbl.configure(
                text=f"Change: {format_money(change_amount)}"
            )

            self.reference_lbl.configure(
                text=f"Reference No: {reference}"
            )

    # ============================================================
    # GET SELECTED ORDER
    # ============================================================
    def _get_selected_order(self):
        if self.sel_id is None:
            messagebox.showwarning("Orders", "Select an order first.", parent=self)
            return None

        order = get_order_by_id(self.sel_id)

        if not order:
            messagebox.showerror("Orders", "Selected order was not found.", parent=self)
            return None

        return order

    # ============================================================
    # ACCEPT ORDER
    # ============================================================
    def _accept(self):
        order = self._get_selected_order()

        if order is None:
            return

        if order["order_status"] != "pending":
            messagebox.showinfo(
                "Orders",
                f"Order is already '{db_status_to_display(order['order_status'])}'.",
                parent=self
            )
            return

        subtotal = safe_float(order.get("subtotal_amount"))
        discount = safe_float(order.get("discount_amount"))
        total = compute_final_total(subtotal, discount, order.get("total_amount"))

        confirm = messagebox.askyesno(
            "Accept Order",
            f"Accept {make_order_ref(order['order_id'])}?\n\n"
            f"Final Total: {format_money(total)}\n"
            f"Payment Method: {order.get('payment_method') or 'Cash'}",
            parent=self
        )

        if not confirm:
            return

        success, message = accept_order(order["order_id"], self.admin_id)

        if success:
            messagebox.showinfo("Accepted", f"✅ {message}", parent=self)
            self._load_orders()
        else:
            messagebox.showerror("Accept Failed", message, parent=self)

    # ============================================================
    # CANCEL ORDER
    # ============================================================
    def _cancel(self):
        order = self._get_selected_order()

        if order is None:
            return

        if order["order_status"] != "pending":
            messagebox.showinfo(
                "Orders",
                f"Order is already '{db_status_to_display(order['order_status'])}'.",
                parent=self
            )
            return

        confirm = messagebox.askyesno(
            "Cancel Order",
            f"Cancel {make_order_ref(order['order_id'])}?",
            parent=self
        )

        if not confirm:
            return

        success, message = cancel_order(order["order_id"], self.admin_id)

        if success:
            messagebox.showinfo("Cancelled", message, parent=self)
            self._load_orders()
        else:
            messagebox.showerror("Cancel Failed", message, parent=self)


# ============================================================
# RUN DIRECTLY FOR TESTING
# ============================================================
if __name__ == "__main__":
    AdminOrders("Admin").mainloop()