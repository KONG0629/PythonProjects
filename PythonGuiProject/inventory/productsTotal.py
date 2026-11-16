import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from theme import *

from databases.product_backend import get_inventory_products

ctk.set_appearance_mode("light")


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


class ProductsTotal(ctk.CTk):
    def __init__(self, user_name="Inventory"):
        super().__init__()

        self.user_name = user_name
        self.products = []
        self.filtered_products = []

        self.filter_var = tk.StringVar(master=self, value="All")
        self.search_var = tk.StringVar(master=self)
        self.sort_asc = True

        self.title("Inventory — Products Overview")
        self.configure(fg_color=BG)
        self.attributes("-fullscreen", True)

        self._build()

    # =========================
    # NAVIGATION
    # =========================
    def _go_inventory(self):
        try:
            self.configure(cursor="watch")
            self.update_idletasks()

            from inventory.inventoryDashboard import InventoryDashboard
            app = InventoryDashboard(self.user_name)

            self.destroy()
            app.mainloop()

        except Exception as e:
            self.configure(cursor="")
            messagebox.showerror(
                "Navigation Error",
                f"Unable to open Inventory Dashboard.\n\n{e}",
                parent=self
            )

    # =========================
    # MAIN UI
    # =========================
    def _build(self):
        nav = [
            ("inventory", "📦", "Inventory", self._go_inventory),
            ("total", "📊", "Products Total", lambda: None),
        ]

        make_sidebar(self, self.user_name, "Inventory Staff", nav, "total")

        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="right", fill="both", expand=True)

        self._build_header()
        self._build_kpi_container()
        self._build_middle_panels()
        self._build_search_filter_bar()
        self._build_table()

        self._load()

    def _build_header(self):
        header = tk.Frame(self.main, bg=CREAM, height=82)
        header.pack(fill="x")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=CREAM)
        left.pack(side="left", padx=26, pady=12)

        tk.Label(
            left,
            text="📊 Products Overview",
            font=("Georgia", 22, "bold"),
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w")

        tk.Label(
            left,
            text="View total stocks, stock value, product status, and low-stock items.",
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

        primary_btn(
            right,
            "🔄 Refresh",
            self._load,
            height=38,
            width=130
        ).pack(side="left", padx=4)

    def _build_kpi_container(self):
        self.kpi_frame = tk.Frame(self.main, bg=BG)
        self.kpi_frame.pack(fill="x", padx=24, pady=(18, 10))

    def _build_middle_panels(self):
        wrapper = tk.Frame(self.main, bg=BG)
        wrapper.pack(fill="x", padx=24, pady=(0, 12))

        self.info_panel = tk.Frame(
            wrapper,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            height=250
        )
        self.info_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.info_panel.pack_propagate(False)

        self.alert_panel = tk.Frame(
            wrapper,
            bg="#FFF8E1",
            highlightbackground=GOLD,
            highlightthickness=1,
            width=540,
            height=250
        )
        self.alert_panel.pack(side="right", fill="both")
        self.alert_panel.pack_propagate(False)

    def _build_search_filter_bar(self):
        self.filter_card = tk.Frame(
            self.main,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.filter_card.pack(fill="x", padx=24, pady=(0, 12))

        top_row = tk.Frame(self.filter_card, bg=CARD_BG)
        top_row.pack(fill="x", padx=14, pady=(12, 8))

        tk.Label(
            top_row,
            text="Inventory Product Records",
            font=("Segoe UI", 13, "bold"),
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left")

        tk.Label(
            top_row,
            text="Unavailable products are included but not counted in active stock value.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg="#9B7B4A"
        ).pack(side="left", padx=10)

        bottom_row = tk.Frame(self.filter_card, bg=CARD_BG)
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
            textvariable=self.search_var,
            width=340,
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
            height=38,
            width=95
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
            command=self._show_all
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
            width=16,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.filter_cb.pack(side="left", padx=4, ipady=4)
        self.filter_cb.bind("<<ComboboxSelected>>", lambda event: self._apply_filter_sort_load())

        self.sort_btn = gold_btn(
            bottom_row,
            "🔤 A → Z",
            self._toggle_sort,
            height=38,
            width=110
        )
        self.sort_btn.pack(side="left", padx=4)

        gold_btn(
            bottom_row,
            "📋 Show All",
            self._show_all,
            height=38,
            width=115
        ).pack(side="left", padx=4)

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
            "InventoryProduct.Treeview",
            background=CARD_BG,
            fieldbackground=CARD_BG,
            foreground=TEXT,
            rowheight=42,
            font=("Segoe UI", 10)
        )

        style.configure(
            "InventoryProduct.Treeview.Heading",
            background=SIDEBAR,
            foreground=WHITE,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padding=8
        )

        style.map(
            "InventoryProduct.Treeview",
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

        widths = {
            "ID": 65,
            "Name": 280,
            "Category": 180,
            "Price": 125,
            "Unit": 90,
            "Quantity": 110,
            "Stock Value": 150,
            "Status": 150
        }

        self.tree = ttk.Treeview(
            table_card,
            columns=cols,
            show="headings",
            style="InventoryProduct.Treeview"
        )

        for col_name in cols:
            self.tree.heading(col_name, text=col_name)
            self.tree.column(
                col_name,
                width=widths[col_name],
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

        self.tree.tag_configure("odd", background=ODD_ROW, foreground=TEXT)
        self.tree.tag_configure("even", background=CARD_BG, foreground=TEXT)
        self.tree.tag_configure("low", background="#FFF3CD", foreground="#856404")
        self.tree.tag_configure("out", background="#F8D7DA", foreground="#842029")
        self.tree.tag_configure("inactive", background="#ECEFF1", foreground="#7B7D7D")

        self.table_hint = tk.Label(
            table_card,
            text="Showing product overview records.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT
        )
        self.table_hint.pack(anchor="w", padx=10, pady=(0, 8))

    # =========================
    # DATA LOADING
    # =========================
    def _load(self):
        try:
            self.configure(cursor="watch")
            self.update_idletasks()

            self.search_var.set("")
            self.filter_var.set("All")

            self.products = get_inventory_products()

            self._build_info_panel(self.products)
            self._build_alert_panel(self.products)
            self._apply_filter_sort_load()

        except Exception as e:
            messagebox.showerror(
                "Database Error",
                f"Unable to load products from database.\n\n{e}",
                parent=self
            )

        finally:
            self.configure(cursor="")

    def _show_all(self):
        self.search_var.set("")
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
        keyword = self.search_var.get().strip()
        selected_filter = self.filter_var.get()

        rows = [
            product for product in self.products
            if self._product_matches_search(product, keyword)
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
                and 0 < safe_int(p.get("quantity")) < LOW_STOCK_LIMIT
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

        self._build_kpis(rows)
        self._build_info_panel(rows)
        self._build_alert_panel(rows)
        self._load_table(rows)

    def _toggle_sort(self):
        self.sort_asc = not self.sort_asc
        self.sort_btn.configure(text="🔤 A → Z" if self.sort_asc else "🔤 Z → A")
        self._apply_filter_sort_load()

    # =========================
    # KPI / INFO / ALERTS
    # =========================
    def _build_kpis(self, rows):
        for widget in self.kpi_frame.winfo_children():
            widget.destroy()

        total_products = len(rows)

        available_products = sum(
            1 for p in rows
            if str(p.get("status", "active")).lower() == "active"
        )

        unavailable_products = sum(
            1 for p in rows
            if str(p.get("status", "active")).lower() == "inactive"
        )

        total_units = sum(
            safe_int(p.get("quantity"))
            for p in rows
            if str(p.get("status", "active")).lower() == "active"
        )

        stock_value = sum(
            safe_float(p.get("price")) * safe_int(p.get("quantity"))
            for p in rows
            if str(p.get("status", "active")).lower() == "active"
        )

        low_stock = sum(
            1 for p in rows
            if str(p.get("status", "active")).lower() == "active"
            and 0 < safe_int(p.get("quantity")) < LOW_STOCK_LIMIT
        )

        out_stock = sum(
            1 for p in rows
            if str(p.get("status", "active")).lower() == "active"
            and safe_int(p.get("quantity")) <= 0
        )

        kpis = [
            ("📦 Products", total_products, SIDEBAR, "Displayed records"),
            ("✅ Available", available_products, "#27AE60", "Active products"),
            ("🚫 Unavailable", unavailable_products, "#B03A2E", "Inactive products"),
            ("📊 Total Units", total_units, "#2874A6", "Active stocks"),
            ("⚠️ Low Stock", low_stock, GOLD, f"Below {LOW_STOCK_LIMIT}"),
            ("💰 Stock Value", format_money(stock_value), "#6C3483", "Active value"),
        ]

        for index, (label, value, color, subtitle) in enumerate(kpis):
            card = tk.Frame(
                self.kpi_frame,
                bg=color,
                highlightbackground=color,
                highlightthickness=1
            )
            card.grid(row=0, column=index, sticky="nsew", padx=5)
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
                font=("Georgia", 18, "bold"),
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

    def _build_info_panel(self, rows):
        for widget in self.info_panel.winfo_children():
            widget.destroy()

        total_rows = len(rows)
        active_rows = [
            p for p in rows
            if str(p.get("status", "active")).lower() == "active"
        ]

        active_stock_value = sum(
            safe_float(p.get("price")) * safe_int(p.get("quantity"))
            for p in active_rows
        )

        highest_value_product = None
        highest_value = 0

        for p in active_rows:
            value = safe_float(p.get("price")) * safe_int(p.get("quantity"))

            if value > highest_value:
                highest_value = value
                highest_value_product = p

        tk.Label(
            self.info_panel,
            text="Products Summary",
            font=("Segoe UI", 14, "bold"),
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(anchor="w", padx=18, pady=(14, 4))

        summary_text = (
            "This page gives a complete overview of your inventory products. "
            "Unavailable products are still shown for monitoring, but only available products are included in total stock value."
        )

        tk.Label(
            self.info_panel,
            text=summary_text,
            font=("Segoe UI", 10),
            bg=CARD_BG,
            fg=TEXT,
            wraplength=760,
            justify="left"
        ).pack(anchor="w", padx=18, pady=(0, 10))

        details = tk.Frame(self.info_panel, bg=CARD_BG)
        details.pack(fill="x", padx=18, pady=(2, 8))

        self._mini_info_card(
            details,
            "Displayed Records",
            str(total_rows),
            "#FDF2E9"
        )

        self._mini_info_card(
            details,
            "Active Stock Value",
            format_money(active_stock_value),
            "#EBF5FB"
        )

        if highest_value_product:
            product_name = highest_value_product.get("product_name", "Unnamed Product")
            top_text = f"{product_name} — {format_money(highest_value)}"
        else:
            top_text = "No active product"

        tk.Label(
            self.info_panel,
            text=f"Top stock value item: {top_text}",
            font=("Segoe UI", 10, "bold"),
            bg=CARD_BG,
            fg=DARK_RED,
            wraplength=760,
            justify="left"
        ).pack(anchor="w", padx=18, pady=(2, 0))

    def _mini_info_card(self, parent, label, value, color):
        card = tk.Frame(
            parent,
            bg=color,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        card.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Label(
            card,
            text=label,
            font=("Segoe UI", 9, "bold"),
            bg=color,
            fg=TEXT
        ).pack(anchor="w", padx=10, pady=(8, 0))

        tk.Label(
            card,
            text=value,
            font=("Segoe UI", 12, "bold"),
            bg=color,
            fg=DARK_RED
        ).pack(anchor="w", padx=10, pady=(0, 8))

    def _build_alert_panel(self, rows):
        for widget in self.alert_panel.winfo_children():
            widget.destroy()

        header = tk.Frame(self.alert_panel, bg="#FFF8E1")
        header.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(
            header,
            text="⚠️ Stock Watch",
            font=("Segoe UI", 15, "bold"),
            bg="#FFF8E1",
            fg=DARK_RED
        ).pack(side="left")

        low_items = [
            p for p in rows
            if str(p.get("status", "active")).lower() == "active"
            and safe_int(p.get("quantity")) < LOW_STOCK_LIMIT
        ]

        low_items = sorted(
            low_items,
            key=lambda p: safe_int(p.get("quantity"))
        )

        tk.Label(
            header,
            text=f"{len(low_items)} item(s)",
            font=("Segoe UI", 10, "bold"),
            bg="#FFF8E1",
            fg=TEXT
        ).pack(side="right")

        if not low_items:
            empty_box = tk.Frame(
                self.alert_panel,
                bg="#EAF7EA",
                highlightbackground="#A9DFBF",
                highlightthickness=1
            )
            empty_box.pack(fill="both", expand=True, padx=16, pady=(8, 16))

            tk.Label(
                empty_box,
                text="✅ No low-stock products in this view.",
                font=("Segoe UI", 12, "bold"),
                bg="#EAF7EA",
                fg="#1E8449"
            ).pack(anchor="center", pady=(40, 4))

            tk.Label(
                empty_box,
                text="Your displayed active products currently have enough stocks.",
                font=("Segoe UI", 10),
                bg="#EAF7EA",
                fg=TEXT,
                wraplength=460,
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

        for item in low_items:
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
                wraplength=460,
                justify="left"
            ).pack(anchor="w", padx=12, pady=(0, 2))

            tk.Label(
                row,
                text=f"Category: {category}",
                font=("Segoe UI", 9),
                bg=bg_color,
                fg=TEXT,
                wraplength=460,
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
    # TABLE
    # =========================
    def _load_table(self, rows):
        self.tree.delete(*self.tree.get_children())

        if not rows:
            self.tree.insert(
                "",
                "end",
                values=("—", "No products found", "—", "₱0.00", "—", "0", "₱0.00", "—"),
                tags=("even",)
            )
            self.table_hint.configure(text="No products found.")
            return

        for index, product in enumerate(rows):
            product_id = product.get("product_id")
            product_name = product.get("product_name") or "Unnamed Product"
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

                elif quantity < LOW_STOCK_LIMIT:
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

        self.table_hint.configure(
            text=f"Showing {len(rows)} product record(s). Active products are included in stock value; unavailable products are displayed in gray."
        )


def run(user_name="Inventory"):
    app = ProductsTotal(user_name)
    app.mainloop()


if __name__ == "__main__":
    run()