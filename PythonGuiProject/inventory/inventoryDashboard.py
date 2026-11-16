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

LOW_STOCK_LIMIT = 10


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


class InventoryDashboard(ctk.CTk):
    def __init__(self, user_name="Inventory", inventory_id=None):
        super().__init__()

        self.user_name = user_name
        self.inventory_id = inventory_id

        self.products = []
        self.filtered_products = []
        self.sort_asc = True

        self.filter_var = tk.StringVar(master=self, value="All")
        self.srch_var = tk.StringVar(master=self)

        self.title("Inventory Dashboard")
        self.configure(fg_color=BG)
        self.attributes("-fullscreen", True)

        self._build()

    # =========================
    # NAVIGATION
    # =========================
    def _go_total(self):
        try:
            self.configure(cursor="watch")
            self.update_idletasks()

            from inventory.productsTotal import ProductsTotal
            app = ProductsTotal(self.user_name)

            self.destroy()
            app.mainloop()

        except Exception as e:
            self.configure(cursor="")
            messagebox.showerror(
                "Navigation Error",
                f"Unable to open Products Total.\n\n{e}",
                parent=self
            )

    # =========================
    # UI BUILD
    # =========================
    def _build(self):
        nav = [
            ("inventory", "📦", "Inventory", lambda: None),
            ("total", "📊", "Products Total", self._go_total),
        ]

        make_sidebar(self, self.user_name, "Inventory Staff", nav, "inventory")

        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="right", fill="both", expand=True)

        self._build_header()
        self._build_kpi_container()
        self._build_middle_panels()
        self._build_action_bar()
        self._build_table()

        self._refresh_products()

    def _build_header(self):
        header = tk.Frame(self.main, bg=CREAM, height=82)
        header.pack(fill="x")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=CREAM)
        left.pack(side="left", padx=26, pady=12)

        tk.Label(
            left,
            text="📦 Inventory Dashboard",
            font=("Georgia", 22, "bold"),
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Manage products, stock levels, availability, and chicken categories.",
            font=("Segoe UI", 10),
            bg=CREAM,
            fg=TEXT
        ).pack(anchor="w", pady=(2, 0))

        right = tk.Frame(header, bg=CREAM)
        right.pack(side="right", padx=22, pady=16)

        tk.Label(
            right,
            text=f"Welcome, {self.user_name}",
            font=("Segoe UI", 11, "bold"),
            bg=CREAM,
            fg=DARK_RED
        ).pack(side="left", padx=(0, 12))

        gold_btn(
            right,
            "➕ Add Product",
            self._add_dlg,
            height=38
        ).pack(side="left", padx=4)

        primary_btn(
            right,
            "🔄 Refresh",
            self._refresh_products,
            height=38
        ).pack(side="left", padx=4)

    def _build_kpi_container(self):
        self.kpi_frame = tk.Frame(self.main, bg=BG)
        self.kpi_frame.pack(fill="x", padx=24, pady=(18, 10))

    def _build_middle_panels(self):
        wrapper = tk.Frame(self.main, bg=BG)
        wrapper.pack(fill="x", padx=24, pady=(0, 12))

        self.quick_panel = tk.Frame(
            wrapper,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            height=230
        )
        self.quick_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.quick_panel.pack_propagate(False)

        # Bigger stock alert panel
        self.alert_panel = tk.Frame(
            wrapper,
            bg="#FFF8E1",
            highlightbackground=GOLD,
            highlightthickness=1,
            width=520,
            height=230
        )
        self.alert_panel.pack(side="right", fill="both")
        self.alert_panel.pack_propagate(False)

    def _build_action_bar(self):
        self.action_card = tk.Frame(
            self.main,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.action_card.pack(fill="x", padx=24, pady=(0, 12))

        top_row = tk.Frame(self.action_card, bg=CARD_BG)
        top_row.pack(fill="x", padx=14, pady=(12, 8))

        tk.Label(
            top_row,
            text="Product List",
            font=("Segoe UI", 13, "bold"),
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left")

        tk.Label(
            top_row,
            text="Double-click a product to edit it.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=10)

        bottom_row = tk.Frame(self.action_card, bg=CARD_BG)
        bottom_row.pack(fill="x", padx=14, pady=(0, 12))

        search_box = tk.Frame(bottom_row, bg=CARD_BG)
        search_box.pack(side="left", fill="x", expand=True)

        tk.Label(
            search_box,
            text="🔍 Search",
            font=("Segoe UI", 10, "bold"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(0, 6))

        self.search_entry = ctk.CTkEntry(
            search_box,
            textvariable=self.srch_var,
            width=330,
            height=38,
            placeholder_text="Search name, category, unit, status...",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=F_BODY,
            corner_radius=10
        )
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda event: self._apply_filter_sort_load())
        self.search_entry.bind("<Return>", lambda event: self._apply_filter_sort_load())

        primary_btn(
            search_box,
            "Search",
            self._apply_filter_sort_load,
            height=38
        ).pack(side="left", padx=4)

        clear_btn = ctk.CTkButton(
            search_box,
            text="Clear",
            height=38,
            width=80,
            corner_radius=10,
            fg_color="#EAECEE",
            hover_color="#D5DBDB",
            text_color=TEXT,
            font=("Segoe UI", 10, "bold"),
            command=self._clear_search
        )
        clear_btn.pack(side="left", padx=4)

        tk.Label(
            bottom_row,
            text="Filter:",
            font=("Segoe UI", 10, "bold"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(10, 4))

        self.filter_cb = ttk.Combobox(
            bottom_row,
            textvariable=self.filter_var,
            values=["All", "Available", "Low Stock", "Out of Stock", "Unavailable"],
            width=15,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.filter_cb.pack(side="left", padx=4, ipady=4)
        self.filter_cb.bind("<<ComboboxSelected>>", lambda event: self._apply_filter_sort_load())

        self.sort_btn = gold_btn(
            bottom_row,
            "🔤 A → Z",
            self._toggle_sort,
            height=38
        )
        self.sort_btn.pack(side="left", padx=4)

        danger_btn(
            bottom_row,
            "🚫 Unavailable",
            self._mark_unavailable,
            height=38
        ).pack(side="right", padx=4)

        success_btn(
            bottom_row,
            "✅ Available",
            self._mark_available,
            height=38
        ).pack(side="right", padx=4)

        primary_btn(
            bottom_row,
            "✏️ Edit Product",
            self._edit_dlg,
            height=38
        ).pack(side="right", padx=4)

    def _build_table(self):
        table_card = tk.Frame(
            self.main,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        table_card.pack(fill="both", expand=True, padx=24, pady=(0, 22))

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Inv.Treeview",
            background=CARD_BG,
            fieldbackground=CARD_BG,
            foreground=TEXT,
            rowheight=42,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Inv.Treeview.Heading",
            background=SIDEBAR,
            foreground=WHITE,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padding=8
        )

        style.map(
            "Inv.Treeview",
            background=[("selected", GOLD)],
            foreground=[("selected", DARK_RED)]
        )

        columns = (
            "ID",
            "Name",
            "Category",
            "Price",
            "Unit",
            "Quantity",
            "Status"
        )

        self.tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            style="Inv.Treeview"
        )

        column_settings = {
            "ID": 60,
            "Name": 280,
            "Category": 180,
            "Price": 125,
            "Unit": 90,
            "Quantity": 110,
            "Status": 150
        }

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(
                col,
                width=column_settings[col],
                anchor="center",
                minwidth=60
            )

        self.tree.column("Name", anchor="w")
        self.tree.column("Category", anchor="w")

        y_scroll = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview)

        self.tree.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )

        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        self.tree.tag_configure("even", background=CARD_BG, foreground=TEXT)
        self.tree.tag_configure("odd", background=ODD_ROW, foreground=TEXT)
        self.tree.tag_configure("low", background="#FFF3CD", foreground="#856404")
        self.tree.tag_configure("out", background="#F8D7DA", foreground="#842029")
        self.tree.tag_configure("inactive", background="#ECEFF1", foreground="#7B7D7D")

        self.tree.bind("<Double-1>", lambda event: self._edit_dlg())
        self.tree.bind("<<TreeviewSelect>>", lambda event: self._update_selected_hint())

        self.selected_hint = tk.Label(
            table_card,
            text="Select a product to edit or change availability.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT
        )
        self.selected_hint.pack(anchor="w", padx=10, pady=(0, 8))

    # =========================
    # KPI / PANELS
    # =========================
    def _build_kpis(self):
        for widget in self.kpi_frame.winfo_children():
            widget.destroy()

        total_products = len(self.products)

        available_products = sum(
            1 for p in self.products
            if str(p.get("status", "active")).lower() == "active"
        )

        unavailable_products = sum(
            1 for p in self.products
            if str(p.get("status", "active")).lower() == "inactive"
        )

        low_stock = sum(
            1 for p in self.products
            if 0 < safe_int(p.get("quantity")) < LOW_STOCK_LIMIT
            and str(p.get("status", "active")).lower() == "active"
        )

        out_of_stock = sum(
            1 for p in self.products
            if safe_int(p.get("quantity")) <= 0
            and str(p.get("status", "active")).lower() == "active"
        )

        total_stock = sum(
            safe_int(p.get("quantity"))
            for p in self.products
            if str(p.get("status", "active")).lower() == "active"
        )

        stats = [
            ("📦 Total Products", total_products, SIDEBAR, "All products"),
            ("✅ Available", available_products, "#27AE60", "Active products"),
            ("🚫 Unavailable", unavailable_products, "#B03A2E", "Inactive products"),
            ("⚠️ Low Stock", low_stock, GOLD, f"Below {LOW_STOCK_LIMIT} stocks"),
            ("⛔ Out of Stock", out_of_stock, "#C0392B", "Needs restocking"),
            ("📊 Total Stocks", total_stock, "#7D3C98", "Active stock count"),
        ]

        for index, (label, value, color, subtitle) in enumerate(stats):
            card = tk.Frame(
                self.kpi_frame,
                bg=color,
                highlightbackground=color,
                highlightthickness=1
            )
            card.grid(row=0, column=index, sticky="ew", padx=5)
            self.kpi_frame.columnconfigure(index, weight=1)

            tk.Label(
                card,
                text=label,
                font=("Segoe UI", 9, "bold"),
                bg=color,
                fg=CREAM
            ).pack(anchor="w", padx=12, pady=(10, 0))

            tk.Label(
                card,
                text=str(value),
                font=("Georgia", 20, "bold"),
                bg=color,
                fg=WHITE
            ).pack(anchor="w", padx=12, pady=(0, 0))

            tk.Label(
                card,
                text=subtitle,
                font=("Segoe UI", 8),
                bg=color,
                fg=CREAM
            ).pack(anchor="w", padx=12, pady=(0, 10))

    def _build_quick_panel(self):
        for widget in self.quick_panel.winfo_children():
            widget.destroy()

        tk.Label(
            self.quick_panel,
            text="Inventory Guide",
            font=("Segoe UI", 14, "bold"),
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(anchor="w", padx=18, pady=(14, 4))

        guide = (
            "Use Product Name for the exact item and Category for the general chicken group.\n"
            "Example: Product Name = Chicken Breast, Category = Breast Cuts.\n\n"
            "Unavailable products remain visible here so inventory staff can still monitor and reactivate them anytime."
        )

        tk.Label(
            self.quick_panel,
            text=guide,
            font=("Segoe UI", 10),
            bg=CARD_BG,
            fg=TEXT,
            justify="left",
            wraplength=760
        ).pack(anchor="w", padx=18, pady=(0, 10))

        legend = tk.Frame(self.quick_panel, bg=CARD_BG)
        legend.pack(anchor="w", padx=18, pady=(0, 12))

        self._legend_item(legend, "#FFF3CD", "Low Stock")
        self._legend_item(legend, "#F8D7DA", "Out of Stock")
        self._legend_item(legend, "#ECEFF1", "Unavailable")

    def _legend_item(self, parent, color, text):
        item = tk.Frame(parent, bg=CARD_BG)
        item.pack(side="left", padx=(0, 14))

        tk.Label(
            item,
            text="   ",
            bg=color,
            width=3,
            height=1
        ).pack(side="left")

        tk.Label(
            item,
            text=f" {text}",
            font=("Segoe UI", 9, "bold"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

    def _build_alert_panel(self):
        for widget in self.alert_panel.winfo_children():
            widget.destroy()

        header = tk.Frame(self.alert_panel, bg="#FFF8E1")
        header.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(
            header,
            text="⚠️ Stock Alerts",
            font=("Segoe UI", 15, "bold"),
            bg="#FFF8E1",
            fg=DARK_RED
        ).pack(side="left")

        alert_items = [
            p for p in self.products
            if safe_int(p.get("quantity")) < LOW_STOCK_LIMIT
            and str(p.get("status", "active")).lower() == "active"
        ]

        alert_items = sorted(
            alert_items,
            key=lambda p: safe_int(p.get("quantity"))
        )

        tk.Label(
            header,
            text=f"{len(alert_items)} item(s)",
            font=("Segoe UI", 10, "bold"),
            bg="#FFF8E1",
            fg=TEXT
        ).pack(side="right")

        if not alert_items:
            empty_box = tk.Frame(
                self.alert_panel,
                bg="#EAF7EA",
                highlightbackground="#A9DFBF",
                highlightthickness=1
            )
            empty_box.pack(fill="both", expand=True, padx=16, pady=(8, 16))

            tk.Label(
                empty_box,
                text="✅ No low-stock products right now.",
                font=("Segoe UI", 12, "bold"),
                bg="#EAF7EA",
                fg="#1E8449"
            ).pack(anchor="center", pady=(34, 4))

            tk.Label(
                empty_box,
                text="Your available inventory stocks are currently in good condition.",
                font=("Segoe UI", 10),
                bg="#EAF7EA",
                fg=TEXT,
                wraplength=450,
                justify="center"
            ).pack(anchor="center")

            return

        canvas = tk.Canvas(
            self.alert_panel,
            bg="#FFF8E1",
            highlightthickness=0
        )
        canvas.pack(side="left", fill="both", expand=True, padx=(16, 0), pady=(0, 16))

        scrollbar = ttk.Scrollbar(
            self.alert_panel,
            orient="vertical",
            command=canvas.yview
        )
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=(0, 16))

        scroll_frame = tk.Frame(canvas, bg="#FFF8E1")

        canvas_window = canvas.create_window(
            (0, 0),
            window=scroll_frame,
            anchor="nw"
        )

        canvas.configure(yscrollcommand=scrollbar.set)

        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_scroll_frame(event):
            canvas.itemconfig(canvas_window, width=event.width)

        scroll_frame.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", resize_scroll_frame)

        for item in alert_items:
            name = item.get("product_name", "Unnamed Product")
            qty = safe_int(item.get("quantity"))
            unit = item.get("unit", "")
            category = item.get("category") or "General Chicken"

            if qty <= 0:
                status_text = "OUT OF STOCK"
                bg_color = "#F8D7DA"
                border_color = "#E74C3C"
                fg_color = "#842029"
                icon = "⛔"
                action_text = "Restock immediately"
            else:
                status_text = "LOW STOCK"
                bg_color = "#FFF3CD"
                border_color = "#F1C40F"
                fg_color = "#856404"
                icon = "⚠️"
                action_text = "Needs restocking soon"

            row = tk.Frame(
                scroll_frame,
                bg=bg_color,
                highlightbackground=border_color,
                highlightthickness=1
            )
            row.pack(fill="x", pady=5)

            top = tk.Frame(row, bg=bg_color)
            top.pack(fill="x", padx=12, pady=(8, 2))

            tk.Label(
                top,
                text=f"{icon} {status_text}",
                font=("Segoe UI", 9, "bold"),
                bg=bg_color,
                fg=fg_color
            ).pack(side="left")

            tk.Label(
                top,
                text=f"{qty} {unit}",
                font=("Segoe UI", 12, "bold"),
                bg=bg_color,
                fg=fg_color
            ).pack(side="right")

            tk.Label(
                row,
                text=name,
                font=("Segoe UI", 12, "bold"),
                bg=bg_color,
                fg=TEXT,
                wraplength=440,
                justify="left"
            ).pack(anchor="w", padx=12, pady=(0, 2))

            tk.Label(
                row,
                text=f"Category: {category}",
                font=("Segoe UI", 9),
                bg=bg_color,
                fg=TEXT,
                wraplength=440,
                justify="left"
            ).pack(anchor="w", padx=12)

            tk.Label(
                row,
                text=action_text,
                font=("Segoe UI", 9, "italic"),
                bg=bg_color,
                fg=fg_color
            ).pack(anchor="w", padx=12, pady=(2, 8))

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda event: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda event: canvas.unbind_all("<MouseWheel>"))

    # =========================
    # DATA
    # =========================
    def _refresh_products(self):
        try:
            self.configure(cursor="watch")
            self.update_idletasks()

            self.products = get_inventory_products()

            self._build_kpis()
            self._build_quick_panel()
            self._build_alert_panel()
            self._apply_filter_sort_load()

        except Exception as e:
            messagebox.showerror(
                "Database Error",
                f"Unable to load products from database.\n\n{e}",
                parent=self
            )

        finally:
            self.configure(cursor="")

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
            product for product in self.products
            if self._product_matches_search(product, keyword)
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
                and 0 < safe_int(p.get("quantity")) < LOW_STOCK_LIMIT
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

        products = sorted(
            products,
            key=lambda p: str(p.get("product_name", "")).lower(),
            reverse=not self.sort_asc
        )

        self.filtered_products = products
        self._load_table(products)

    def _load_table(self, products):
        self.tree.delete(*self.tree.get_children())

        if not products:
            self.tree.insert(
                "",
                "end",
                values=("—", "No products found", "—", "₱0.00", "—", "0", "—"),
                tags=("even",)
            )
            self.selected_hint.configure(text="No product selected.")
            return

        for index, product in enumerate(products):
            product_id = product.get("product_id")
            product_name = product.get("product_name") or "Unnamed Product"
            category = product.get("category") or "General Chicken"
            price = safe_float(product.get("price"))
            unit = product.get("unit", "—")
            quantity = safe_int(product.get("quantity"))
            status = str(product.get("status", "active")).lower()

            if status == "inactive":
                tag = "inactive"
                status_text = "Unavailable"

            elif quantity <= 0:
                tag = "out"
                status_text = "Out of Stock"

            elif quantity < LOW_STOCK_LIMIT:
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

        self.selected_hint.configure(
            text=f"Showing {len(products)} product(s). Select a product to edit or change availability."
        )

    # =========================
    # UI ACTIONS
    # =========================
    def _clear_search(self):
        self.srch_var.set("")
        self.filter_var.set("All")
        self._apply_filter_sort_load()

    def _toggle_sort(self):
        self.sort_asc = not self.sort_asc
        self.sort_btn.configure(text="🔤 A → Z" if self.sort_asc else "🔤 Z → A")
        self._apply_filter_sort_load()

    def _update_selected_hint(self):
        product_id, product_name, display_status = self._get_selected_product()

        if not product_id:
            self.selected_hint.configure(text="Select a product to edit or change availability.")
            return

        self.selected_hint.configure(
            text=f"Selected: {product_name} | Status: {display_status}"
        )

    def _get_selected_product(self):
        selected_row = self.tree.focus()

        if not selected_row:
            return None, None, None

        values = self.tree.item(selected_row, "values")

        if not values or values[0] == "—":
            return None, None, None

        return int(values[0]), values[1], values[6]

    # =========================
    # STATUS UPDATE
    # =========================
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
            f"Are you sure you want to mark '{product_name}' as {action_text}?",
            parent=self
        )

        if not confirm:
            return

        try:
            success = set_product_status(product_id, new_status, self.inventory_id)

            if success:
                messagebox.showinfo(
                    "Status Updated",
                    f"'{product_name}' is now {action_text}.",
                    parent=self
                )
                self._refresh_products()
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

    # =========================
    # PRODUCT FORM
    # =========================
    def _product_form(self, title, defaults=None):
        result = {}

        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("520x650")
        win.resizable(False, False)
        win.grab_set()
        win.configure(fg_color=BG)

        win.update_idletasks()

        try:
            x = self.winfo_x() + (self.winfo_width() // 2) - 260
            y = self.winfo_y() + (self.winfo_height() // 2) - 325
            win.geometry(f"520x650+{x}+{y}")
        except Exception:
            pass

        banner = tk.Frame(win, bg=SIDEBAR, height=72)
        banner.pack(fill="x")
        banner.pack_propagate(False)

        icon = "➕" if "Add" in title else "✏️"

        tk.Label(
            banner,
            text=f"{icon} {title}",
            font=("Georgia", 18, "bold"),
            bg=SIDEBAR,
            fg=CREAM
        ).pack(anchor="w", padx=22, pady=(12, 0))

        tk.Label(
            banner,
            text="Fill out product details carefully before saving.",
            font=("Segoe UI", 9),
            bg=SIDEBAR,
            fg=CREAM
        ).pack(anchor="w", padx=22, pady=(2, 0))

        body = tk.Frame(win, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=18)

        form = tk.Frame(
            body,
            bg=CREAM,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        form.pack(fill="both", expand=True)

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

        self._form_label(form, "Product Name")
        name_entry = self._form_entry(
            form,
            "e.g. Chicken Breast / Chicken Wings / Chicken Liver"
        )

        if default_name != "":
            name_entry.insert(0, str(default_name))

        entries["product_name"] = name_entry

        self._form_label(form, "Category")
        category_var = tk.StringVar(master=win, value=default_category)

        category_cb = ttk.Combobox(
            form,
            textvariable=category_var,
            values=category_values,
            state="readonly",
            font=("Segoe UI", 11)
        )
        category_cb.pack(fill="x", padx=20, pady=(0, 4), ipady=7)

        tk.Label(
            form,
            text="Example: Chicken Breast = Breast Cuts, Chicken Wings = Wing Cuts, Chicken Liver = Organ / Offal.",
            font=("Segoe UI", 9),
            bg=CREAM,
            fg=TEXT,
            anchor="w",
            wraplength=440,
            justify="left"
        ).pack(fill="x", padx=20, pady=(0, 4))

        self._form_label(form, "Price (₱)")
        price_entry = self._form_entry(form, "e.g. 180.00")

        if default_price != "":
            price_entry.insert(0, str(default_price))

        entries["price"] = price_entry

        self._form_label(form, "Unit")
        unit_entry = self._form_entry(form, "e.g. kg / pc / tray")

        if default_unit != "":
            unit_entry.insert(0, str(default_unit))

        entries["unit"] = unit_entry

        self._form_label(form, "Quantity")
        quantity_entry = self._form_entry(form, "e.g. 50")

        if default_quantity != "":
            quantity_entry.insert(0, str(default_quantity))

        entries["quantity"] = quantity_entry

        tk.Frame(form, bg=CREAM, height=12).pack()

        def save_form():
            try:
                product_name = entries["product_name"].get().strip()
                category = category_var.get().strip() or "General Chicken"
                price_raw = entries["price"].get().strip()
                unit = entries["unit"].get().strip()
                quantity_raw = entries["quantity"].get().strip()

                price = float(price_raw)
                quantity = int(quantity_raw)

                if not product_name:
                    messagebox.showwarning(
                        "Input Required",
                        "Product name is required.",
                        parent=win
                    )
                    return

                if not unit:
                    messagebox.showwarning(
                        "Input Required",
                        "Unit is required. Example: kg, pc, tray.",
                        parent=win
                    )
                    return

                if price < 0:
                    messagebox.showwarning(
                        "Invalid Price",
                        "Price cannot be negative.",
                        parent=win
                    )
                    return

                if quantity < 0:
                    messagebox.showwarning(
                        "Invalid Quantity",
                        "Quantity cannot be negative.",
                        parent=win
                    )
                    return

            except ValueError:
                messagebox.showwarning(
                    "Invalid Input",
                    "Please check your entries.\n\n"
                    "Price must be a valid number.\n"
                    "Quantity must be a whole number.",
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

        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(fill="x", pady=(14, 0))

        gold_btn(
            btn_row,
            "💾 Save Product",
            save_form,
            height=44
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        danger_btn(
            btn_row,
            "✖ Cancel",
            win.destroy,
            height=44
        ).pack(side="left", fill="x", expand=True)

        name_entry.focus_set()
        win.wait_window()

        return result if result else None

    def _form_label(self, parent, text):
        tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold"),
            bg=CREAM,
            fg=DARK_RED,
            anchor="w"
        ).pack(fill="x", padx=20, pady=(14, 3))

    def _form_entry(self, parent, placeholder):
        entry = ctk.CTkEntry(
            parent,
            height=40,
            placeholder_text=placeholder,
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=F_BODY,
            corner_radius=10
        )
        entry.pack(fill="x", padx=20, pady=(0, 2))
        return entry

    # =========================
    # ADD / EDIT
    # =========================
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
                    self.inventory_id,
                    data["category"]
                )

            except TypeError:
                product_id = add_product(
                    data["product_name"],
                    data["price"],
                    data["unit"],
                    data["quantity"],
                    self.inventory_id
                )

            if product_id:
                messagebox.showinfo(
                    "Product Added",
                    f"'{data['product_name']}' was added to inventory.",
                    parent=self
                )
                self._refresh_products()
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
                "Edit Product",
                "Select a product to edit.",
                parent=self
            )
            return

        values = self.tree.item(selected_row, "values")

        if not values or values[0] == "—":
            return

        product_id = int(values[0])

        try:
            product = get_product_by_id(product_id)

            if not product:
                messagebox.showerror(
                    "Edit Product",
                    "Selected product was not found in database.",
                    parent=self
                )
                return

            data = self._product_form("Edit Product", product)

            if not data:
                return

            try:
                success = update_product(
                    product_id,
                    data["product_name"],
                    data["price"],
                    data["unit"],
                    data["quantity"],
                    self.inventory_id,
                    data["category"]
                )

            except TypeError:
                success = update_product(
                    product_id,
                    data["product_name"],
                    data["price"],
                    data["unit"],
                    data["quantity"],
                    self.inventory_id
                )

            if success:
                messagebox.showinfo(
                    "Product Updated",
                    "Product updated successfully.",
                    parent=self
                )
                self._refresh_products()
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
    InventoryDashboard("Inventory").mainloop()