"""
admin/mostBuyproduct.py

Admin Best Selling Products page connected to MySQL.

UI upgraded to match Admin Dashboard style.

Features:
- Dashboard-style header
- KPI summary cards
- Period filter: All Time, Month, Year
- Month/year dropdown controls
- Top product highlight panel
- Bigger scrollable Product Insights panel
- Best-selling products bar chart
- Ranking table
- Refresh button
- No backend function removed
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

from databases.report_backend import (
    get_best_selling_products,
    get_best_selling_products_by_month,
    get_best_selling_products_by_year
)

ctk.set_appearance_mode("light")


# ============================================================
# MONTH AND YEAR OPTIONS
# ============================================================
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

MONTH_NUM = {month_name: index + 1 for index, month_name in enumerate(MONTHS)}

CURRENT_YEAR = datetime.now().year
YEARS = [str(year) for year in range(2004, CURRENT_YEAR + 6)]

CHART_COLORS = [
    "#7B1E1E",
    "#D4A017",
    "#27AE60",
    "#6C3483",
    "#B03A2E",
    "#2874A6",
    "#CA6F1E",
    "#117864",
    "#884EA0",
    "#196F3D",
]


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


def safe_float(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def short_text(value, limit=24):
    value = str(value or "")

    if len(value) <= limit:
        return value

    return value[:limit - 1] + "…"


# ============================================================
# BEST SELLING PRODUCTS CLASS
# ============================================================
class MostBuyedProducts(ctk.CTk):

    def __init__(self, user_name="Admin"):
        super().__init__()

        self.user_name = user_name

        self.period_var = tk.StringVar(master=self, value="All Time")

        now = datetime.now()
        self.selected_month = now.month
        self.selected_year = now.year

        self.current_data = []

        self.title("Admin — Best Selling Products")
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

        make_sidebar(self, self.user_name, "Administrator", nav, "mostbuyed")

        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="right", fill="both", expand=True)

        # ========================================================
        # HEADER — DASHBOARD STYLE
        # ========================================================
        hdr = tk.Frame(self.main, bg=CREAM, height=74)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        left_hdr = tk.Frame(hdr, bg=CREAM)
        left_hdr.pack(side="left", padx=24, pady=10)

        tk.Label(
            left_hdr,
            text="🏆 Best Selling Products",
            font=F_TITLE,
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w")

        tk.Label(
            left_hdr,
            text="Track the products with the highest accepted sales performance.",
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

        for period in ("All Time", "Month", "Year"):
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
                command=self._on_period_change
            ).pack(side="left", padx=6)

        self.filter_controls = tk.Frame(filter_card, bg=CARD_BG)
        self.filter_controls.pack(side="left", padx=12)

        primary_btn(
            filter_card,
            "🔄 Refresh",
            self._load,
            height=34,
            width=110
        ).pack(side="right", padx=12, pady=10)

        self._build_filter_controls()

        # ========================================================
        # CONTENT GRID
        # ========================================================
        self.content_grid = tk.Frame(self.main, bg=BG)
        self.content_grid.pack(fill="both", expand=False, padx=22, pady=(0, 10))

        left_panel = tk.Frame(self.content_grid, bg=BG)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))

        right_panel = tk.Frame(self.content_grid, bg=BG, width=430)
        right_panel.pack(side="right", fill="both", padx=(6, 0))
        right_panel.pack_propagate(False)

        self.chart_card = tk.Frame(
            left_panel,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            height=300
        )
        self.chart_card.pack(fill="both", expand=True)
        self.chart_card.pack_propagate(False)

        self.highlight_card = tk.Frame(
            right_panel,
            bg="#FFF8E1",
            highlightbackground=GOLD,
            highlightthickness=1,
            height=300
        )
        self.highlight_card.pack(fill="both", expand=True)
        self.highlight_card.pack_propagate(False)

        # ========================================================
        # TABLE TITLE
        # ========================================================
        table_title = tk.Frame(self.main, bg=BG)
        table_title.pack(fill="x", padx=22)

        tk.Label(
            table_title,
            text="Product Ranking",
            font=F_HEAD,
            bg=BG,
            fg=DARK_RED
        ).pack(side="left")

        tk.Label(
            table_title,
            text="Only accepted orders are counted",
            font=("Segoe UI", 10, "italic"),
            bg=BG,
            fg=TEXT
        ).pack(side="left", padx=10)

        # ========================================================
        # TABLE CONTAINER
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
            "MB.Treeview",
            background=CARD_BG,
            fieldbackground=CARD_BG,
            foreground=TEXT,
            rowheight=42,
            font=("Segoe UI", 11)
        )

        style.configure(
            "MB.Treeview.Heading",
            background=SIDEBAR,
            foreground=WHITE,
            font=("Segoe UI", 11, "bold"),
            relief="flat"
        )

        style.map(
            "MB.Treeview",
            background=[("selected", GOLD)],
            foreground=[("selected", DARK_RED)]
        )

        cols = ("Rank", "Product Name", "Total Qty Sold", "Total Revenue (₱)", "Contribution")
        widths = [90, 360, 180, 200, 160]

        self.tree = ttk.Treeview(
            tbl,
            columns=cols,
            show="headings",
            style="MB.Treeview"
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

        self.tree.tag_configure("gold", background="#FFF3CD", foreground="#7D4E00")
        self.tree.tag_configure("silver", background="#F0F0F0", foreground="#444444")
        self.tree.tag_configure("bronze", background="#FDEBD0", foreground="#6E2C00")
        self.tree.tag_configure("other", background=CARD_BG, foreground=TEXT)

        self._load()

    # ============================================================
    # KPI UI
    # ============================================================
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

    def _update_kpis(self, data):
        for widget in self.kpi_frame.winfo_children():
            widget.destroy()

        total_products = len(data)
        total_qty = sum(safe_int(row.get("total_quantity_sold")) for row in data)
        total_sales = sum(safe_float(row.get("total_sales")) for row in data)

        top_name = "No data"
        top_qty = 0

        if data:
            top_name = str(data[0].get("product_name") or "Unnamed")
            top_qty = safe_int(data[0].get("total_quantity_sold"))

        avg_revenue = total_sales / total_products if total_products > 0 else 0

        stats = [
            ("🏆 Ranked Products", str(total_products), SIDEBAR, "Displayed items"),
            ("🔢 Qty Sold", str(total_qty), GOLD, "Total quantity"),
            ("💰 Revenue", format_money(total_sales), "#27AE60", "Accepted sales"),
            ("⭐ Top Product", short_text(top_name, 18), "#6C3483", f"{top_qty} sold"),
            ("📊 Avg Revenue", format_money(avg_revenue), "#B03A2E", "Per ranked product"),
        ]

        for index, (label, value, color, subtext) in enumerate(stats):
            self._make_kpi_card(index, label, value, color, subtext)

    # ============================================================
    # BUILD FILTER CONTROLS
    # ============================================================
    def _build_filter_controls(self):
        for widget in self.filter_controls.winfo_children():
            widget.destroy()

        period = self.period_var.get()

        if period == "All Time":
            tk.Label(
                self.filter_controls,
                text="Showing all accepted sales records.",
                font=("Segoe UI", 9, "italic"),
                bg=CARD_BG,
                fg=TEXT
            ).pack(side="left")
            return

        if period == "Month":
            tk.Label(
                self.filter_controls,
                text="Month:",
                font=F_BOLD,
                bg=CARD_BG,
                fg=TEXT
            ).pack(side="left", padx=(0, 4))

            self.month_cb = ttk.Combobox(
                self.filter_controls,
                values=MONTHS,
                width=13,
                state="readonly",
                font=("Segoe UI", 10)
            )

            self.month_cb.set(MONTHS[self.selected_month - 1])
            self.month_cb.pack(side="left", padx=(0, 12))

            self.month_cb.bind(
                "<<ComboboxSelected>>",
                self._on_month_selected
            )

        tk.Label(
            self.filter_controls,
            text="Year:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(0, 4))

        self.year_cb = ttk.Combobox(
            self.filter_controls,
            values=YEARS,
            width=8,
            state="readonly",
            font=("Segoe UI", 10)
        )

        self.year_cb.set(str(self.selected_year))
        self.year_cb.pack(side="left", padx=(0, 8))

        self.year_cb.bind(
            "<<ComboboxSelected>>",
            self._on_year_selected
        )

    # ============================================================
    # PERIOD CHANGE
    # ============================================================
    def _on_period_change(self):
        self._build_filter_controls()
        self._load()

    # ============================================================
    # MONTH SELECTED
    # ============================================================
    def _on_month_selected(self, event=None):
        month_name = self.month_cb.get()
        self.selected_month = MONTH_NUM[month_name]
        self._load()

    # ============================================================
    # YEAR SELECTED
    # ============================================================
    def _on_year_selected(self, event=None):
        self.selected_year = int(self.year_cb.get())
        self._load()

    # ============================================================
    # GET DATA FROM BACKEND
    # ============================================================
    def _get_best_products_data(self):
        period = self.period_var.get()

        if period == "All Time":
            return get_best_selling_products(limit=10)

        if period == "Month":
            return get_best_selling_products_by_month(
                self.selected_year,
                self.selected_month,
                limit=10
            )

        if period == "Year":
            return get_best_selling_products_by_year(
                self.selected_year,
                limit=10
            )

        return []

    # ============================================================
    # CHART AND HIGHLIGHT
    # ============================================================
    def _draw_bar_chart(self, data):
        for widget in self.chart_card.winfo_children():
            widget.destroy()

        header = tk.Frame(self.chart_card, bg=CARD_BG)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Best Products Chart",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left", padx=14, pady=(10, 0))

        tk.Label(
            header,
            text="Visual ranking by quantity sold",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=10, pady=(13, 0))

        canvas = tk.Canvas(
            self.chart_card,
            width=760,
            height=250,
            bg=CARD_BG,
            highlightthickness=0
        )
        canvas.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        if not data:
            canvas.create_text(
                380,
                115,
                text="No accepted sales found for this filter.",
                font=("Segoe UI", 12, "bold"),
                fill=TEXT
            )
            return

        max_qty = max(safe_int(row.get("total_quantity_sold")) for row in data)

        if max_qty <= 0:
            canvas.create_text(
                380,
                115,
                text="No quantity data available.",
                font=("Segoe UI", 12, "bold"),
                fill=TEXT
            )
            return

        left_margin = 165
        top_margin = 22
        bar_height = 21
        gap = 9
        max_bar_width = 500

        for index, row in enumerate(data[:8]):
            product_name = str(row.get("product_name") or "Unnamed Product")
            qty = safe_int(row.get("total_quantity_sold"))

            y = top_margin + index * (bar_height + gap)
            bar_width = int((qty / max_qty) * max_bar_width)

            canvas.create_text(
                left_margin - 10,
                y + bar_height / 2,
                text=short_text(product_name, 23),
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
                text=f"{qty} sold",
                anchor="w",
                font=("Segoe UI", 9, "bold"),
                fill=DARK_RED
            )

    def _build_highlight_panel(self, data):
        for widget in self.highlight_card.winfo_children():
            widget.destroy()

        # Header fixed at top
        header = tk.Frame(self.highlight_card, bg="#FFF8E1")
        header.pack(fill="x")

        tk.Label(
            header,
            text="📌 Product Insights",
            font=("Segoe UI", 14, "bold"),
            bg="#FFF8E1",
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(12, 2))

        tk.Label(
            header,
            text="Scrollable summary of selected product performance.",
            font=("Segoe UI", 9, "italic"),
            bg="#FFF8E1",
            fg=TEXT
        ).pack(anchor="w", padx=14, pady=(0, 8))

        # Scrollable content area
        scroll_area = tk.Frame(self.highlight_card, bg="#FFF8E1")
        scroll_area.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        canvas = tk.Canvas(
            scroll_area,
            bg="#FFF8E1",
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            scroll_area,
            orient="vertical",
            command=canvas.yview
        )

        content = tk.Frame(canvas, bg="#FFF8E1")

        content.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def resize_content(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", resize_content)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)
        content.bind("<MouseWheel>", on_mousewheel)

        if not data:
            tk.Label(
                content,
                text="No accepted sales found for the selected filter.",
                font=("Segoe UI", 10),
                bg="#FFF8E1",
                fg=TEXT,
                wraplength=360,
                justify="left"
            ).pack(anchor="w", padx=8, pady=10)
            return

        total_qty = sum(safe_int(row.get("total_quantity_sold")) for row in data)
        total_sales = sum(safe_float(row.get("total_sales")) for row in data)

        top_product = data[0]
        top_name = str(top_product.get("product_name") or "Unnamed Product")
        top_qty = safe_int(top_product.get("total_quantity_sold"))
        top_sales = safe_float(top_product.get("total_sales"))

        top_contribution = (top_sales / total_sales * 100) if total_sales > 0 else 0

        second_product = data[1] if len(data) > 1 else None
        third_product = data[2] if len(data) > 2 else None

        second_text = "No second product"
        third_text = "No third product"

        if second_product:
            second_text = (
                f"{second_product.get('product_name')} "
                f"({safe_int(second_product.get('total_quantity_sold'))} sold)"
            )

        if third_product:
            third_text = (
                f"{third_product.get('product_name')} "
                f"({safe_int(third_product.get('total_quantity_sold'))} sold)"
            )

        lowest_product = data[-1]
        lowest_text = (
            f"{lowest_product.get('product_name')} "
            f"({safe_int(lowest_product.get('total_quantity_sold'))} sold)"
        )

        avg_qty = total_qty / len(data) if data else 0
        avg_sales = total_sales / len(data) if data else 0

        insights = [
            ("Top Product", top_name),
            ("Top Quantity Sold", f"{top_qty} item(s)"),
            ("Top Revenue", format_money(top_sales)),
            ("Top Contribution", f"{top_contribution:.1f}% of revenue"),
            ("Second Best Product", second_text),
            ("Third Best Product", third_text),
            ("Lowest Ranked Product", lowest_text),
            ("Total Quantity", f"{total_qty} item(s)"),
            ("Total Revenue", format_money(total_sales)),
            ("Average Quantity", f"{avg_qty:.1f} item(s) per product"),
            ("Average Revenue", f"{format_money(avg_sales)} per product"),
            ("Products Displayed", f"{len(data)} ranked product(s)"),
        ]

        for title, value in insights:
            box = tk.Frame(
                content,
                bg="#FFFDF2",
                highlightbackground="#E6C76E",
                highlightthickness=1
            )
            box.pack(fill="x", padx=6, pady=5)

            tk.Label(
                box,
                text=title,
                font=("Segoe UI", 9, "bold"),
                bg="#FFFDF2",
                fg=DARK_RED
            ).pack(anchor="w", padx=10, pady=(7, 0))

            tk.Label(
                box,
                text=value,
                font=("Segoe UI", 10),
                bg="#FFFDF2",
                fg=TEXT,
                wraplength=360,
                justify="left"
            ).pack(anchor="w", padx=10, pady=(0, 7))

    # ============================================================
    # LOAD TABLE
    # ============================================================
    def _load(self):
        try:
            self.tree.delete(*self.tree.get_children())

            data = self._get_best_products_data()
            self.current_data = data

            self._update_kpis(data)
            self._draw_bar_chart(data)
            self._build_highlight_panel(data)

            medals = ["🥇", "🥈", "🥉"]
            tags = ["gold", "silver", "bronze"]

            total_sales_all = sum(safe_float(row.get("total_sales")) for row in data)

            if not data:
                self.tree.insert(
                    "",
                    "end",
                    values=("—", "No accepted sales found", "0", "₱0.00", "0%"),
                    tags=("other",)
                )
                return

            for index, row in enumerate(data):
                rank = medals[index] if index < 3 else f"#{index + 1}"
                tag = tags[index] if index < 3 else "other"

                product_name = row.get("product_name")
                total_qty = safe_int(row.get("total_quantity_sold"))
                total_sales = safe_float(row.get("total_sales"))

                contribution = (total_sales / total_sales_all * 100) if total_sales_all > 0 else 0

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        rank,
                        product_name,
                        total_qty,
                        format_money(total_sales),
                        f"{contribution:.1f}%"
                    ),
                    tags=(tag,)
                )

        except Exception as e:
            messagebox.showerror(
                "Best Products Error",
                f"Unable to load best selling products.\n\n{e}",
                parent=self
            )


# ============================================================
# RUN DIRECTLY FOR TESTING
# ============================================================
if __name__ == "__main__":
    MostBuyedProducts("Admin").mainloop()