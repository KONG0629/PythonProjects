from tkinter import *
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta

from databases.db import get_connection
from databases.pdf_receipt_backend import generate_receipt_pdf


# ============================================================
# COLORS / FONTS
# ============================================================
BG = "#fff8ec"
CARD_BG = "#ffffff"
CREAM = "#fff1d6"
DARK_RED = "#7B1C1C"
TEXT = "#2b1a14"
MUTED = "#7a5b50"
BORDER = "#e6d5c1"
SIDEBAR = "#2b0f0a"
WHITE = "#ffffff"
GOLD = "#d4a017"
ODD_ROW = "#fffaf2"
GREEN = "#2e7d32"
LIGHT_GREEN = "#e8f5e9"
RED = "#B03A2E"
SOFT_RED = "#FDECEA"

F_TITLE = ("Georgia", 24, "bold")
F_HEAD = ("Segoe UI", 15, "bold")
F_BODY = ("Segoe UI", 10)
F_BOLD = ("Segoe UI", 10, "bold")
F_SMALL = ("Segoe UI", 9)


MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

MONTH_NUM = {month: index + 1 for index, month in enumerate(MONTHS)}
CURRENT_YEAR = datetime.now().year
YEARS = [str(year) for year in range(2004, CURRENT_YEAR + 6)]


# ============================================================
# HELPER FUNCTIONS
# ============================================================
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


def safe_error(error):
    text = str(error).strip()
    return text if text else repr(error)


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


