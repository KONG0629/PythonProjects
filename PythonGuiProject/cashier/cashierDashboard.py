import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from theme import *

from databases.product_backend import get_inventory_products
from databases.db import fetch_one

ctk.set_appearance_mode("light")


# ============================================================
# HELPERS
# ============================================================
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


def format_value(value):
    return "—" if value is None else str(value)


def safe_error(error):
    text = str(error).strip()
    return text if text else repr(error)


# ============================================================
# MAIN CASHIER DASHBOARD
# ============================================================
class CashierDashboard(ctk.CTk):
    def __init__(self, user_name="Cashier", cashier_id=None, start_page="products"):
        super().__init__()

        self.user_name = user_name
        self.cashier_id = cashier_id or self._resolve_cashier_id()

        self.products = []
        self.filtered_products = []
        self.sort_asc = True

        self.filter_var = tk.StringVar(master=self, value="All")
        self.srch_var = tk.StringVar(master=self)

        self.title("Cashier — Dashboard")
        self.configure(fg_color=BG)
        self.attributes("-fullscreen", True)

        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="right", fill="both", expand=True)

        if start_page == "order_status":
            self._show_order_status()
        else:
            self._show_dashboard()

    # ============================================================
    # SIDEBAR
    # ============================================================
    def _nav_items(self):
        return [
            ("products", "🧺", "Dashboard", self._show_dashboard),
            ("orders", "📋", "Orders", self._go_orders),
            ("order_status", "🧾", "Order Status", self._show_order_status),
        ]

    def _set_sidebar(self, active_key):
        make_sidebar(
            self,
            self.user_name,
            "Cashier",
            self._nav_items(),
            active_key
        )

    # ============================================================
    # CASHIER ID
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
            return result["user_id"] if result else None

        except Exception:
            return None

    # ============================================================
    # NAVIGATION
    # ============================================================
    def _go_orders(self):
        try:
            self.configure(cursor="watch")
            self.update_idletasks()

            from cashier.orders import CashierOrders

            self.destroy()

            app = CashierOrders(self.user_name, self.cashier_id)
            app.mainloop()

        except Exception as e:
            messagebox.showerror(
                "Navigation Error",
                f"Unable to open Orders page.\n\n{safe_error(e)}"
            )

    def _clear_main(self):
        for widget in self.main.winfo_children():
            widget.destroy()

    # ============================================================
    # CASHIER DASHBOARD PAGE
    # ============================================================
    def _show_dashboard(self):
        self._set_sidebar("products")
        self._clear_main()

        self._build_header()
        self._build_summary_cards()

        content = tk.Frame(self.main, bg=BG)
        content.pack(fill="both", expand=True, padx=22, pady=(0, 20))

        left_area = tk.Frame(content, bg=BG)
        left_area.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right_area = tk.Frame(content, bg=BG, width=365)
        right_area.pack(side="right", fill="y")
        right_area.pack_propagate(False)

        self._build_search_filter(left_area)
        self._build_table(left_area)

        self.alert_panel = self._create_card(
            right_area,
            bg_color="#FFF8E1",
            border_color=GOLD
        )
        self.alert_panel.pack(fill="both", expand=True)

        self._refresh_products()

    # ============================================================
    # HEADER UI
    # ============================================================
    def _build_header(self):
        header = tk.Frame(self.main, bg=CREAM, height=94)
        header.pack(fill="x")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=CREAM)
        left.pack(side="left", padx=26, pady=14)

        tk.Label(
            left,
            text="🧺 Cashier Dashboard",
            font=("Georgia", 23, "bold"),
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w")

        tk.Label(
            left,
            text=f"Welcome, {self.user_name}. Monitor product availability and create customer orders quickly.",
            font=("Segoe UI", 10, "bold"),
            bg=CREAM,
            fg=TEXT
        ).pack(anchor="w", pady=(2, 0))

        right = tk.Frame(header, bg=CREAM)
        right.pack(side="right", padx=22, pady=18)

        gold_btn(
            right,
            "📋 Create Order",
            self._go_orders,
            height=38,
            width=155
        ).pack(side="left", padx=5)

        primary_btn(
            right,
            "🧾 Order Status",
            self._show_order_status,
            height=38,
            width=150
        ).pack(side="left", padx=5)

        primary_btn(
            right,
            "🔄 Refresh",
            self._refresh_products,
            height=38,
            width=115
        ).pack(side="left", padx=5)

    # ============================================================
    # CARD HELPERS
    # ============================================================
    def _create_card(self, parent, bg_color=None, border_color=None):
        return tk.Frame(
            parent,
            bg=bg_color or CARD_BG,
            highlightbackground=border_color or BORDER,
            highlightthickness=1
        )

    def _build_summary_cards(self):
        self.card_frame = tk.Frame(self.main, bg=BG)
        self.card_frame.pack(fill="x", padx=22, pady=(16, 14))

    def _stat_card(self, parent, index, title, value, subtitle, color):
        card = tk.Frame(parent, bg=color, height=112)
        card.grid(row=0, column=index, sticky="ew", padx=7)
        card.grid_propagate(False)

        parent.columnconfigure(index, weight=1)

        tk.Label(
            card,
            text=title,
            font=("Segoe UI", 10, "bold"),
            bg=color,
            fg=CREAM
        ).pack(anchor="w", padx=16, pady=(14, 0))

        tk.Label(
            card,
            text=value,
            font=("Georgia", 25, "bold"),
            bg=color,
            fg=WHITE
        ).pack(anchor="w", padx=16, pady=(1, 0))

        tk.Label(
            card,
            text=subtitle,
            font=("Segoe UI", 9),
            bg=color,
            fg=CREAM
        ).pack(anchor="w", padx=16, pady=(2, 10))

    # ============================================================
    # SEARCH AND FILTER UI
    # ============================================================
    def _build_search_filter(self, parent):
        bar = self._create_card(parent)
        bar.pack(fill="x", pady=(0, 12))

        title_row = tk.Frame(bar, bg=CARD_BG)
        title_row.pack(fill="x", padx=16, pady=(12, 4))

        tk.Label(
            title_row,
            text="🔍 Product Search & Filter",
            font=("Segoe UI", 14, "bold"),
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left")

        tk.Label(
            title_row,
            text="Double-click a product row to view details.",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg="#8A6D3B"
        ).pack(side="right")

        inner = tk.Frame(bar, bg=CARD_BG)
        inner.pack(fill="x", padx=16, pady=(6, 14))

        self.search_entry = ctk.CTkEntry(
            inner,
            textvariable=self.srch_var,
            width=345,
            height=39,
            placeholder_text="Search product name, category, unit, stock, or status…",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=("Segoe UI", 10),
            corner_radius=10
        )
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda event: self._apply_filter_sort_load())

        primary_btn(
            inner,
            "Search",
            self._apply_filter_sort_load,
            height=37,
            width=90
        ).pack(side="left", padx=4)

        self.sort_btn = gold_btn(
            inner,
            "A → Z",
            self._toggle_sort,
            height=37,
            width=85
        )
        self.sort_btn.pack(side="left", padx=4)

        tk.Label(
            inner,
            text="Status:",
            font=("Segoe UI", 10, "bold"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(15, 5))

        self.filter_cb = ttk.Combobox(
            inner,
            textvariable=self.filter_var,
            values=["All", "Available", "Low Stock", "Out of Stock", "Unavailable"],
            width=15,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.filter_cb.pack(side="left", padx=4)
        self.filter_cb.bind("<<ComboboxSelected>>", lambda event: self._apply_filter_sort_load())

        gold_btn(
            inner,
            "Show All",
            self._show_all,
            height=37,
            width=95
        ).pack(side="left", padx=4)

    # ============================================================
    # TABLE UI
    # ============================================================
    def _build_table(self, parent):
        table_card = self._create_card(parent)
        table_card.pack(fill="both", expand=True)

        table_header = tk.Frame(table_card, bg=CARD_BG)
        table_header.pack(fill="x", padx=16, pady=(14, 6))

        left = tk.Frame(table_header, bg=CARD_BG)
        left.pack(side="left")

        tk.Label(
            left,
            text="📦 Product Availability",
            font=("Segoe UI", 15, "bold"),
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Unavailable and out-of-stock products are shown for cashier awareness.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg="#7B7D7D"
        ).pack(anchor="w", pady=(1, 0))

        self.result_label = tk.Label(
            table_header,
            text="0 product(s) shown",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg="#7B7D7D"
        )
        self.result_label.pack(side="right", pady=(18, 0))

        tbl = tk.Frame(table_card, bg=CARD_BG)
        tbl.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "CD.Treeview",
            background=CARD_BG,
            fieldbackground=CARD_BG,
            foreground=TEXT,
            rowheight=41,
            font=("Segoe UI", 10)
        )

        style.configure(
            "CD.Treeview.Heading",
            background=SIDEBAR,
            foreground=WHITE,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )

        style.map(
            "CD.Treeview",
            background=[("selected", GOLD)],
            foreground=[("selected", DARK_RED)]
        )

        cols = ("ID", "Name", "Category", "Price", "Unit", "Stock", "Status")
        widths = [60, 300, 150, 115, 85, 90, 145]

        self.tree = ttk.Treeview(
            tbl,
            columns=cols,
            show="headings",
            style="CD.Treeview"
        )

        for col_name, width in zip(cols, widths):
            self.tree.heading(col_name, text=col_name)
            self.tree.column(col_name, width=width, anchor="center", minwidth=50)

        self.tree.column("Name", anchor="w")
        self.tree.column("Category", anchor="w")

        vsb = ttk.Scrollbar(tbl, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(tbl, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=xsb.set)

        vsb.pack(side="right", fill="y")
        xsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.tree.tag_configure("odd", background=ODD_ROW)
        self.tree.tag_configure("even", background=CARD_BG)
        self.tree.tag_configure("low", background="#FFF3CD", foreground="#8A6D00")
        self.tree.tag_configure("out", background="#FDECEA", foreground="#B03A2E")
        self.tree.tag_configure("inactive", background="#F2F3F4", foreground="#7B7D7D")

        self.tree.bind("<Double-1>", self._detail)

    # ============================================================
    # CASHIER ORDER STATUS PAGE
    # ============================================================
    def _show_order_status(self):
        self._set_sidebar("order_status")
        self._clear_main()

        try:
            from cashier.cashierOrderStatus import CashierOrderStatus

            CashierOrderStatus(
                self.main,
                user_name=self.user_name
            )

        except Exception as e:
            messagebox.showerror(
                "Order Status Error",
                f"Unable to open Cashier Order Status page.\n\n{safe_error(e)}",
                parent=self
            )

    # ============================================================
    # PRODUCT DASHBOARD FUNCTIONS
    # ============================================================
    def _build_cards(self, products):
        for widget in self.card_frame.winfo_children():
            widget.destroy()

        total_products = len(products)

        available_products = sum(
            1 for p in products
            if str(p.get("status", "active")).lower() == "active"
            and safe_int(p.get("quantity")) > 0
        )

        unavailable_products = sum(
            1 for p in products
            if str(p.get("status", "active")).lower() == "inactive"
        )

        low_stock = sum(
            1 for p in products
            if str(p.get("status", "active")).lower() == "active"
            and 0 < safe_int(p.get("quantity")) < 10
        )

        out_stock = sum(
            1 for p in products
            if str(p.get("status", "active")).lower() == "active"
            and safe_int(p.get("quantity")) <= 0
        )

        self._stat_card(
            self.card_frame,
            0,
            "🧺 Total Products",
            str(total_products),
            "All registered items",
            SIDEBAR
        )

        self._stat_card(
            self.card_frame,
            1,
            "✅ Available",
            str(available_products),
            "Can be added to orders",
            "#1E8449"
        )

        self._stat_card(
            self.card_frame,
            2,
            "⚠️ Low Stock",
            str(low_stock),
            "Needs restock soon",
            GOLD
        )

        self._stat_card(
            self.card_frame,
            3,
            "🚫 Unavailable / Out",
            str(unavailable_products + out_stock),
            "Do not sell",
            "#B03A2E"
        )

    def _build_alert_panel(self, products):
        for widget in self.alert_panel.winfo_children():
            widget.destroy()

        tk.Label(
            self.alert_panel,
            text="⚠️ Product Watch",
            font=("Segoe UI", 15, "bold"),
            bg="#FFF8E1",
            fg=DARK_RED
        ).pack(anchor="w", padx=16, pady=(15, 2))

        tk.Label(
            self.alert_panel,
            text="Low stock, out-of-stock, and unavailable products.",
            font=("Segoe UI", 9),
            bg="#FFF8E1",
            fg="#8A6D3B",
            wraplength=310,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        watch_items = [
            p for p in products
            if str(p.get("status", "active")).lower() == "inactive"
            or (
                str(p.get("status", "active")).lower() == "active"
                and safe_int(p.get("quantity")) < 10
            )
        ]

        if not watch_items:
            empty_box = tk.Frame(self.alert_panel, bg="#FFF8E1")
            empty_box.pack(fill="both", expand=True, padx=16, pady=20)

            tk.Label(
                empty_box,
                text="✅ All Good",
                font=("Segoe UI", 19, "bold"),
                bg="#FFF8E1",
                fg="#1E8449"
            ).pack(pady=(70, 4))

            tk.Label(
                empty_box,
                text="No product needs cashier attention right now.",
                font=("Segoe UI", 10),
                bg="#FFF8E1",
                fg="#1E8449",
                wraplength=280,
                justify="center"
            ).pack()

            return

        legend = tk.Frame(self.alert_panel, bg="#FFF8E1")
        legend.pack(fill="x", padx=16, pady=(0, 8))

        tk.Label(
            legend,
            text=f"{len(watch_items)} item(s) need attention",
            font=("Segoe UI", 9, "bold"),
            bg="#FFF8E1",
            fg="#B03A2E"
        ).pack(anchor="w")

        scroll_holder = tk.Frame(self.alert_panel, bg="#FFF8E1")
        scroll_holder.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        canvas = tk.Canvas(
            scroll_holder,
            bg="#FFF8E1",
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            scroll_holder,
            orient="vertical",
            command=canvas.yview
        )

        list_frame = tk.Frame(canvas, bg="#FFF8E1")

        list_frame.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for item in watch_items:
            name = item.get("product_name", "Unnamed")
            qty = safe_int(item.get("quantity"))
            unit = item.get("unit", "")
            status = str(item.get("status", "active")).lower()

            if status == "inactive":
                title = "UNAVAILABLE"
                desc = f"{name}"
                color = "#7B7D7D"
                icon = "🚫"
            elif qty <= 0:
                title = "OUT OF STOCK"
                desc = f"{name}"
                color = "#B03A2E"
                icon = "📦"
            else:
                title = "LOW STOCK"
                desc = f"{name} — {qty} {unit}"
                color = "#8A6D00"
                icon = "⚠️"

            item_card = tk.Frame(
                list_frame,
                bg=WHITE,
                highlightbackground="#E0D4A8",
                highlightthickness=1
            )
            item_card.pack(fill="x", padx=2, pady=5)

            tk.Label(
                item_card,
                text=f"{icon} {title}",
                font=("Segoe UI", 8, "bold"),
                bg=WHITE,
                fg=color
            ).pack(anchor="w", padx=10, pady=(8, 0))

            tk.Label(
                item_card,
                text=desc,
                font=("Segoe UI", 10, "bold"),
                bg=WHITE,
                fg=TEXT,
                wraplength=285,
                justify="left"
            ).pack(anchor="w", padx=10, pady=(2, 8))

    def _refresh_products(self):
        try:
            self.configure(cursor="watch")
            self.update_idletasks()

            self.products = get_inventory_products()

            self._build_cards(self.products)
            self._build_alert_panel(self.products)
            self._apply_filter_sort_load()

        except Exception as e:
            messagebox.showerror(
                "Products Error",
                f"Unable to load products from database.\n\n{safe_error(e)}",
                parent=self
            )

        finally:
            self.configure(cursor="")

    def _show_all(self):
        self.srch_var.set("")
        self.filter_var.set("All")
        self._apply_filter_sort_load()

    def _product_matches_search(self, product, keyword):
        if not keyword:
            return True

        keyword = keyword.lower().strip()

        display_status = (
            "unavailable"
            if str(product.get("status", "active")).lower() == "inactive"
            else "available"
        )

        searchable_text = " ".join([
            str(product.get("product_id", "")),
            str(product.get("product_name", "")),
            str(product.get("category", "")),
            str(product.get("price", "")),
            str(product.get("unit", "")),
            str(product.get("quantity", "")),
            str(product.get("status", "")),
            display_status,
        ]).lower()

        return keyword in searchable_text

    def _apply_filter_sort_load(self):
        keyword = self.srch_var.get().strip()
        selected_filter = self.filter_var.get()

        products = [
            p for p in self.products
            if self._product_matches_search(p, keyword)
        ]

        if selected_filter == "Available":
            products = [
                p for p in products
                if str(p.get("status", "active")).lower() == "active"
                and safe_int(p.get("quantity")) > 0
            ]

        elif selected_filter == "Low Stock":
            products = [
                p for p in products
                if str(p.get("status", "active")).lower() == "active"
                and 0 < safe_int(p.get("quantity")) < 10
            ]

        elif selected_filter == "Out of Stock":
            products = [
                p for p in products
                if str(p.get("status", "active")).lower() == "active"
                and safe_int(p.get("quantity")) <= 0
            ]

        elif selected_filter == "Unavailable":
            products = [
                p for p in products
                if str(p.get("status", "active")).lower() == "inactive"
            ]

        sorted_products = sorted(
            products,
            key=lambda row: str(row.get("product_name", "")).lower(),
            reverse=not self.sort_asc
        )

        self.filtered_products = sorted_products
        self._load(sorted_products)

    def _toggle_sort(self):
        self.sort_asc = not self.sort_asc
        self.sort_btn.configure(text="A → Z" if self.sort_asc else "Z → A")
        self._apply_filter_sort_load()

    def _load(self, products):
        self.tree.delete(*self.tree.get_children())

        if hasattr(self, "result_label"):
            self.result_label.configure(text=f"{len(products)} product(s) shown")

        if not products:
            self.tree.insert(
                "",
                "end",
                values=("—", "No products found", "—", "₱0.00", "—", "0", "—"),
                tags=("even",)
            )
            return

        for index, product in enumerate(products):
            product_id = product.get("product_id")
            product_name = product.get("product_name")
            category = product.get("category", "—")
            price = float(product.get("price") or 0)
            unit = product.get("unit", "—")
            quantity = safe_int(product.get("quantity"))
            status = str(product.get("status", "active")).lower()

            if status == "inactive":
                tag = "inactive"
                status_text = "Unavailable"
            elif quantity <= 0:
                tag = "out"
                status_text = "Out of Stock"
            elif quantity < 10:
                tag = "low"
                status_text = "Low Stock"
            else:
                tag = "odd" if index % 2 else "even"
                status_text = "Available"

            self.tree.insert(
                "",
                "end",
                values=(
                    product_id,
                    product_name,
                    category,
                    format_money(price),
                    unit,
                    quantity,
                    status_text
                ),
                tags=(tag,)
            )

    # ============================================================
    # PRODUCT DETAILS POPUP
    # ============================================================
    def _detail(self, event=None):
        selected_row = self.tree.focus()

        if not selected_row:
            return

        values = self.tree.item(selected_row, "values")

        if not values or values[0] == "—":
            return

        win = ctk.CTkToplevel(self)
        win.title("Product Details")
        win.geometry("550x500")
        win.resizable(False, False)
        win.grab_set()
        win.configure(fg_color=BG)

        tk.Label(
            win,
            text="🐔 Product Details",
            font=("Georgia", 21, "bold"),
            bg=BG,
            fg=DARK_RED
        ).pack(pady=(24, 6))

        tk.Label(
            win,
            text="Review this product before adding it to an order.",
            font=("Segoe UI", 10),
            bg=BG,
            fg=TEXT
        ).pack(pady=(0, 14))

        box = tk.Frame(
            win,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        box.pack(padx=34, fill="x")

        labels = ["ID", "Name", "Category", "Price", "Unit", "Stock", "Status"]

        for label, value in zip(labels, values):
            row = tk.Frame(box, bg=CARD_BG)
            row.pack(fill="x", padx=18, pady=8)

            tk.Label(
                row,
                text=f"{label}:",
                font=("Segoe UI", 10, "bold"),
                bg=CARD_BG,
                fg=DARK_RED,
                width=12,
                anchor="w"
            ).pack(side="left")

            tk.Label(
                row,
                text=format_value(value),
                font=("Segoe UI", 10),
                bg=CARD_BG,
                fg=TEXT,
                anchor="w",
                wraplength=350,
                justify="left"
            ).pack(side="left")

        status = values[6]

        if status == "Unavailable":
            msg = "This product is unavailable and should not be added to orders."
            color = "#B03A2E"
            icon = "🚫"
        elif status == "Out of Stock":
            msg = "This product is currently out of stock."
            color = "#B03A2E"
            icon = "📦"
        elif status == "Low Stock":
            msg = "This product is available, but stock is low."
            color = "#8A6D00"
            icon = "⚠️"
        else:
            msg = "This product is available for selling."
            color = "#1E8449"
            icon = "✅"

        status_box = tk.Frame(
            win,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        status_box.pack(fill="x", padx=34, pady=(14, 4))

        tk.Label(
            status_box,
            text=f"{icon} {msg}",
            font=("Segoe UI", 10, "bold"),
            bg=WHITE,
            fg=color,
            wraplength=430,
            justify="center"
        ).pack(padx=14, pady=12)

        primary_btn(
            win,
            "Close",
            win.destroy,
            height=38,
            width=120
        ).pack(pady=16)


# ============================================================
# RUN
# ============================================================
def run(user_name="Cashier", cashier_id=None):
    app = CashierDashboard(user_name, cashier_id)
    app.mainloop()


if __name__ == "__main__":
    CashierDashboard("Cashier").mainloop()