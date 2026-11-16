"""
cashier/orders.py

Cashier Orders page connected to MySQL.

Updated UI:
- Cleaner cashier-friendly layout
- Consistent style with Cashier Dashboard and Order Status
- Better product picker area
- Better cart and payment panel
- Improved total payable display
- Keeps all existing functions and order logic
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

from databases.product_backend import get_all_products, search_products
from databases.order_backend import create_order
from databases.db import fetch_one

ctk.set_appearance_mode("light")


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def safe_money_to_float(value):
    if value is None:
        return 0.0

    text = str(value).strip()
    text = text.replace("₱", "").replace(",", "").strip()

    if text in ("", "."):
        return 0.0

    try:
        return float(text)
    except Exception:
        return 0.0


def format_money(value):
    try:
        return f"₱{float(value or 0):,.2f}"
    except Exception:
        return "₱0.00"


def safe_error(error):
    text = str(error).strip()
    return text if text else repr(error)


# ============================================================
# CASHIER ORDERS CLASS
# ============================================================
class CashierOrders(ctk.CTk):
    def __init__(self, user_name="Cashier", cashier_id=None):
        super().__init__()

        self.user_name = user_name
        self.cashier_id = cashier_id or self._resolve_cashier_id()

        self.cart = []
        self.current_products = []

        self._subtotal_total = 0.0
        self._discount_amount = 0.0
        self._payable_total = 0.0

        self.title("Cashier — Orders")
        self.configure(fg_color=BG)
        self.attributes("-fullscreen", True)

        self._build()

    # ============================================================
    # RESOLVE CASHIER ID
    # ============================================================
    def _resolve_cashier_id(self):
        try:
            query = """
                SELECT user_id
                FROM users
                WHERE full_name = %s
                AND role = 'cashier'
                AND status = 'active'
                LIMIT 1
            """

            result = fetch_one(query, (self.user_name,))

            if result:
                return result["user_id"]

            return None

        except Exception:
            return None

    # ============================================================
    # NAVIGATION
    # ============================================================
    def _go_products(self):
        try:
            self.configure(cursor="watch")
            self.update_idletasks()

            from cashier.cashierDashboard import CashierDashboard

            self.destroy()

            app = CashierDashboard(self.user_name, self.cashier_id)
            app.mainloop()

        except Exception as e:
            self.configure(cursor="")
            messagebox.showerror(
                "Navigation Error",
                f"Unable to open cashier dashboard.\n\n{safe_error(e)}",
                parent=self
            )

    def _go_order_status(self):
        try:
            self.configure(cursor="watch")
            self.update_idletasks()

            self.destroy()

            from cashier.cashierDashboard import CashierDashboard

            app = CashierDashboard(self.user_name, self.cashier_id)
            app._show_order_status()
            app.mainloop()

        except Exception as e:
            self.configure(cursor="")
            messagebox.showerror(
                "Navigation Error",
                f"Unable to open Order Status page.\n\n{safe_error(e)}"
            )

    # ============================================================
    # VALIDATION FUNCTIONS
    # ============================================================
    def _validate_money_input(self, value):
        if value == "":
            return True

        cleaned = value.replace(",", "")

        if cleaned.count(".") > 1:
            return False

        for char in cleaned:
            if not (char.isdigit() or char == "."):
                return False

        return True

    def _validate_quantity_input(self, value):
        if value == "":
            return True

        return value.isdigit()

    # ============================================================
    # DISCOUNT LOGIC
    # ============================================================
    def _get_discount_rate(self):
        discount_type = self.discount_var.get()

        discount_rates = {
            "No Discount": 0.00,
            "PWD Discount - 20%": 0.20,
            "Senior Citizen - 20%": 0.20,
            "Employee Discount - 10%": 0.10,
            "Promo Discount - 5%": 0.05,
        }

        return discount_rates.get(discount_type, 0.00)

    def _recalculate_totals(self):
        subtotal = 0.0

        for item in self.cart:
            subtotal += item["price"] * item["quantity"]

        discount_rate = self._get_discount_rate()
        discount_amount = subtotal * discount_rate
        payable_total = subtotal - discount_amount

        if payable_total < 0:
            payable_total = 0.0

        self._subtotal_total = subtotal
        self._discount_amount = discount_amount
        self._payable_total = payable_total

        self.subtotal_lbl.configure(text=format_money(subtotal))
        self.discount_lbl.configure(text=f"-{format_money(discount_amount)}")
        self.total_lbl.configure(text=format_money(payable_total))

        self._calc_change()

    # ============================================================
    # PAYMENT METHOD LOGIC
    # ============================================================
    def _on_payment_method_change(self, selected_payment=None):
        payment_method = self.payment_method_var.get()

        if payment_method == "Cash":
            self.received_entry.configure(state="normal")
            self.reference_entry.configure(state="disabled")
            self.reference_var.set("")
        else:
            self.received_var.set(format(self._payable_total, ".2f"))
            self.received_entry.configure(state="disabled")
            self.reference_entry.configure(state="normal")

        self._calc_change()

    # ============================================================
    # UI HELPERS
    # ============================================================
    def _card(self, parent, bg_color=None, border_color=None):
        return tk.Frame(
            parent,
            bg=bg_color or CARD_BG,
            highlightbackground=border_color or BORDER,
            highlightthickness=1
        )

    def _section_title(self, parent, title, subtitle=None, bg_color=None):
        bg = bg_color or CARD_BG

        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x", padx=16, pady=(14, 6))

        tk.Label(
            row,
            text=title,
            font=("Segoe UI", 15, "bold"),
            bg=bg,
            fg=DARK_RED
        ).pack(anchor="w")

        if subtitle:
            tk.Label(
                row,
                text=subtitle,
                font=("Segoe UI", 9),
                bg=bg,
                fg="#7A5B50"
            ).pack(anchor="w", pady=(1, 0))

    # ============================================================
    # BUILD UI
    # ============================================================
    def _build(self):
        nav = [
            ("products", "🧺", "Dashboard", self._go_products),
            ("orders", "📋", "Orders", lambda: None),
            ("order_status", "🧾", "Order Status", self._go_order_status),
        ]

        make_sidebar(self, self.user_name, "Cashier", nav, "orders")

        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="right", fill="both", expand=True)

        self._build_header()

        body = tk.Frame(self.main, bg=BG)
        body.pack(fill="both", expand=True, padx=22, pady=(16, 20))

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right = tk.Frame(body, bg=BG, width=475)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)

        self._build_product_picker(left)
        self._build_cart_payment_panel(right)

        self._refresh_products()

    # ============================================================
    # HEADER
    # ============================================================
    def _build_header(self):
        hdr = tk.Frame(self.main, bg=CREAM, height=94)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=CREAM)
        left.pack(side="left", padx=26, pady=14)

        tk.Label(
            left,
            text="📋 Cashier Orders",
            font=("Georgia", 23, "bold"),
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Search products, add items to cart, apply discounts, and send orders to admin.",
            font=("Segoe UI", 10, "bold"),
            bg=CREAM,
            fg=TEXT
        ).pack(anchor="w", pady=(2, 0))

        right = tk.Frame(hdr, bg=CREAM)
        right.pack(side="right", padx=22, pady=18)

        primary_btn(
            right,
            "🔄 Refresh Products",
            self._refresh_products,
            height=38,
            width=150
        ).pack(side="left", padx=5)

        gold_btn(
            right,
            "🧾 Order Status",
            self._go_order_status,
            height=38,
            width=140
        ).pack(side="left", padx=5)

    # ============================================================
    # LEFT SIDE: PRODUCT PICKER
    # ============================================================
    def _build_product_picker(self, parent):
        product_card = self._card(parent)
        product_card.pack(fill="both", expand=True)

        self._section_title(
            product_card,
            "🧺 Select Products",
            "Choose a product, type the quantity, then add it to the cart."
        )

        # Search box
        search_card = tk.Frame(product_card, bg=CARD_BG)
        search_card.pack(fill="x", padx=16, pady=(4, 10))

        self.srch_var = tk.StringVar(master=self)

        self.search_entry = ctk.CTkEntry(
            search_card,
            textvariable=self.srch_var,
            height=39,
            placeholder_text="Search product name, category, unit, price, or stock…",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=("Segoe UI", 10),
            corner_radius=10
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda event: self._search_products())

        primary_btn(
            search_card,
            "Search",
            self._search_products,
            height=37,
            width=90
        ).pack(side="left", padx=(8, 0))

        gold_btn(
            search_card,
            "Show All",
            self._clear_search,
            height=37,
            width=95
        ).pack(side="left", padx=(6, 0))

        # Table header
        table_header = tk.Frame(product_card, bg=CARD_BG)
        table_header.pack(fill="x", padx=16, pady=(2, 4))

        tk.Label(
            table_header,
            text="📦 Available Product List",
            font=("Segoe UI", 12, "bold"),
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left")

        self.product_count_lbl = tk.Label(
            table_header,
            text="0 product(s)",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg="#7A5B50"
        )
        self.product_count_lbl.pack(side="right")

        # Table style
        style = ttk.Style()
        style.theme_use("clam")

        for style_name in ("PL", "CT"):
            style.configure(
                f"{style_name}.Treeview",
                background=CARD_BG,
                fieldbackground=CARD_BG,
                foreground=TEXT,
                rowheight=40,
                font=("Segoe UI", 10)
            )

            style.configure(
                f"{style_name}.Treeview.Heading",
                background=SIDEBAR,
                foreground=WHITE,
                font=("Segoe UI", 10, "bold"),
                relief="flat"
            )

            style.map(
                f"{style_name}.Treeview",
                background=[("selected", GOLD)],
                foreground=[("selected", DARK_RED)]
            )

        table_box = tk.Frame(product_card, bg=CARD_BG)
        table_box.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        cols_p = ("ID", "Name", "Price", "Unit", "Stock")
        widths_p = [55, 310, 110, 90, 90]

        self.prod_tree = ttk.Treeview(
            table_box,
            columns=cols_p,
            show="headings",
            style="PL.Treeview",
            selectmode="browse"
        )

        for col_name, width in zip(cols_p, widths_p):
            self.prod_tree.heading(col_name, text=col_name)
            self.prod_tree.column(col_name, width=width, anchor="center", minwidth=50)

        self.prod_tree.column("Name", anchor="w")

        vsb1 = ttk.Scrollbar(table_box, orient="vertical", command=self.prod_tree.yview)
        xsb1 = ttk.Scrollbar(table_box, orient="horizontal", command=self.prod_tree.xview)

        self.prod_tree.configure(yscrollcommand=vsb1.set, xscrollcommand=xsb1.set)

        vsb1.pack(side="right", fill="y")
        xsb1.pack(side="bottom", fill="x")
        self.prod_tree.pack(fill="both", expand=True)

        self.prod_tree.tag_configure("odd", background=ODD_ROW)
        self.prod_tree.tag_configure("even", background=CARD_BG)
        self.prod_tree.tag_configure("low", background="#FFF3CD", foreground="#8A6D00")
        self.prod_tree.tag_configure("out", background="#FDECEA", foreground="#B03A2E")

        self.prod_tree.bind("<Double-1>", lambda event: self._add_to_cart())

        # Quantity action area
        action_box = tk.Frame(
            product_card,
            bg=CREAM,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        action_box.pack(fill="x", padx=16, pady=(0, 16))

        left = tk.Frame(action_box, bg=CREAM)
        left.pack(side="left", padx=14, pady=12)

        tk.Label(
            left,
            text="Quantity",
            font=("Segoe UI", 10, "bold"),
            bg=CREAM,
            fg=TEXT
        ).pack(anchor="w")

        qty_row = tk.Frame(left, bg=CREAM)
        qty_row.pack(anchor="w", pady=(3, 0))

        self.qty_var = tk.StringVar(master=self, value="1")
        validate_qty = self.register(self._validate_quantity_input)

        self.qty_entry = ctk.CTkEntry(
            qty_row,
            textvariable=self.qty_var,
            width=105,
            height=38,
            placeholder_text="Qty",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=("Segoe UI", 12, "bold"),
            corner_radius=10,
            validate="key",
            validatecommand=(validate_qty, "%P")
        )
        self.qty_entry.pack(side="left")
        self.qty_entry.bind("<Return>", lambda event: self._add_to_cart())

        right = tk.Frame(action_box, bg=CREAM)
        right.pack(side="right", padx=14, pady=12)

        gold_btn(
            right,
            "➕ Add to Cart",
            self._add_to_cart,
            height=40,
            width=145
        ).pack(side="right")

        tk.Label(
            action_box,
            text="Tip: Double-click a product row to add it quickly.",
            font=("Segoe UI", 9, "italic"),
            bg=CREAM,
            fg="#7A5B50"
        ).pack(side="left", padx=12)

    # ============================================================
    # RIGHT SIDE: CART AND PAYMENT
    # ============================================================
    def _build_cart_payment_panel(self, parent):
        cart_card = self._card(parent)
        cart_card.pack(fill="both", expand=True)

        self._section_title(
            cart_card,
            "🛒 Order Cart",
            "Review selected items before sending the order."
        )

        self.cart_count_lbl = tk.Label(
            cart_card,
            text="0 item(s) in cart",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg="#7A5B50"
        )
        self.cart_count_lbl.pack(anchor="e", padx=16, pady=(0, 4))

        self._build_cart_table(cart_card)

        danger_btn(
            cart_card,
            "🗑 Remove Selected Item",
            self._remove_item,
            height=34
        ).pack(fill="x", padx=16, pady=(0, 8))

        self._build_discount_box(cart_card)
        self._build_totals_box(cart_card)
        self._build_payment_box(cart_card)

        primary_btn(
            cart_card,
            "📤 Send Order to Admin",
            self._send_order,
            height=44
        ).pack(fill="x", padx=16, pady=(0, 16))

    # ============================================================
    # CART TABLE
    # ============================================================
    def _build_cart_table(self, parent):
        table_box = tk.Frame(parent, bg=CARD_BG)
        table_box.pack(fill="x", padx=10, pady=(0, 8))

        cols_c = ("Name", "Qty", "Unit Price", "Subtotal")
        widths_c = [185, 55, 100, 105]

        self.cart_tree = ttk.Treeview(
            table_box,
            columns=cols_c,
            show="headings",
            style="CT.Treeview",
            height=7,
            selectmode="browse"
        )

        for col_name, width in zip(cols_c, widths_c):
            self.cart_tree.heading(col_name, text=col_name)
            self.cart_tree.column(col_name, width=width, anchor="center", minwidth=45)

        self.cart_tree.column("Name", anchor="w")

        vsb2 = ttk.Scrollbar(table_box, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=vsb2.set)

        vsb2.pack(side="right", fill="y")
        self.cart_tree.pack(fill="x")

        self.cart_tree.tag_configure("odd", background=ODD_ROW)
        self.cart_tree.tag_configure("even", background=CARD_BG)

    # ============================================================
    # DISCOUNT BOX
    # ============================================================
    def _build_discount_box(self, parent):
        discount_box = tk.Frame(
            parent,
            bg=CREAM,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        discount_box.pack(fill="x", padx=16, pady=(4, 8))

        tk.Label(
            discount_box,
            text="🏷 Discount",
            font=("Segoe UI", 13, "bold"),
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(10, 6))

        discount_row = tk.Frame(discount_box, bg=CREAM)
        discount_row.pack(fill="x", padx=14, pady=(0, 12))

        tk.Label(
            discount_row,
            text="Type:",
            font=F_BOLD,
            bg=CREAM,
            fg=TEXT
        ).pack(side="left")

        self.discount_var = tk.StringVar(master=self, value="No Discount")

        self.discount_dropdown = ctk.CTkOptionMenu(
            discount_row,
            variable=self.discount_var,
            values=[
                "No Discount",
                "PWD Discount - 20%",
                "Senior Citizen - 20%",
                "Employee Discount - 10%",
                "Promo Discount - 5%",
            ],
            width=220,
            height=36,
            fg_color=WHITE,
            button_color=GOLD,
            button_hover_color=DARK_RED,
            text_color=TEXT,
            dropdown_fg_color=WHITE,
            dropdown_text_color=TEXT,
            font=("Segoe UI", 11),
            corner_radius=10,
            command=lambda selected: self._recalculate_totals()
        )
        self.discount_dropdown.pack(side="left", padx=8)

        self.pwd_btn = ctk.CTkButton(
            discount_row,
            text="PWD",
            width=62,
            height=36,
            command=self._apply_pwd_discount,
            fg_color=GOLD,
            hover_color=DARK_RED,
            text_color=DARK_RED,
            font=("Segoe UI", 11, "bold"),
            corner_radius=10
        )
        self.pwd_btn.pack(side="left", padx=(4, 0))

    # ============================================================
    # TOTALS BOX
    # ============================================================
    def _build_totals_box(self, parent):
        totals_box = tk.Frame(
            parent,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        totals_box.pack(fill="x", padx=16, pady=(0, 8))

        rows = tk.Frame(totals_box, bg=WHITE)
        rows.pack(fill="x", padx=14, pady=(10, 8))

        # Subtotal
        row1 = tk.Frame(rows, bg=WHITE)
        row1.pack(fill="x", pady=2)

        tk.Label(
            row1,
            text="Subtotal",
            font=("Segoe UI", 10, "bold"),
            bg=WHITE,
            fg=TEXT
        ).pack(side="left")

        self.subtotal_lbl = tk.Label(
            row1,
            text="₱0.00",
            font=("Segoe UI", 11, "bold"),
            bg=WHITE,
            fg=TEXT
        )
        self.subtotal_lbl.pack(side="right")

        # Discount
        row2 = tk.Frame(rows, bg=WHITE)
        row2.pack(fill="x", pady=2)

        tk.Label(
            row2,
            text="Discount",
            font=("Segoe UI", 10, "bold"),
            bg=WHITE,
            fg=TEXT
        ).pack(side="left")

        self.discount_lbl = tk.Label(
            row2,
            text="-₱0.00",
            font=("Segoe UI", 11, "bold"),
            bg=WHITE,
            fg="#B03A2E"
        )
        self.discount_lbl.pack(side="right")

        # Divider
        tk.Frame(rows, bg=BORDER, height=1).pack(fill="x", pady=7)

        # Total
        row3 = tk.Frame(rows, bg=WHITE)
        row3.pack(fill="x", pady=2)

        tk.Label(
            row3,
            text="TOTAL PAYABLE",
            font=("Segoe UI", 11, "bold"),
            bg=WHITE,
            fg=DARK_RED
        ).pack(side="left")

        self.total_lbl = tk.Label(
            row3,
            text="₱0.00",
            font=("Georgia", 19, "bold"),
            bg=WHITE,
            fg=DARK_RED
        )
        self.total_lbl.pack(side="right")

    # ============================================================
    # PAYMENT BOX
    # ============================================================
    def _build_payment_box(self, parent):
        pay_box = tk.Frame(
            parent,
            bg=CREAM,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        pay_box.pack(fill="x", padx=16, pady=(0, 10))

        tk.Label(
            pay_box,
            text="💵 Payment",
            font=("Segoe UI", 13, "bold"),
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(10, 6))

        # Payment method
        method_row = tk.Frame(pay_box, bg=CREAM)
        method_row.pack(fill="x", padx=14, pady=(0, 7))

        tk.Label(
            method_row,
            text="Method:",
            font=F_BOLD,
            bg=CREAM,
            fg=TEXT,
            width=15,
            anchor="w"
        ).pack(side="left")

        self.payment_method_var = tk.StringVar(master=self, value="Cash")

        self.payment_method_dropdown = ctk.CTkOptionMenu(
            method_row,
            variable=self.payment_method_var,
            values=[
                "Cash",
                "Online Payment",
            ],
            width=210,
            height=36,
            fg_color=WHITE,
            button_color=GOLD,
            button_hover_color=DARK_RED,
            text_color=TEXT,
            dropdown_fg_color=WHITE,
            dropdown_text_color=TEXT,
            font=("Segoe UI", 11),
            corner_radius=10,
            command=self._on_payment_method_change
        )
        self.payment_method_dropdown.pack(side="left", padx=8)

        # Amount received
        ar_row = tk.Frame(pay_box, bg=CREAM)
        ar_row.pack(fill="x", padx=14, pady=(0, 7))

        tk.Label(
            ar_row,
            text="Amount Received:",
            font=F_BOLD,
            bg=CREAM,
            fg=TEXT,
            width=15,
            anchor="w"
        ).pack(side="left")

        self.received_var = tk.StringVar(master=self)
        validate_money = self.register(self._validate_money_input)

        self.received_entry = ctk.CTkEntry(
            ar_row,
            textvariable=self.received_var,
            width=210,
            height=36,
            placeholder_text="0.00",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=("Segoe UI", 12),
            corner_radius=10,
            validate="key",
            validatecommand=(validate_money, "%P")
        )
        self.received_entry.pack(side="left", padx=8)

        self.received_var.trace_add("write", lambda *_: self._calc_change())

        # Online reference
        ref_row = tk.Frame(pay_box, bg=CREAM)
        ref_row.pack(fill="x", padx=14, pady=(0, 7))

        tk.Label(
            ref_row,
            text="Online Ref No:",
            font=F_BOLD,
            bg=CREAM,
            fg=TEXT,
            width=15,
            anchor="w"
        ).pack(side="left")

        self.reference_var = tk.StringVar(master=self)

        self.reference_entry = ctk.CTkEntry(
            ref_row,
            textvariable=self.reference_var,
            width=210,
            height=36,
            placeholder_text="GCash/Maya reference",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=("Segoe UI", 12),
            corner_radius=10,
            state="disabled"
        )
        self.reference_entry.pack(side="left", padx=8)

        # Change
        change_box = tk.Frame(
            pay_box,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        change_box.pack(fill="x", padx=14, pady=(2, 12))

        tk.Label(
            change_box,
            text="Change",
            font=("Segoe UI", 10, "bold"),
            bg=WHITE,
            fg=TEXT
        ).pack(side="left", padx=12, pady=9)

        self.change_lbl = tk.Label(
            change_box,
            text="₱0.00",
            font=("Georgia", 17, "bold"),
            bg=WHITE,
            fg="#1E8449"
        )
        self.change_lbl.pack(side="right", padx=12, pady=9)

    # ============================================================
    # QUICK PWD BUTTON
    # ============================================================
    def _apply_pwd_discount(self):
        self.discount_var.set("PWD Discount - 20%")
        self._recalculate_totals()

    # ============================================================
    # CLEAR SEARCH
    # ============================================================
    def _clear_search(self):
        self.srch_var.set("")
        self._refresh_products()

    # ============================================================
    # REFRESH PRODUCTS FROM DATABASE
    # ============================================================
    def _refresh_products(self):
        try:
            self.configure(cursor="watch")
            self.update_idletasks()

            products = get_all_products()
            self.current_products = products
            self._load_products(products)

        except Exception as e:
            messagebox.showerror(
                "Products Error",
                f"Unable to load products from database.\n\n{safe_error(e)}",
                parent=self
            )

        finally:
            self.configure(cursor="")

    # ============================================================
    # SEARCH PRODUCTS
    # ============================================================
    def _search_products(self):
        keyword = self.srch_var.get().strip()

        try:
            self.configure(cursor="watch")
            self.update_idletasks()

            if keyword:
                products = search_products(keyword)
            else:
                products = get_all_products()

            self.current_products = products
            self._load_products(products)

        except Exception as e:
            messagebox.showerror(
                "Search Error",
                f"Unable to search products.\n\n{safe_error(e)}",
                parent=self
            )

        finally:
            self.configure(cursor="")

    # ============================================================
    # LOAD PRODUCTS INTO TABLE
    # ============================================================
    def _load_products(self, products):
        self.prod_tree.delete(*self.prod_tree.get_children())

        if hasattr(self, "product_count_lbl"):
            self.product_count_lbl.configure(text=f"{len(products)} product(s)")

        if not products:
            self.prod_tree.insert(
                "",
                "end",
                values=("—", "No products found", "₱0.00", "—", "0"),
                tags=("even",)
            )
            return

        for index, product in enumerate(products):
            product_id = product["product_id"]
            product_name = product["product_name"]
            price = float(product["price"] or 0)
            unit = product["unit"]
            quantity = int(product["quantity"] or 0)

            if quantity <= 0:
                tag = "out"
            elif quantity < 10:
                tag = "low"
            else:
                tag = "odd" if index % 2 else "even"

            self.prod_tree.insert(
                "",
                "end",
                values=(
                    product_id,
                    product_name,
                    format_money(price),
                    unit,
                    quantity
                ),
                tags=(tag,)
            )

    # ============================================================
    # ADD PRODUCT TO CART
    # ============================================================
    def _add_to_cart(self):
        selected_row = self.prod_tree.focus()

        if not selected_row:
            messagebox.showwarning(
                "Cart",
                "Select a product first.",
                parent=self
            )
            return

        values = self.prod_tree.item(selected_row, "values")

        if not values or values[0] == "—":
            return

        product_id = int(values[0])
        product_name = values[1]
        price = safe_money_to_float(values[2])
        unit = values[3]
        stock = int(values[4])

        if stock <= 0:
            messagebox.showwarning(
                "Cart",
                "This product is out of stock and cannot be added to the cart.",
                parent=self
            )
            return

        qty_text = self.qty_var.get().strip()

        if qty_text == "":
            messagebox.showwarning(
                "Quantity",
                "Enter quantity first.",
                parent=self
            )
            return

        try:
            quantity = int(qty_text)
        except Exception:
            messagebox.showwarning(
                "Quantity",
                "Quantity must be a whole number.",
                parent=self
            )
            self.qty_var.set("1")
            return

        if quantity <= 0:
            messagebox.showwarning(
                "Quantity",
                "Quantity must be at least 1.",
                parent=self
            )
            self.qty_var.set("1")
            return

        if quantity > stock:
            messagebox.showwarning(
                "Cart",
                f"Only {stock} in stock.",
                parent=self
            )
            return

        for item in self.cart:
            if item["product_id"] == product_id:
                if item["quantity"] + quantity > stock:
                    messagebox.showwarning(
                        "Cart",
                        f"Only {stock} total in stock.",
                        parent=self
                    )
                    return

                item["quantity"] += quantity
                self.qty_var.set("1")
                self._refresh_cart()
                return

        self.cart.append(
            {
                "product_id": product_id,
                "product_name": product_name,
                "price": price,
                "unit": unit,
                "quantity": quantity,
                "stock": stock
            }
        )

        self.qty_var.set("1")
        self._refresh_cart()

    # ============================================================
    # REFRESH CART TABLE
    # ============================================================
    def _refresh_cart(self):
        self.cart_tree.delete(*self.cart_tree.get_children())

        if hasattr(self, "cart_count_lbl"):
            total_items = sum(item["quantity"] for item in self.cart)
            self.cart_count_lbl.configure(
                text=f"{len(self.cart)} product(s), {total_items} item(s) in cart"
            )

        for index, item in enumerate(self.cart):
            subtotal = item["price"] * item["quantity"]

            self.cart_tree.insert(
                "",
                "end",
                values=(
                    item["product_name"],
                    item["quantity"],
                    format_money(item["price"]),
                    format_money(subtotal)
                ),
                tags=("odd" if index % 2 else "even",)
            )

        self._recalculate_totals()
        self._on_payment_method_change()

    # ============================================================
    # CALCULATE CHANGE
    # ============================================================
    def _calc_change(self):
        total = getattr(self, "_payable_total", 0.0)
        payment_method = self.payment_method_var.get()

        if payment_method == "Online Payment":
            self.change_lbl.configure(text="₱0.00", fg="#1E8449")
            return

        received_text = self.received_var.get().strip()
        received = safe_money_to_float(received_text)

        if received_text == "":
            self.change_lbl.configure(text="₱0.00", fg="#1E8449")
            return

        change = received - total

        if change < 0:
            self.change_lbl.configure(
                text=f"-{format_money(abs(change))} insufficient",
                fg="#B03A2E"
            )
        else:
            self.change_lbl.configure(
                text=format_money(change),
                fg="#1E8449"
            )

    # ============================================================
    # REMOVE SELECTED CART ITEM
    # ============================================================
    def _remove_item(self):
        selected_row = self.cart_tree.focus()

        if not selected_row:
            messagebox.showwarning(
                "Cart",
                "Select an item from the cart first.",
                parent=self
            )
            return

        index = self.cart_tree.index(selected_row)

        if 0 <= index < len(self.cart):
            self.cart.pop(index)

        self._refresh_cart()

    # ============================================================
    # PREPARE ORDER ITEMS FOR DATABASE
    # ============================================================
    def _prepare_order_items(self):
        order_items = []

        for item in self.cart:
            subtotal = item["price"] * item["quantity"]

            order_items.append(
                {
                    "product_id": item["product_id"],
                    "product_name": item["product_name"],
                    "price": item["price"],
                    "unit_price": item["price"],
                    "quantity": item["quantity"],
                    "qty": item["quantity"],
                    "subtotal": subtotal
                }
            )

        return order_items

    # ============================================================
    # CREATE ORDER USING ORDER BACKEND
    # ============================================================
    def _create_order_in_database(
        self,
        order_items,
        amount_received,
        change_amount,
        discount_type,
        discount_amount,
        payment_method,
        online_reference
    ):
        try:
            return create_order(
                cashier_id=self.cashier_id,
                order_items=order_items,
                amount_received=amount_received,
                change_amount=change_amount,
                discount_type=discount_type,
                discount_amount=discount_amount,
                payment_method=payment_method,
                online_reference=online_reference
            )
        except TypeError:
            pass

        try:
            return create_order(
                self.cashier_id,
                order_items,
                amount_received,
                change_amount,
                discount_type,
                discount_amount,
                payment_method,
                online_reference
            )
        except TypeError:
            pass

        try:
            return create_order(
                self.cashier_id,
                order_items,
                amount_received,
                change_amount
            )
        except TypeError:
            pass

        try:
            return create_order(
                self.cashier_id,
                order_items,
                amount_received
            )
        except TypeError:
            return create_order(
                self.cashier_id,
                order_items
            )

    # ============================================================
    # SEND ORDER TO ADMIN
    # ============================================================
    def _send_order(self):
        if not self.cashier_id:
            messagebox.showerror(
                "Cashier Error",
                "Cashier account was not found in the database.\n\n"
                "Make sure this cashier exists in the users table and is active.",
                parent=self
            )
            return

        if not self.cart:
            messagebox.showwarning(
                "Order",
                "Cart is empty.",
                parent=self
            )
            return

        subtotal = sum(item["price"] * item["quantity"] for item in self.cart)
        discount_type = self.discount_var.get()
        discount_amount = self._discount_amount
        total = self._payable_total
        payment_method = self.payment_method_var.get()
        online_reference = self.reference_var.get().strip()

        if payment_method == "Cash":
            received_text = self.received_var.get().strip()

            if received_text == "":
                messagebox.showwarning(
                    "Payment",
                    "Enter amount received.",
                    parent=self
                )
                return

            amount_received = safe_money_to_float(received_text)

            if amount_received < total:
                messagebox.showwarning(
                    "Payment",
                    f"Amount received ({format_money(amount_received)}) is less than total ({format_money(total)}).",
                    parent=self
                )
                return

            change_amount = amount_received - total

        else:
            if online_reference == "":
                messagebox.showwarning(
                    "Online Payment",
                    "Enter the online payment reference number.",
                    parent=self
                )
                return

            amount_received = total
            change_amount = 0.0

        confirm = messagebox.askyesno(
            "Send Order",
            f"Send this order to admin?\n\n"
            f"Subtotal: {format_money(subtotal)}\n"
            f"Discount Type: {discount_type}\n"
            f"Discount Amount: -{format_money(discount_amount)}\n"
            f"Total Payable: {format_money(total)}\n\n"
            f"Payment Method: {payment_method}\n"
            f"Amount Received: {format_money(amount_received)}\n"
            f"Change: {format_money(change_amount)}\n"
            f"{'Reference No: ' + online_reference if payment_method == 'Online Payment' else ''}",
            parent=self
        )

        if not confirm:
            return

        try:
            order_items = self._prepare_order_items()

            result = self._create_order_in_database(
                order_items,
                amount_received,
                change_amount,
                discount_type,
                discount_amount,
                payment_method,
                online_reference
            )

            success = False
            message = "Order sent successfully."
            order_id = None

            if isinstance(result, tuple):
                success = bool(result[0])

                if len(result) >= 2:
                    message = str(result[1])

                if len(result) >= 3:
                    order_id = result[2]

            elif isinstance(result, int):
                success = True
                order_id = result

            elif result:
                success = True

            if not success:
                messagebox.showerror(
                    "Order Failed",
                    f"Unable to send order.\n\n{message}",
                    parent=self
                )
                return

            order_text = f"#{order_id}" if order_id else ""

            messagebox.showinfo(
                "Order Sent",
                f"✅ Order {order_text} sent to admin!\n\n"
                f"Subtotal: {format_money(subtotal)}\n"
                f"Discount: -{format_money(discount_amount)}\n"
                f"Total Payable: {format_money(total)}\n\n"
                f"Payment Method: {payment_method}\n"
                f"Amount Received: {format_money(amount_received)}\n"
                f"Change: {format_money(change_amount)}\n"
                f"{'Reference No: ' + online_reference if payment_method == 'Online Payment' else ''}\n\n"
                f"Status: Pending admin approval",
                parent=self
            )

            self.cart.clear()
            self.received_var.set("")
            self.reference_var.set("")
            self.qty_var.set("1")
            self.discount_var.set("No Discount")
            self.payment_method_var.set("Cash")
            self.reference_entry.configure(state="disabled")
            self.received_entry.configure(state="normal")

            self._refresh_cart()
            self._refresh_products()

        except Exception as e:
            messagebox.showerror(
                "Order Error",
                f"Unable to save order to database.\n\nError:\n{safe_error(e)}",
                parent=self
            )


# ============================================================
# RUN DIRECTLY FOR TESTING
# ============================================================
if __name__ == "__main__":
    CashierOrders("Cashier").mainloop()