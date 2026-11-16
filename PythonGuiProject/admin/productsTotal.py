import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from theme import *

from databases.product_backend import (
    get_inventory_products,
    get_product_by_id,
    add_product,
    update_product,
    set_product_status
)

ctk.set_appearance_mode("light")


CHICKEN_CATEGORIES = [
    "General Chicken",
    "Whole Chicken",
    "Breast Cuts",
    "Leg Cuts",
    "Wing Cuts",
    "Thigh Cuts",
    "Drumstick Cuts",
    "Mixed Chicken Cuts",
    "Organ / Offal",
    "Bones / Soup Parts",
    "Skin / Fat Parts",
    "Head / Neck / Feet",
    "Processed Chicken",
    "Frozen Chicken",
    "Fresh Chicken",
    "Others"
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


def short_text(value, limit=35):
    value = str(value or "")

    if len(value) <= limit:
        return value

    return value[:limit - 1] + "…"


class AdminProductsTotal(ctk.CTk):
    def __init__(self, user_name="Admin", admin_id=None):
        super().__init__()

        self.user_name = user_name
        self.admin_id = admin_id

        self.products = []
        self.filtered_products = []

        self.search_var = tk.StringVar(master=self)
        self.filter_var = tk.StringVar(master=self, value="All")
        self.category_var = tk.StringVar(master=self, value="All Categories")
        self.sort_asc = True

        self.selected_product_id = None

        self.title("Admin — Manage Products")
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
                app = AdminProductsTotal(self.user_name, self.admin_id)

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
    # SCROLLABLE CARD CONTENT
    # ============================================================
    def _make_scrollable_area(self, parent, bg_color="#FFF8E1"):
        container = tk.Frame(parent, bg=bg_color)
        container.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        canvas = tk.Canvas(
            container,
            bg=bg_color,
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=canvas.yview
        )

        content = tk.Frame(canvas, bg=bg_color)

        window_id = canvas.create_window(
            (0, 0),
            window=content,
            anchor="nw"
        )

        canvas.configure(yscrollcommand=scrollbar.set)

        def update_scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_content(event):
            canvas.itemconfig(window_id, width=event.width)

        def mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        content.bind("<Configure>", update_scrollregion)
        canvas.bind("<Configure>", resize_content)

        canvas.bind("<MouseWheel>", mousewheel)
        content.bind("<MouseWheel>", mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return content

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

        make_sidebar(self, self.user_name, "Administrator", nav, "products")

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
            text="📋 Product Management",
            font=F_TITLE,
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w")

        tk.Label(
            left_hdr,
            text="Manage product records, stock availability, category, price, and quantity.",
            font=("Segoe UI", 10, "italic"),
            bg=CREAM,
            fg=TEXT
        ).pack(anchor="w")

        right_hdr = tk.Frame(hdr, bg=CREAM)
        right_hdr.pack(side="right", padx=20, pady=10)

        import datetime

        tk.Label(
            right_hdr,
            text=datetime.datetime.now().strftime("%B %d, %Y"),
            font=("Segoe UI", 11, "bold"),
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="e")

        tk.Label(
            right_hdr,
            text=datetime.datetime.now().strftime("%A"),
            font=F_SMALL,
            bg=CREAM,
            fg=TEXT
        ).pack(anchor="e")

        # ========================================================
        # KPI CARDS
        # ========================================================
        self.kpi = tk.Frame(self.main, bg=BG)
        self.kpi.pack(fill="x", padx=22, pady=(14, 10))

        # ========================================================
        # ACTION CARD
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
            text="Product Tools",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left", padx=14, pady=12)

        tk.Label(
            action_card,
            text="Select a product first before editing or changing availability.",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=10)

        gold_btn(
            action_card,
            "➕ Add Product",
            self._add_dlg,
            height=34,
            width=140
        ).pack(side="right", padx=(4, 12), pady=10)

        primary_btn(
            action_card,
            "✏️ Edit",
            self._edit_dlg,
            height=34,
            width=100
        ).pack(side="right", padx=4, pady=10)

        success_btn(
            action_card,
            "✅ Mark Available",
            self._mark_available,
            height=34,
            width=150
        ).pack(side="right", padx=4, pady=10)

        danger_btn(
            action_card,
            "🚫 Mark Unavailable",
            self._mark_unavailable,
            height=34,
            width=165
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

        search_box = tk.Frame(filter_card, bg=CARD_BG)
        search_box.pack(side="left", padx=(8, 12), pady=10)

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
            placeholder_text="Search name, category, unit, status...",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=("Segoe UI", 10),
            corner_radius=8
        )
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", lambda event: self._apply_filter_sort_load())
        self.search_entry.bind("<Return>", lambda event: self._apply_filter_sort_load())

        tk.Label(
            filter_card,
            text="Status:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(4, 4))

        self.filter_cb = ttk.Combobox(
            filter_card,
            textvariable=self.filter_var,
            values=["All", "Available", "Low Stock", "Out of Stock", "Unavailable"],
            width=14,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.filter_cb.pack(side="left", padx=(0, 10))
        self.filter_cb.bind("<<ComboboxSelected>>", lambda event: self._apply_filter_sort_load())

        tk.Label(
            filter_card,
            text="Category:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(4, 4))

        self.category_cb = ttk.Combobox(
            filter_card,
            textvariable=self.category_var,
            values=["All Categories"] + CHICKEN_CATEGORIES,
            width=18,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.category_cb.pack(side="left", padx=(0, 10))
        self.category_cb.bind("<<ComboboxSelected>>", lambda event: self._apply_filter_sort_load())

        self.sort_btn = gold_btn(
            filter_card,
            "🔤 A → Z",
            self._toggle_sort,
            height=34,
            width=105
        )
        self.sort_btn.pack(side="right", padx=(4, 12), pady=10)

        gold_btn(
            filter_card,
            "Clear",
            self._show_all,
            height=34,
            width=80
        ).pack(side="right", padx=4, pady=10)

        # ========================================================
        # INSIGHT AREA
        # This is intentionally taller so Selected Product can scroll.
        # ========================================================
        insight_area = tk.Frame(self.main, bg=BG, height=305)
        insight_area.pack(fill="x", padx=22, pady=(0, 10))
        insight_area.pack_propagate(False)

        self.info_panel = tk.Frame(
            insight_area,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.info_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.selected_panel = tk.Frame(
            insight_area,
            bg="#FFF8E1",
            highlightbackground=GOLD,
            highlightthickness=1,
            width=400
        )
        self.selected_panel.pack(side="right", fill="both", padx=(0, 8))
        self.selected_panel.pack_propagate(False)

        self.alert_panel = tk.Frame(
            insight_area,
            bg="#FFF8E1",
            highlightbackground=GOLD,
            highlightthickness=1,
            width=400
        )
        self.alert_panel.pack(side="right", fill="both")
        self.alert_panel.pack_propagate(False)

        # ========================================================
        # TABLE TITLE
        # ========================================================
        table_title = tk.Frame(self.main, bg=BG)
        table_title.pack(fill="x", padx=22)

        tk.Label(
            table_title,
            text="Product Records",
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
            "AdminProducts.Treeview",
            background=CARD_BG,
            fieldbackground=CARD_BG,
            foreground=TEXT,
            rowheight=38,
            font=("Segoe UI", 11)
        )

        style.configure(
            "AdminProducts.Treeview.Heading",
            background=SIDEBAR,
            foreground=WHITE,
            font=("Segoe UI", 11, "bold"),
            relief="flat"
        )

        style.map(
            "AdminProducts.Treeview",
            background=[("selected", GOLD)],
            foreground=[("selected", DARK_RED)]
        )

        cols = (
            "ID",
            "Name",
            "Category",
            "Price",
            "Unit",
            "Quantity",
            "Stock Value",
            "Status"
        )

        widths = [55, 270, 170, 110, 80, 95, 140, 135]

        self.tree = ttk.Treeview(
            tbl,
            columns=cols,
            show="headings",
            style="AdminProducts.Treeview"
        )

        for col_name, width in zip(cols, widths):
            self.tree.heading(col_name, text=col_name)
            self.tree.column(col_name, width=width, anchor="center", minwidth=50)

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
        self.tree.tag_configure("low", background="#FDECEA", foreground="#B03A2E")
        self.tree.tag_configure("out", background="#FADBD8", foreground="#922B21")
        self.tree.tag_configure("inactive", background="#F2F3F4", foreground="#7B7D7D")

        self.tree.bind("<Double-1>", lambda event: self._edit_dlg())
        self.tree.bind("<<TreeviewSelect>>", self._on_product_select)

        self._load()

    # ============================================================
    # KPI
    # ============================================================
    def _make_kpi_card(self, index, label, value, color, subtext=""):
        card = tk.Frame(self.kpi, bg=color)
        card.grid(row=0, column=index, sticky="ew", padx=5)

        self.kpi.columnconfigure(index, weight=1)

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

    def _load_kpi_cards(self, rows):
        for widget in self.kpi.winfo_children():
            widget.destroy()

        total_products = len(rows)

        available_products = sum(
            1 for p in rows
            if str(p.get("status", "active")).lower() == "active"
        )

        low_stock_count = sum(
            1 for p in rows
            if str(p.get("status", "active")).lower() == "active"
            and 0 < safe_int(p.get("quantity")) < 10
        )

        out_stock_count = sum(
            1 for p in rows
            if str(p.get("status", "active")).lower() == "active"
            and safe_int(p.get("quantity")) <= 0
        )

        stock_value = sum(
            safe_float(p.get("price")) * safe_int(p.get("quantity"))
            for p in rows
            if str(p.get("status", "active")).lower() == "active"
        )

        stats = [
            ("📦 Products", str(total_products), SIDEBAR, "Displayed records"),
            ("✅ Available", str(available_products), "#27AE60", "Active items"),
            ("⚠️ Low Stock", str(low_stock_count), GOLD, "Below 10 qty"),
            ("❌ Out Stock", str(out_stock_count), "#B03A2E", "Needs restock"),
            ("💰 Stock Value", format_money(stock_value), "#6C3483", "Active only"),
        ]

        for index, (label, value, color, subtext) in enumerate(stats):
            self._make_kpi_card(index, label, value, color, subtext)

    # ============================================================
    # LOAD / FILTER
    # ============================================================
    def _load(self):
        try:
            self.products = get_inventory_products()

            self._build_info_panel()
            self._build_alert_panel()
            self._build_selected_panel(None)
            self._apply_filter_sort_load()

        except Exception as e:
            messagebox.showerror(
                "Database Error",
                f"Unable to load products from database.\n\n{e}",
                parent=self
            )

    def _show_all(self):
        self.search_var.set("")
        self.filter_var.set("All")
        self.category_var.set("All Categories")
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
        keyword = self.search_var.get().strip()
        selected_filter = self.filter_var.get()
        selected_category = self.category_var.get()

        rows = [
            product for product in self.products
            if self._product_matches_search(product, keyword)
        ]

        if selected_category != "All Categories":
            rows = [
                p for p in rows
                if str(p.get("category") or "General Chicken") == selected_category
            ]

        if selected_filter == "Available":
            rows = [
                p for p in rows
                if str(p.get("status", "active")).lower() == "active"
                and safe_int(p.get("quantity")) > 0
            ]

        elif selected_filter == "Low Stock":
            rows = [
                p for p in rows
                if str(p.get("status", "active")).lower() == "active"
                and 0 < safe_int(p.get("quantity")) < 10
            ]

        elif selected_filter == "Out of Stock":
            rows = [
                p for p in rows
                if str(p.get("status", "active")).lower() == "active"
                and safe_int(p.get("quantity")) <= 0
            ]

        elif selected_filter == "Unavailable":
            rows = [
                p for p in rows
                if str(p.get("status", "active")).lower() == "inactive"
            ]

        rows = sorted(
            rows,
            key=lambda p: str(p.get("product_name", "")).lower(),
            reverse=not self.sort_asc
        )

        self.filtered_products = rows

        self._load_kpi_cards(rows)
        self._load_products_table(rows)
        self.result_lbl.configure(text=f"{len(rows)} product(s) shown")

    def _toggle_sort(self):
        self.sort_asc = not self.sort_asc
        self.sort_btn.configure(text="🔤 A → Z" if self.sort_asc else "🔤 Z → A")
        self._apply_filter_sort_load()

    # ============================================================
    # PANELS
    # ============================================================
    def _build_info_panel(self):
        for widget in self.info_panel.winfo_children():
            widget.destroy()

        tk.Label(
            self.info_panel,
            text="Admin Product Tools",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(10, 4))

        tk.Label(
            self.info_panel,
            text=(
                "Use this page to manage all products. You can add new products, edit product details, "
                "mark products as unavailable, restore unavailable products, and monitor stock levels."
            ),
            font=("Segoe UI", 10),
            bg=CARD_BG,
            fg=TEXT,
            wraplength=650,
            justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 8))

        legend = tk.Frame(self.info_panel, bg=CARD_BG)
        legend.pack(anchor="w", padx=14, pady=(0, 10))

        legends = [
            ("Available", "#27AE60"),
            ("Low Stock", "#D68910"),
            ("Out of Stock", "#B03A2E"),
            ("Unavailable", "#7B7D7D"),
        ]

        for text, color in legends:
            tk.Label(
                legend,
                text=f"● {text}",
                font=("Segoe UI", 9, "bold"),
                bg=CARD_BG,
                fg=color
            ).pack(side="left", padx=(0, 16))

    def _build_selected_panel(self, product):
        for widget in self.selected_panel.winfo_children():
            widget.destroy()

        header = tk.Frame(self.selected_panel, bg="#FFF8E1")
        header.pack(fill="x")

        tk.Label(
            header,
            text="📌 Selected Product",
            font=("Segoe UI", 13, "bold"),
            bg="#FFF8E1",
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(10, 2))

        tk.Label(
            header,
            text="This area is scrollable. Use the scrollbar to view all details.",
            font=("Segoe UI", 8, "italic"),
            bg="#FFF8E1",
            fg=TEXT
        ).pack(anchor="w", padx=14, pady=(0, 6))

        # REAL SCROLLABLE SELECTED PRODUCT CONTENT
        content = self._make_scrollable_area(self.selected_panel, "#FFF8E1")

        if not product:
            tk.Label(
                content,
                text="Select a product from the table to preview its full details here.",
                font=("Segoe UI", 10),
                bg="#FFF8E1",
                fg=TEXT,
                wraplength=350,
                justify="left"
            ).pack(anchor="w", padx=8, pady=(8, 12))
            return

        name = product.get("product_name", "Unnamed Product")
        category = product.get("category") or "General Chicken"
        price = safe_float(product.get("price"))
        unit = product.get("unit", "—")
        qty = safe_int(product.get("quantity"))
        status = str(product.get("status", "active")).lower()

        if status == "inactive":
            display_status = "Unavailable"
        elif qty <= 0:
            display_status = "Out of Stock"
        elif qty < 10:
            display_status = "Low Stock"
        else:
            display_status = "Available"

        stock_value = price * qty if status == "active" else 0

        detail_rows = [
            ("Product ID", product.get("product_id", "—")),
            ("Product Name", name),
            ("Category", category),
            ("Price", format_money(price)),
            ("Unit", unit),
            ("Quantity", str(qty)),
            ("Stock Value", format_money(stock_value)),
            ("Status", display_status),
            ("Action Hint", "Double-click the product row to edit this product."),
            ("Availability Hint", "Use Mark Available or Mark Unavailable after selecting a product."),
        ]

        for title, value in detail_rows:
            box = tk.Frame(
                content,
                bg="#FFFDF2",
                highlightbackground="#E6C76E",
                highlightthickness=1
            )
            box.pack(fill="x", padx=6, pady=4)

            tk.Label(
                box,
                text=title,
                font=("Segoe UI", 8, "bold"),
                bg="#FFFDF2",
                fg=DARK_RED
            ).pack(anchor="w", padx=8, pady=(5, 0))

            tk.Label(
                box,
                text=value,
                font=("Segoe UI", 9),
                bg="#FFFDF2",
                fg=TEXT,
                wraplength=340,
                justify="left"
            ).pack(anchor="w", padx=8, pady=(0, 5))

    def _build_alert_panel(self):
        for widget in self.alert_panel.winfo_children():
            widget.destroy()

        header = tk.Frame(self.alert_panel, bg="#FFF8E1")
        header.pack(fill="x")

        tk.Label(
            header,
            text="⚠️ Stock Watch",
            font=("Segoe UI", 13, "bold"),
            bg="#FFF8E1",
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(10, 2))

        tk.Label(
            header,
            text="Low-stock and out-of-stock products.",
            font=("Segoe UI", 8, "italic"),
            bg="#FFF8E1",
            fg=TEXT
        ).pack(anchor="w", padx=14, pady=(0, 6))

        content = self._make_scrollable_area(self.alert_panel, "#FFF8E1")

        low_items = [
            p for p in self.products
            if str(p.get("status", "active")).lower() == "active"
            and safe_int(p.get("quantity")) < 10
        ]

        if not low_items:
            tk.Label(
                content,
                text="No low-stock available products right now.",
                font=("Segoe UI", 10),
                bg="#FFF8E1",
                fg="#1E8449",
                wraplength=350,
                justify="left"
            ).pack(anchor="w", padx=8, pady=(8, 12))
            return

        for item in low_items:
            name = short_text(item.get("product_name", "Unnamed"), 30)
            qty = safe_int(item.get("quantity"))
            unit = item.get("unit", "")
            category = item.get("category") or "General Chicken"
            label = "OUT OF STOCK" if qty <= 0 else "LOW STOCK"

            box = tk.Frame(
                content,
                bg="#FFFDF2",
                highlightbackground="#E6C76E",
                highlightthickness=1
            )
            box.pack(fill="x", padx=6, pady=4)

            tk.Label(
                box,
                text=f"{label}: {name}",
                font=("Segoe UI", 9, "bold"),
                bg="#FFFDF2",
                fg="#B03A2E",
                anchor="w"
            ).pack(fill="x", padx=8, pady=(6, 0))

            tk.Label(
                box,
                text=f"Category: {category}",
                font=("Segoe UI", 8),
                bg="#FFFDF2",
                fg=TEXT,
                anchor="w"
            ).pack(fill="x", padx=8, pady=(1, 0))

            tk.Label(
                box,
                text=f"Current stock: {qty} {unit}",
                font=("Segoe UI", 8, "bold"),
                bg="#FFFDF2",
                fg=TEXT,
                anchor="w"
            ).pack(fill="x", padx=8, pady=(1, 6))

    # ============================================================
    # TABLE
    # ============================================================
    def _load_products_table(self, rows):
        self.tree.delete(*self.tree.get_children())

        if not rows:
            self.tree.insert(
                "",
                "end",
                values=("—", "No products found", "—", "₱0.00", "—", "0", "₱0.00", "—"),
                tags=("even",)
            )
            return

        for index, product in enumerate(rows):
            product_id = product.get("product_id")
            product_name = product.get("product_name")
            category = product.get("category") or "General Chicken"
            price = safe_float(product.get("price"))
            unit = product.get("unit", "—")
            quantity = safe_int(product.get("quantity"))
            status = str(product.get("status", "active")).lower()

            if status == "inactive":
                status_text = "Unavailable"
                stock_value = 0
                tag = "inactive"
            else:
                stock_value = price * quantity

                if quantity <= 0:
                    status_text = "Out of Stock"
                    tag = "out"
                elif quantity < 10:
                    status_text = "Low Stock"
                    tag = "low"
                else:
                    status_text = "Available"
                    tag = "odd" if index % 2 else "even"

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
                    format_money(stock_value),
                    status_text
                ),
                tags=(tag,)
            )

    def _on_product_select(self, event=None):
        product_id, _, _ = self._get_selected_product()

        if not product_id:
            self.selected_product_id = None
            self._build_selected_panel(None)
            return

        self.selected_product_id = product_id

        product = get_product_by_id(product_id)

        if product:
            self._build_selected_panel(product)

    def _get_selected_product(self):
        selected_row = self.tree.focus()

        if not selected_row:
            return None, None, None

        values = self.tree.item(selected_row, "values")

        if not values or values[0] == "—":
            return None, None, None

        return int(values[0]), values[1], values[7]

    # ============================================================
    # STATUS ACTIONS
    # ============================================================
    def _set_product_status(self, new_status, action_text):
        product_id, product_name, display_status = self._get_selected_product()

        if not product_id:
            messagebox.showwarning("Status", "Select a product first.", parent=self)
            return

        if new_status == "active" and display_status != "Unavailable":
            messagebox.showinfo(
                "Status",
                f"'{product_name}' is already available.",
                parent=self
            )
            return

        if new_status == "inactive" and display_status == "Unavailable":
            messagebox.showinfo(
                "Status",
                f"'{product_name}' is already unavailable.",
                parent=self
            )
            return

        confirm = messagebox.askyesno(
            "Change Product Status",
            f"Mark '{product_name}' as {action_text}?",
            parent=self
        )

        if not confirm:
            return

        try:
            success = set_product_status(product_id, new_status, self.admin_id)

            if success:
                messagebox.showinfo(
                    "Status Updated",
                    f"'{product_name}' is now {action_text}.",
                    parent=self
                )
                self._load()
            else:
                messagebox.showerror(
                    "Status Failed",
                    "Unable to update product status.",
                    parent=self
                )

        except Exception as e:
            messagebox.showerror(
                "Status Error",
                f"Unable to update product status.\n\n{e}",
                parent=self
            )

    def _mark_available(self):
        self._set_product_status("active", "available")

    def _mark_unavailable(self):
        self._set_product_status("inactive", "unavailable")

    # ============================================================
    # PRODUCT FORM
    # ============================================================
    def _product_form(self, title, defaults=None):
        result = {}

        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("520x640")
        win.resizable(False, False)
        win.grab_set()
        win.configure(fg_color=BG)

        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (520 // 2)
        y = (win.winfo_screenheight() // 2) - (640 // 2)
        win.geometry(f"520x640+{x}+{y}")

        banner = tk.Frame(win, bg=SIDEBAR, height=60)
        banner.pack(fill="x")
        banner.pack_propagate(False)

        tk.Label(
            banner,
            text=f"{'➕' if 'Add' in title else '✏️'} {title}",
            font=("Georgia", 16, "bold"),
            bg=SIDEBAR,
            fg=CREAM
        ).pack(side="left", padx=18, pady=12)

        tk.Label(
            win,
            text="Fill out all product information carefully before saving.",
            font=("Segoe UI", 10, "italic"),
            bg=BG,
            fg=TEXT
        ).pack(anchor="w", padx=28, pady=(14, 0))

        form = tk.Frame(
            win,
            bg=CREAM,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        form.pack(padx=24, pady=14, fill="x")

        default_name = defaults.get("product_name", "") if defaults else ""
        default_category = defaults.get("category", "General Chicken") if defaults else "General Chicken"

        if not default_category or str(default_category).strip() == "":
            default_category = "General Chicken"

        if default_category not in CHICKEN_CATEGORIES:
            category_values = CHICKEN_CATEGORIES + [default_category]
        else:
            category_values = CHICKEN_CATEGORIES

        default_price = defaults.get("price", "") if defaults else ""
        default_unit = defaults.get("unit", "") if defaults else ""
        default_quantity = defaults.get("quantity", "") if defaults else ""

        entries = {}

        tk.Label(
            form,
            text="Product Name",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED,
            anchor="w"
        ).pack(fill="x", padx=18, pady=(12, 2))

        name_entry = ctk.CTkEntry(
            form,
            height=38,
            placeholder_text="e.g. Chicken Breast / Chicken Wings / Chicken Liver",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=F_BODY,
            corner_radius=8
        )

        if default_name != "":
            name_entry.insert(0, str(default_name))

        name_entry.pack(fill="x", padx=18, pady=(0, 2))
        entries["product_name"] = name_entry

        tk.Label(
            form,
            text="Category",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED,
            anchor="w"
        ).pack(fill="x", padx=18, pady=(12, 2))

        category_var = tk.StringVar(master=win, value=default_category)

        category_cb = ttk.Combobox(
            form,
            textvariable=category_var,
            values=category_values,
            state="readonly",
            font=("Segoe UI", 11)
        )
        category_cb.pack(fill="x", padx=18, pady=(0, 2), ipady=6)

        tk.Label(
            form,
            text="Example: Chicken Breast = Breast Cuts, Chicken Wings = Wing Cuts, Chicken Liver = Organ / Offal.",
            font=("Segoe UI", 9),
            bg=CREAM,
            fg=TEXT,
            anchor="w",
            wraplength=440,
            justify="left"
        ).pack(fill="x", padx=18, pady=(2, 0))

        tk.Label(
            form,
            text="Price (₱)",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED,
            anchor="w"
        ).pack(fill="x", padx=18, pady=(12, 2))

        price_entry = ctk.CTkEntry(
            form,
            height=38,
            placeholder_text="e.g. 180.00",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=F_BODY,
            corner_radius=8
        )

        if default_price != "":
            price_entry.insert(0, str(default_price))

        price_entry.pack(fill="x", padx=18, pady=(0, 2))
        entries["price"] = price_entry

        tk.Label(
            form,
            text="Unit",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED,
            anchor="w"
        ).pack(fill="x", padx=18, pady=(12, 2))

        unit_entry = ctk.CTkEntry(
            form,
            height=38,
            placeholder_text="e.g. kg / pc / tray",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=F_BODY,
            corner_radius=8
        )

        if default_unit != "":
            unit_entry.insert(0, str(default_unit))

        unit_entry.pack(fill="x", padx=18, pady=(0, 2))
        entries["unit"] = unit_entry

        tk.Label(
            form,
            text="Quantity",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED,
            anchor="w"
        ).pack(fill="x", padx=18, pady=(12, 2))

        quantity_entry = ctk.CTkEntry(
            form,
            height=38,
            placeholder_text="e.g. 50",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=F_BODY,
            corner_radius=8
        )

        if default_quantity != "":
            quantity_entry.insert(0, str(default_quantity))

        quantity_entry.pack(fill="x", padx=18, pady=(0, 2))
        entries["quantity"] = quantity_entry

        tk.Frame(form, bg=CREAM, height=8).pack()

        def save_form():
            try:
                product_name = entries["product_name"].get().strip()
                category = category_var.get().strip() or "General Chicken"
                price = float(entries["price"].get())
                unit = entries["unit"].get().strip()
                quantity = int(entries["quantity"].get())

                if not product_name or not unit:
                    raise ValueError

                if price < 0 or quantity < 0:
                    raise ValueError

            except Exception:
                messagebox.showwarning(
                    "Input",
                    "Please fill all fields correctly.\n\n"
                    "Product name and unit are required.\n"
                    "Price must be a number.\n"
                    "Quantity must be a whole number.\n"
                    "Price and quantity cannot be negative.",
                    parent=win
                )
                return

            result.update(
                {
                    "product_name": product_name,
                    "category": category,
                    "price": price,
                    "unit": unit,
                    "quantity": quantity
                }
            )

            win.destroy()

        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack(fill="x", padx=24, pady=(0, 16))

        gold_btn(
            btn_row,
            "💾 Save Product",
            save_form,
            height=42
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        danger_btn(
            btn_row,
            "✖ Cancel",
            win.destroy,
            height=42
        ).pack(side="left", fill="x", expand=True)

        name_entry.focus_set()
        win.wait_window()

        return result if result else None

    # ============================================================
    # ADD / EDIT
    # ============================================================
    def _add_dlg(self):
        data = self._product_form("Add Product")

        if not data:
            return

        try:
            try:
                product_id = add_product(
                    data["product_name"],
                    data["price"],
                    data["unit"],
                    data["quantity"],
                    self.admin_id,
                    data["category"]
                )
            except TypeError:
                product_id = add_product(
                    data["product_name"],
                    data["price"],
                    data["unit"],
                    data["quantity"],
                    self.admin_id
                )

            if product_id:
                messagebox.showinfo(
                    "Added",
                    f"'{data['product_name']}' added successfully.",
                    parent=self
                )
                self._load()
            else:
                messagebox.showerror(
                    "Add Failed",
                    "Unable to add product.",
                    parent=self
                )

        except Exception as e:
            messagebox.showerror(
                "Add Error",
                f"Unable to add product.\n\n{e}",
                parent=self
            )

    def _edit_dlg(self):
        selected_row = self.tree.focus()

        if not selected_row:
            messagebox.showwarning(
                "Edit",
                "Select a product to edit.",
                parent=self
            )
            return

        values = self.tree.item(selected_row, "values")

        if not values or values[0] == "—":
            return

        product_id = int(values[0])
        product = get_product_by_id(product_id)

        if not product:
            messagebox.showerror(
                "Edit",
                "Selected product was not found in database.",
                parent=self
            )
            return

        data = self._product_form("Edit Product", product)

        if not data:
            return

        try:
            try:
                success = update_product(
                    product_id,
                    data["product_name"],
                    data["price"],
                    data["unit"],
                    data["quantity"],
                    self.admin_id,
                    data["category"]
                )
            except TypeError:
                success = update_product(
                    product_id,
                    data["product_name"],
                    data["price"],
                    data["unit"],
                    data["quantity"],
                    self.admin_id
                )

            if success:
                messagebox.showinfo(
                    "Updated",
                    "Product updated successfully.",
                    parent=self
                )
                self._load()
            else:
                messagebox.showerror(
                    "Update Failed",
                    "Unable to update product.",
                    parent=self
                )

        except Exception as e:
            messagebox.showerror(
                "Update Error",
                f"Unable to update product.\n\n{e}",
                parent=self
            )


if __name__ == "__main__":
    AdminProductsTotal("Admin").mainloop()