# ============================================================
# DATABASE FUNCTIONS
# ============================================================
def get_cashier_sales_records(start_date, end_date):
    connection = get_connection()

    if connection is None:
        raise Exception("Database connection failed.")

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                o.order_id,
                COALESCE(u.full_name, 'Cashier') AS cashier_name,

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
            LEFT JOIN users u
                ON o.cashier_id = u.user_id
            LEFT JOIN payments p
                ON o.order_id = p.order_id
            JOIN order_items oi
                ON o.order_id = oi.order_id

            WHERE LOWER(o.order_status) = 'accepted'
            AND o.accepted_at IS NOT NULL
            AND DATE(o.accepted_at) BETWEEN %s AND %s

            ORDER BY o.accepted_at DESC, o.order_id DESC, oi.order_item_id ASC
            """,
            (start_date, end_date)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


# ============================================================
# CASHIER ORDER STATUS PAGE
# ============================================================
class CashierOrderStatus(Frame):
    def __init__(self, parent, user_name="Cashier"):
        super().__init__(parent, bg=BG)
        self.pack(fill="both", expand=True)

        self.user_name = user_name
        self.period_var = StringVar(master=self, value="Week")

        self._raw_sales = []
        self._grouped_orders = []

        self._build()

    # ============================================================
    # UI HELPERS
    # ============================================================
    def _card(self, parent, bg_color=CARD_BG, border_color=BORDER):
        return Frame(
            parent,
            bg=bg_color,
            highlightbackground=border_color,
            highlightthickness=1
        )

    def _solid_button(self, parent, text, command, bg_color, hover_color, width=16):
        button = Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=bg_color,
            fg=WHITE,
            activebackground=hover_color,
            activeforeground=WHITE,
            relief="flat",
            cursor="hand2",
            width=width,
            padx=12,
            pady=8,
            bd=0
        )

        button.bind("<Enter>", lambda event: button.config(bg=hover_color))
        button.bind("<Leave>", lambda event: button.config(bg=bg_color))

        return button

    def receipt_button(self, parent, text, command):
        return self._solid_button(
            parent,
            text,
            command,
            GREEN,
            "#256428",
            width=22
        )

    # ============================================================
    # BUILD UI
    # ============================================================
    def _build(self):
        self._build_header()

        main = Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=22, pady=(16, 20))

        self._build_receipt_action(main)
        self._build_filter_area(main)

        self.range_label = Label(
            main,
            text="",
            font=("Segoe UI", 10, "italic"),
            bg=BG,
            fg=MUTED
        )
        self.range_label.pack(anchor="w", pady=(0, 8))

        self.summary_frame = Frame(main, bg=BG)
        self.summary_frame.pack(fill="x", pady=(0, 12))

        self._build_table(main)

        self._on_period()

    # ============================================================
    # HEADER
    # ============================================================
    def _build_header(self):
        header = Frame(self, bg=CREAM, height=94)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_box = Frame(header, bg=CREAM)
        title_box.pack(side="left", padx=26, pady=14)

        Label(
            title_box,
            text="🧾 Cashier Order Status",
            font=F_TITLE,
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w")

        Label(
            title_box,
            text="View completed sales, filter reports, and generate PDF receipts for selected orders.",
            font=("Segoe UI", 10, "bold"),
            bg=CREAM,
            fg=TEXT
        ).pack(anchor="w", pady=(2, 0))

        right_box = Frame(header, bg=CREAM)
        right_box.pack(side="right", padx=24, pady=18)

        Label(
            right_box,
            text=f"Cashier: {self.user_name}",
            font=("Segoe UI", 10, "bold"),
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="e")

        Label(
            right_box,
            text=datetime.now().strftime("%B %d, %Y"),
            font=("Segoe UI", 9),
            bg=CREAM,
            fg=MUTED
        ).pack(anchor="e", pady=(2, 0))

    # ============================================================
    # RECEIPT ACTION AREA
    # ============================================================
    def _build_receipt_action(self, parent):
        receipt_card = self._card(
            parent,
            bg_color=LIGHT_GREEN,
            border_color=GREEN
        )
        receipt_card.pack(fill="x", pady=(0, 12))

        receipt_card.columnconfigure(0, weight=1)
        receipt_card.columnconfigure(1, weight=0)

        left = Frame(receipt_card, bg=LIGHT_GREEN)
        left.grid(row=0, column=0, sticky="ew", padx=18, pady=14)

        Label(
            left,
            text="🧾 Generate Single Receipt",
            font=("Segoe UI", 16, "bold"),
            bg=LIGHT_GREEN,
            fg="#1b5e20"
        ).pack(anchor="w")

        Label(
            left,
            text="Select one accepted order from the table below, then save its receipt as PDF.",
            font=("Segoe UI", 10),
            bg=LIGHT_GREEN,
            fg="#1b5e20"
        ).pack(anchor="w", pady=(2, 0))

        self.generate_receipt_btn = self.receipt_button(
            receipt_card,
            "Generate PDF Receipt",
            self.generate_selected_receipt
        )
        self.generate_receipt_btn.grid(row=0, column=1, sticky="e", padx=18, pady=14)

    # ============================================================
    # FILTER AREA
    # ============================================================
    def _build_filter_area(self, parent):
        filter_card = self._card(parent)
        filter_card.pack(fill="x", pady=(0, 12))

        title_row = Frame(filter_card, bg=CARD_BG)
        title_row.pack(fill="x", padx=16, pady=(12, 4))

        Label(
            title_row,
            text="📅 Sales Filter",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left")

        Label(
            title_row,
            text="Choose a date range to display accepted orders.",
            font=F_SMALL,
            bg=CARD_BG,
            fg=MUTED
        ).pack(side="right")

        control_frame = Frame(filter_card, bg=CARD_BG)
        control_frame.pack(fill="x", padx=16, pady=(6, 10))

        Label(
            control_frame,
            text="Filter by:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(0, 8))

        for period in ("Week", "Month", "Year"):
            Radiobutton(
                control_frame,
                text=period,
                variable=self.period_var,
                value=period,
                font=F_BOLD,
                bg=CARD_BG,
                fg=DARK_RED,
                selectcolor=CREAM,
                activebackground=CARD_BG,
                activeforeground=DARK_RED,
                command=self._on_period,
                cursor="hand2"
            ).pack(side="left", padx=8)

        self.pick_frame = Frame(filter_card, bg=CARD_BG)
        self.pick_frame.pack(fill="x", padx=16, pady=(0, 14))

        now = datetime.now()

        # Week filter
        self.week_filter_frame = Frame(self.pick_frame, bg=CARD_BG)

        self.week_year_var = StringVar(master=self, value=str(now.year))
        self.week_month_var = StringVar(master=self, value=MONTHS[now.month - 1])
        self.week_var = StringVar(master=self)

        current_week_values = get_weeks_in_month(now.year, now.month)
        self.week_var.set(current_week_values[0])

        Label(
            self.week_filter_frame,
            text="Month:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

        self._combo(
            self.week_filter_frame,
            self.week_month_var,
            MONTHS,
            12,
            command=lambda event: self._refresh_week_choices()
        ).pack(side="left", padx=(4, 8))

        Label(
            self.week_filter_frame,
            text="Year:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

        self._combo(
            self.week_filter_frame,
            self.week_year_var,
            YEARS,
            6,
            command=lambda event: self._refresh_week_choices()
        ).pack(side="left", padx=(4, 8))

        Label(
            self.week_filter_frame,
            text="Week:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

        self.week_combo = self._combo(
            self.week_filter_frame,
            self.week_var,
            current_week_values,
            25
        )
        self.week_combo.pack(side="left", padx=(4, 0))

        # Month filter
        self.month_filter_frame = Frame(self.pick_frame, bg=CARD_BG)

        self.month_var = StringVar(master=self, value=MONTHS[now.month - 1])
        self.month_year_var = StringVar(master=self, value=str(now.year))

        Label(
            self.month_filter_frame,
            text="Month:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

        self._combo(
            self.month_filter_frame,
            self.month_var,
            MONTHS,
            12
        ).pack(side="left", padx=(4, 8))

        Label(
            self.month_filter_frame,
            text="Year:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

        self._combo(
            self.month_filter_frame,
            self.month_year_var,
            YEARS,
            6
        ).pack(side="left", padx=(4, 0))

        # Year filter
        self.year_filter_frame = Frame(self.pick_frame, bg=CARD_BG)

        self.year_var = StringVar(master=self, value=str(now.year))

        Label(
            self.year_filter_frame,
            text="Year:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

        self._combo(
            self.year_filter_frame,
            self.year_var,
            YEARS,
            6
        ).pack(side="left", padx=(4, 0))

    # ============================================================
    # TABLE
    # ============================================================
    def _build_table(self, parent):
        table_card = self._card(parent)
        table_card.pack(fill="both", expand=True)

        table_header = Frame(table_card, bg=CARD_BG)
        table_header.pack(fill="x", padx=16, pady=(14, 6))

        left = Frame(table_header, bg=CARD_BG)
        left.pack(side="left")

        Label(
            left,
            text="📋 Accepted Orders",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(anchor="w")

        Label(
            left,
            text="Only accepted orders are displayed. Select one row before generating a receipt.",
            font=F_SMALL,
            bg=CARD_BG,
            fg=MUTED
        ).pack(anchor="w", pady=(1, 0))

        self.result_label = Label(
            table_header,
            text="0 order(s) shown",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg=MUTED
        )
        self.result_label.pack(side="right", pady=(18, 0))

        table_frame = Frame(table_card, bg=CARD_BG)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "CashierReceipt.Treeview",
            background=CARD_BG,
            fieldbackground=CARD_BG,
            foreground=TEXT,
            rowheight=41,
            font=("Segoe UI", 10)
        )

        style.configure(
            "CashierReceipt.Treeview.Heading",
            background=SIDEBAR,
            foreground=WHITE,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )

        style.map(
            "CashierReceipt.Treeview",
            background=[("selected", GOLD)],
            foreground=[("selected", DARK_RED)]
        )

        columns = (
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

        widths = [85, 360, 85, 115, 115, 125, 130, 140, 165]

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="CashierReceipt.Treeview",
            selectmode="browse"
        )

        for column_name, width in zip(columns, widths):
            self.tree.heading(column_name, text=column_name)
            self.tree.column(column_name, width=width, anchor="center", minwidth=60)

        self.tree.column("Products", anchor="w")
        self.tree.column("Cashier", anchor="w")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.tree.tag_configure("odd", background=ODD_ROW)
        self.tree.tag_configure("even", background=CARD_BG)

    # ============================================================
    # COMBOBOX
    # ============================================================
    def _combo(self, parent, var, values, width_chars, command=None):
        combo = ttk.Combobox(
            parent,
            textvariable=var,
            values=values,
            width=width_chars,
            state="readonly",
            font=("Segoe UI", 10)
        )

        if command:
            combo.bind("<<ComboboxSelected>>", command)
        else:
            combo.bind("<<ComboboxSelected>>", lambda event: self._load())

        return combo

    # ============================================================
    # DATE FILTERS
    # ============================================================
    def _refresh_week_choices(self):
        year_value = int(self.week_year_var.get())
        month_value = MONTH_NUM[self.week_month_var.get()]

        week_values = get_weeks_in_month(year_value, month_value)

        self.week_combo.configure(values=week_values)
        self.week_var.set(week_values[0])

        self._load()

    def _on_period(self):
        for frame in (
            self.week_filter_frame,
            self.month_filter_frame,
            self.year_filter_frame
        ):
            frame.pack_forget()

        if self.period_var.get() == "Week":
            self.week_filter_frame.pack(side="left")
        elif self.period_var.get() == "Month":
            self.month_filter_frame.pack(side="left")
        else:
            self.year_filter_frame.pack(side="left")

        self._load()

    def _get_date_range(self):
        period = self.period_var.get()

        if period == "Week":
            year_value = int(self.week_year_var.get())
            month_value = MONTH_NUM[self.week_month_var.get()]
            selected_week = self.week_var.get()

            week_number = int(selected_week.split()[1])

            month_start = date(year_value, month_value, 1)
            month_end = get_month_last_day(year_value, month_value)

            start_date = month_start + timedelta(days=(week_number - 1) * 7)
            end_date = min(start_date + timedelta(days=6), month_end)

            return start_date, end_date

        if period == "Month":
            month_value = MONTH_NUM[self.month_var.get()]
            year_value = int(self.month_year_var.get())

            start_date = date(year_value, month_value, 1)
            end_date = get_month_last_day(year_value, month_value)

            return start_date, end_date

        year_value = int(self.year_var.get())

        return date(year_value, 1, 1), date(year_value, 12, 31)

    # ============================================================
    # GROUP DATA
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
                    "cashier_name": row.get("cashier_name") or "Cashier",
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

    # ============================================================
    # LOAD DATA
    # ============================================================
    def _load(self):
        try:
            start_date, end_date = self._get_date_range()

            self.range_label.config(
                text=f"Showing accepted orders from {start_date} to {end_date}"
            )

            self._raw_sales = get_cashier_sales_records(start_date, end_date)
            self._grouped_orders = self._group_sales_by_order(self._raw_sales)

            self._load_summary_cards()
            self._load_table()

        except Exception as e:
            messagebox.showerror(
                "Load Error",
                f"Unable to load cashier order status.\n\n{safe_error(e)}",
                parent=self
            )

    def _load_summary_cards(self):
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        revenue = sum(safe_float(order["final_total"]) for order in self._grouped_orders)
        discounts = sum(safe_float(order["discount"]) for order in self._grouped_orders)
        transactions = len(self._grouped_orders)
        qty = sum(safe_int(order["total_qty"]) for order in self._grouped_orders)

        stats = [
            ("💰 Revenue", format_money(revenue), "Total accepted sales", SIDEBAR),
            ("🏷 Discounts", format_money(discounts), "Total discount given", RED),
            ("🧾 Orders", str(transactions), "Accepted transactions", GREEN),
            ("🔢 Items Sold", str(qty), "Total product quantity", GOLD),
        ]

        for index, (label, value, subtitle, color) in enumerate(stats):
            card = Frame(self.summary_frame, bg=color, height=104)
            card.grid(row=0, column=index, sticky="ew", padx=6)
            card.grid_propagate(False)

            self.summary_frame.columnconfigure(index, weight=1)

            Label(
                card,
                text=label,
                font=("Segoe UI", 10, "bold"),
                bg=color,
                fg=CREAM
            ).pack(anchor="w", padx=15, pady=(12, 0))

            Label(
                card,
                text=value,
                font=("Georgia", 18, "bold"),
                bg=color,
                fg=WHITE
            ).pack(anchor="w", padx=15, pady=(1, 0))

            Label(
                card,
                text=subtitle,
                font=("Segoe UI", 8),
                bg=color,
                fg=CREAM
            ).pack(anchor="w", padx=15, pady=(2, 8))

    def _load_table(self):
        self.tree.delete(*self.tree.get_children())

        if hasattr(self, "result_label"):
            self.result_label.config(text=f"{len(self._grouped_orders)} order(s) shown")

        if not self._grouped_orders:
            self.tree.insert(
                "",
                "end",
                values=(
                    "—",
                    "No accepted orders found for this selected date range",
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

        for index, order in enumerate(self._grouped_orders):
            sale_date = order.get("sale_date")
            sale_date_text = str(sale_date)[:16] if sale_date else ""
            products_text = ", ".join(order["products"])

            self.tree.insert(
                "",
                "end",
                iid=str(order["order_id"]),
                values=(
                    order["order_id"],
                    products_text,
                    order["total_qty"],
                    format_money(order["subtotal"]),
                    format_money(order["discount"]),
                    format_money(order["final_total"]),
                    order.get("payment_method") or "Cash",
                    order["cashier_name"],
                    sale_date_text
                ),
                tags=("odd" if index % 2 else "even",)
            )

    # ============================================================
    # SELECTED ORDER
    # ============================================================
    def get_selected_order_info(self):
        selected = self.tree.focus()

        if not selected:
            messagebox.showwarning(
                "Generate Receipt",
                "Please select one order first.",
                parent=self
            )
            return None

        values = self.tree.item(selected, "values")

        if not values or values[0] == "—":
            messagebox.showwarning(
                "Generate Receipt",
                "Please select a valid order.",
                parent=self
            )
            return None

        order_id = str(values[0])

        for order in self._grouped_orders:
            if str(order.get("order_id")) == order_id:
                return order

        messagebox.showwarning(
            "Generate Receipt",
            "Selected order data was not found. Please refresh and try again.",
            parent=self
        )
        return None

    # ============================================================
    # PREPARE RECEIPT DATA
    # ============================================================
    def prepare_receipt_rows_for_pdf(self, order_info):
        prepared_rows = []

        subtotal_amount = safe_float(order_info.get("subtotal"))
        discount_amount = safe_float(order_info.get("discount"))
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
    # GENERATE SINGLE RECEIPT
    # ============================================================
    def generate_selected_receipt(self):
        try:
            order_info = self.get_selected_order_info()

            if not order_info:
                return

            order_id = str(order_info.get("order_id"))

            path = filedialog.asksaveasfilename(
                parent=self.winfo_toplevel(),
                title="Save Receipt PDF",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"Receipt_Order_{order_id}.pdf"
            )

            if not path:
                return

            if not path.lower().endswith(".pdf"):
                path += ".pdf"

            rows_to_print = self.prepare_receipt_rows_for_pdf(order_info)

            generate_receipt_pdf(
                rows=rows_to_print,
                filename=path,
                generated_by="Cashier"
            )

            messagebox.showinfo(
                "Receipt Generated",
                f"Receipt PDF saved successfully:\n\n{path}",
                parent=self
            )

        except Exception as e:
            messagebox.showerror(
                "Receipt Error",
                f"Unable to generate receipt PDF.\n\n{safe_error(e)}",
                parent=self
            )