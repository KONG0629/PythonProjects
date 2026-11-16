"""
admin/adminHistory.py

Fixed Admin History / Activity Logs Module

Table Columns:
- ID
- User
- Role
- Action
- Description
- Date & Time

Fixes:
- Role filter now works even for old logs with NULL role.
- Action filter now works using readable action names.
- Activity Type filter now works properly.
- Search works with cleaned user, role, action, activity type, description, and date.
- Removed From and To date filters.
- Date display is fixed even if backend DATE_FORMAT is broken.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from datetime import datetime, date
import csv

from theme import *

from databases.admin_history_backend import (
    get_activity_logs,
    get_filter_options
)

ctk.set_appearance_mode("light")


# ============================================================
# FORMAT HELPERS
# ============================================================
def safe_text(value, fallback="-"):
    value = str(value or "").strip()
    return value if value else fallback


def short_text(value, limit=120):
    value = str(value or "")

    if len(value) <= limit:
        return value

    return value[:limit - 1] + "…"


def normalize_role(role):
    role = str(role or "unknown").strip().lower()

    if role in ("admin", "cashier", "inventory"):
        return role

    return "unknown"


def format_role(role):
    role = normalize_role(role)

    if role == "admin":
        return "Admin"
    if role == "cashier":
        return "Cashier"
    if role == "inventory":
        return "Inventory"

    return "Unknown"


def format_action(action):
    action = str(action or "").strip().upper()

    labels = {
        "CREATE_ORDER": "Created Order",
        "ACCEPT_ORDER": "Accepted Order",
        "CANCEL_ORDER": "Cancelled Order",

        "ADD_ACCOUNT": "Added Account",
        "CREATE_USER": "Added Account",
        "EDIT_ACCOUNT": "Edited Account",
        "UPDATE_ACCOUNT": "Updated Account",
        "UPDATE_USER": "Updated Account",
        "UPDATE_ACCOUNT_STATUS": "Updated Account Status",
        "CHANGE_PASSWORD": "Changed Password",
        "DELETE_USER": "Deactivated Account",
        "RESTORE_USER": "Restored Account",

        "ADD_PRODUCT": "Added Product",
        "EDIT_PRODUCT": "Edited Product",
        "UPDATE_PRODUCT": "Updated Product",
        "UPDATE_STOCK": "Updated Stock",
        "MARK_UNAVAILABLE": "Marked Unavailable",
        "RESTORE_PRODUCT": "Restored Product",

        "GENERATE_RECEIPT": "Generated Receipt",
        "GENERATE_REPORT": "Generated Report",

        "LOGIN": "Logged In",
        "LOGOUT": "Logged Out",
        "TEST_LOG": "Test Log",
    }

    return labels.get(action, action.replace("_", " ").title())


def get_activity_type(action_type, description):
    action = str(action_type or "").upper()
    desc = str(description or "").lower()

    if "ORDER" in action or "order" in desc:
        return "Orders"

    if "RECEIPT" in action or "receipt" in desc:
        return "Receipts"

    if (
        "PRODUCT" in action
        or "STOCK" in action
        or "product" in desc
        or "stock" in desc
        or "unavailable" in desc
        or "restored" in desc and "product" in desc
    ):
        return "Inventory"

    if (
        "USER" in action
        or "ACCOUNT" in action
        or "account" in desc
        or "user" in desc
        or "password" in desc
    ):
        return "Accounts"

    if "REPORT" in action or "report" in desc:
        return "Reports"

    if "LOGIN" in action or "LOGOUT" in action:
        return "System"

    return "General"


def infer_role_from_action(action_type, description):
    """
    Used for old logs where actor_role is NULL.
    This lets the Role filter still work properly.
    """
    action = str(action_type or "").upper()
    desc = str(description or "").lower()

    if (
        "USER" in action
        or "ACCOUNT" in action
        or "account" in desc
        or "user" in desc
        or "password" in desc
    ):
        return "admin"

    if (
        "PRODUCT" in action
        or "STOCK" in action
        or "product" in desc
        or "stock" in desc
        or "unavailable" in desc
    ):
        return "inventory"

    if "ORDER" in action or "order" in desc or "receipt" in desc:
        return "cashier"

    if "REPORT" in action or "report" in desc:
        return "admin"

    return "unknown"


def clean_username(username, role, action_type, description):
    username = str(username or "").strip()

    if username and username.lower() not in (
        "none",
        "null",
        "system/unknown",
        "unknown",
        "system"
    ):
        return username

    role = normalize_role(role)

    if role == "admin":
        return "Admin"
    if role == "cashier":
        return "Cashier"
    if role == "inventory":
        return "Inventory"

    guessed_role = infer_role_from_action(action_type, description)

    if guessed_role == "admin":
        return "Admin"
    if guessed_role == "cashier":
        return "Cashier"
    if guessed_role == "inventory":
        return "Inventory"

    return "System"


def fixed_datetime_display(log):
    created_at = log.get("created_at")
    formatted = str(log.get("formatted_created_at") or "").strip()

    if created_at:
        if isinstance(created_at, datetime):
            return created_at.strftime("%b %d, %Y %I:%M %p")

        if isinstance(created_at, date):
            return created_at.strftime("%b %d, %Y")

        created_text = str(created_at).strip()

        possible_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ]

        for fmt in possible_formats:
            try:
                parsed = datetime.strptime(created_text, fmt)
                return parsed.strftime("%b %d, %Y %I:%M %p")
            except Exception:
                pass

        if "%" not in created_text:
            return created_text

    if formatted and "%" not in formatted:
        return formatted

    return "-"


def role_color(role):
    role = normalize_role(role)

    if role == "admin":
        return DARK_RED
    if role == "cashier":
        return "#117864"
    if role == "inventory":
        return "#9A6A00"

    return TEXT


def role_filter_value(role_label):
    role_label = str(role_label or "").strip().lower()

    if role_label == "admin":
        return "admin"
    if role_label == "cashier":
        return "cashier"
    if role_label == "inventory":
        return "inventory"
    if role_label == "unknown":
        return "unknown"

    return "All"


# ============================================================
# MAIN HISTORY WINDOW
# ============================================================
class AdminHistory(ctk.CTk):
    def __init__(self, user_name="Admin"):
        super().__init__()

        self.user_name = user_name
        self.raw_logs = []
        self.all_prepared_logs = []
        self.prepared_logs = []
        self.selected_log = None

        self.search_var = tk.StringVar(master=self)
        self.role_var = tk.StringVar(master=self, value="All")
        self.action_var = tk.StringVar(master=self, value="All")
        self.activity_type_var = tk.StringVar(master=self, value="All")

        self.title("Admin — Activity History")
        self.configure(fg_color=BG)
        self.attributes("-fullscreen", True)

        self._build()
        self._refresh_all()

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
            ("dashboard", "🏠", "Dashboard", lambda: self._nav("dashboard")),
            ("products", "📋", "Products", lambda: self._nav("products")),
            ("mostbuyed", "🏆", "Best Products", lambda: self._nav("mostbuyed")),
            ("orders", "📦", "Orders", lambda: self._nav("orders")),
            ("report", "📑", "Reports", lambda: self._nav("report")),
            ("accounts", "👥", "Manage Accounts", lambda: self._nav("accounts")),
            ("history", "🕘", "History", lambda: None),
        ]

        make_sidebar(self, self.user_name, "Administrator", nav, "history")

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
            text="🕘 Activity History",
            font=F_TITLE,
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w")

        tk.Label(
            left_hdr,
            text="Track all recorded actions made by Admin, Cashier, and Inventory users.",
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
        # CONTROL BAR
        # ========================================================
        ctrl = tk.Frame(self.main, bg=BG)
        ctrl.pack(fill="x", padx=22, pady=(12, 8))

        tk.Label(
            ctrl,
            text="Search history:",
            font=F_BOLD,
            bg=BG,
            fg=TEXT
        ).pack(side="left")

        self.search_entry = ctk.CTkEntry(
            ctrl,
            textvariable=self.search_var,
            width=430,
            height=34,
            placeholder_text="Search user, role, action, activity type, description...",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=("Segoe UI", 10),
            corner_radius=8
        )
        self.search_entry.pack(side="left", padx=8)
        self.search_entry.bind("<Return>", lambda event: self._apply_filters())

        gold_btn(
            ctrl,
            "🔍 Search",
            self._apply_filters,
            height=34,
            width=100
        ).pack(side="left", padx=4)

        primary_btn(
            ctrl,
            "🔄 Refresh",
            self._refresh_all,
            height=34,
            width=110
        ).pack(side="right", padx=4)

        gold_btn(
            ctrl,
            "📤 Export CSV",
            self._export_csv,
            height=34,
            width=120
        ).pack(side="right", padx=4)

        # ========================================================
        # SUMMARY CARDS
        # ========================================================
        self.kpi = tk.Frame(self.main, bg=BG)
        self.kpi.pack(fill="x", padx=22, pady=(4, 10))

        # ========================================================
        # FILTER PANEL
        # ========================================================
        self.filter_card = tk.Frame(
            self.main,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.filter_card.pack(fill="x", padx=22, pady=(0, 10))

        self._build_filter_panel()

        # ========================================================
        # BODY GRID
        # ========================================================
        body = tk.Frame(self.main, bg=BG)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        right = tk.Frame(body, bg=BG, width=360)
        right.pack(side="right", fill="both", padx=(6, 0))
        right.pack_propagate(False)

        # ========================================================
        # TABLE CARD
        # ========================================================
        self.table_card = tk.Frame(
            left,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.table_card.pack(fill="both", expand=True)

        table_head = tk.Frame(self.table_card, bg=CARD_BG)
        table_head.pack(fill="x", padx=14, pady=(12, 6))

        tk.Label(
            table_head,
            text="Activity Records",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left")

        tk.Label(
            table_head,
            text="ID • User • Role • Action • Description • Date & Time",
            font=("Segoe UI", 10, "italic"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=12)

        self.result_label = tk.Label(
            table_head,
            text="0 records found",
            font=("Segoe UI", 10, "italic"),
            bg=CARD_BG,
            fg=TEXT
        )
        self.result_label.pack(side="right")

        table_box = tk.Frame(self.table_card, bg=CARD_BG)
        table_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._build_table(table_box)

        # ========================================================
        # DETAILS PANEL
        # ========================================================
        self.details_card = tk.Frame(
            right,
            bg="#FFF8E1",
            highlightbackground=GOLD,
            highlightthickness=1
        )
        self.details_card.pack(fill="both", expand=True)

        self._build_empty_details()

    # ============================================================
    # FILTER PANEL
    # ============================================================
    def _build_filter_panel(self):
        for widget in self.filter_card.winfo_children():
            widget.destroy()

        header = tk.Frame(self.filter_card, bg=SIDEBAR)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Filters",
            font=("Georgia", 12, "bold"),
            bg=SIDEBAR,
            fg=CREAM
        ).pack(side="left", padx=12, pady=8)

        tk.Label(
            header,
            text="Role, Action, and Activity Type filters are based on cleaned history data",
            font=("Segoe UI", 9, "italic"),
            bg=SIDEBAR,
            fg=CREAM
        ).pack(side="left", padx=10)

        body = tk.Frame(self.filter_card, bg=CARD_BG)
        body.pack(fill="x", padx=14, pady=12)

        self._filter_label(body, "Role")
        self.role_combo = ttk.Combobox(
            body,
            textvariable=self.role_var,
            values=["All", "admin", "cashier", "inventory", "unknown"],
            width=17,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.role_combo.pack(side="left", padx=(4, 16))
        self.role_combo.bind("<<ComboboxSelected>>", lambda event: self._apply_filters())

        self._filter_label(body, "Action")
        self.action_combo = ttk.Combobox(
            body,
            textvariable=self.action_var,
            values=["All"],
            width=28,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.action_combo.pack(side="left", padx=(4, 16))
        self.action_combo.bind("<<ComboboxSelected>>", lambda event: self._apply_filters())

        self._filter_label(body, "Activity Type")
        self.activity_type_combo = ttk.Combobox(
            body,
            textvariable=self.activity_type_var,
            values=[
                "All",
                "Orders",
                "Receipts",
                "Inventory",
                "Accounts",
                "Reports",
                "System",
                "General"
            ],
            width=18,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.activity_type_combo.pack(side="left", padx=(4, 16))
        self.activity_type_combo.bind("<<ComboboxSelected>>", lambda event: self._apply_filters())

        primary_btn(
            body,
            "Apply",
            self._apply_filters,
            height=31,
            width=86
        ).pack(side="left", padx=4)

        gold_btn(
            body,
            "Clear",
            self._clear_filters,
            height=31,
            width=78
        ).pack(side="left", padx=4)

    def _filter_label(self, parent, text):
        tk.Label(
            parent,
            text=f"{text}:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left")

    # ============================================================
    # TABLE
    # ============================================================
    def _build_table(self, parent):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "History.Treeview",
            background=CARD_BG,
            fieldbackground=CARD_BG,
            foreground=TEXT,
            rowheight=40,
            font=("Segoe UI", 10)
        )

        style.configure(
            "History.Treeview.Heading",
            background=SIDEBAR,
            foreground=WHITE,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )

        style.map(
            "History.Treeview",
            background=[("selected", GOLD)],
            foreground=[("selected", DARK_RED)]
        )

        cols = (
            "ID",
            "User",
            "Role",
            "Action",
            "Description",
            "Date & Time"
        )

        widths = [65, 150, 105, 170, 570, 180]

        self.tree = ttk.Treeview(
            parent,
            columns=cols,
            show="headings",
            style="History.Treeview"
        )

        for col_name, width in zip(cols, widths):
            self.tree.heading(col_name, text=col_name)
            self.tree.column(col_name, width=width, anchor="center", minwidth=60)

        self.tree.column("User", anchor="w", minwidth=120)
        self.tree.column("Action", anchor="w", minwidth=140)
        self.tree.column("Description", anchor="w", minwidth=350)
        self.tree.column("Date & Time", anchor="center", minwidth=160)

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.tree.xview)

        self.tree.configure(
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

        self.tree.tag_configure("odd", background=ODD_ROW)
        self.tree.tag_configure("even", background=CARD_BG)
        self.tree.tag_configure("admin", foreground=DARK_RED)
        self.tree.tag_configure("cashier", foreground="#117864")
        self.tree.tag_configure("inventory", foreground="#9A6A00")
        self.tree.tag_configure("unknown", foreground=TEXT)

        self.tree.bind("<<TreeviewSelect>>", self._on_select_log)

    # ============================================================
    # SUMMARY CARDS
    # ============================================================
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

    def _load_summary_cards(self):
        for widget in self.kpi.winfo_children():
            widget.destroy()

        role_counts = {
            "admin": 0,
            "cashier": 0,
            "inventory": 0,
            "unknown": 0
        }

        for item in self.all_prepared_logs:
            role = item.get("role", "unknown")
            if role not in role_counts:
                role = "unknown"
            role_counts[role] += 1

        today_count = 0
        today_text = datetime.now().strftime("%b %d, %Y")

        for item in self.all_prepared_logs:
            if str(item.get("date_time", "")).startswith(today_text):
                today_count += 1

        stats = [
            ("🕘 Total Logs", str(len(self.all_prepared_logs)), SIDEBAR, "All recorded activities"),
            ("📅 Today", str(today_count), "#27AE60", "Activities today"),
            ("🛡️ Admin", str(role_counts["admin"]), DARK_RED, "Admin actions"),
            ("🧾 Cashier", str(role_counts["cashier"]), "#117864", "Cashier actions"),
            ("📦 Inventory", str(role_counts["inventory"]), GOLD, "Inventory actions"),
        ]

        for index, (label, value, color, subtext) in enumerate(stats):
            self._make_kpi_card(self.kpi, index, label, value, color, subtext)

    # ============================================================
    # DATA PREPARATION
    # ============================================================
    def _prepare_display_log(self, log):
        raw_role = log.get("actor_role")
        description = log.get("description")
        action_type = log.get("action_type")

        role = normalize_role(raw_role)

        if role == "unknown":
            role = infer_role_from_action(action_type, description)

        username = clean_username(
            log.get("actor_username"),
            role,
            action_type,
            description
        )

        action_label = format_action(action_type)
        activity_type = get_activity_type(action_type, description)
        date_time = fixed_datetime_display(log)

        return {
            "log_id": log.get("log_id", ""),
            "username": username,
            "role": role,
            "role_label": format_role(role),
            "action_label": action_label,
            "action_type": str(action_type or "").strip().upper(),
            "activity_type": activity_type,
            "description": safe_text(description),
            "date_time": date_time,
            "raw": log
        }

    def _fetch_all_logs(self):
        """
        Important:
        Do NOT pass role_filter/action_filter to backend here.
        Old logs may have NULL actor_role, so backend filtering can hide them.
        We fetch all logs first, clean them, then filter in Python.
        """
        self.raw_logs = get_activity_logs(
            search="",
            role_filter="All",
            module_filter="All",
            action_filter="All",
            date_from="",
            date_to="",
            limit=5000
        )

        self.all_prepared_logs = [
            self._prepare_display_log(log)
            for log in self.raw_logs
        ]

    def _load_filter_options(self):
        """
        Builds the Action filter from cleaned display action names,
        not raw database action codes only.
        """
        try:
            raw_actions = set()

            try:
                options = get_filter_options()
                for action in options.get("actions", []):
                    raw_actions.add(str(action or "").strip().upper())
            except Exception:
                pass

            for item in self.all_prepared_logs:
                if item.get("action_type"):
                    raw_actions.add(item["action_type"])

            action_labels = sorted({
                format_action(action)
                for action in raw_actions
                if action
            })

            self.action_combo["values"] = ["All"] + action_labels

            if self.action_var.get() not in self.action_combo["values"]:
                self.action_var.set("All")

        except Exception:
            self.action_combo["values"] = ["All"]
            self.action_var.set("All")

    # ============================================================
    # FILTERING
    # ============================================================
    def _apply_filters(self):
        search = self.search_var.get().strip().lower()
        role_filter = role_filter_value(self.role_var.get())
        action_filter = self.action_var.get().strip()
        activity_type_filter = self.activity_type_var.get().strip()

        filtered = []

        for item in self.all_prepared_logs:
            # Role filter
            if role_filter != "All" and item["role"] != role_filter:
                continue

            # Action filter
            if action_filter and action_filter != "All":
                if item["action_label"] != action_filter:
                    continue

            # Activity type filter
            if activity_type_filter and activity_type_filter != "All":
                if item["activity_type"] != activity_type_filter:
                    continue

            # Search filter
            if search:
                searchable = " ".join([
                    str(item.get("log_id", "")),
                    str(item.get("username", "")),
                    str(item.get("role_label", "")),
                    str(item.get("role", "")),
                    str(item.get("action_label", "")),
                    str(item.get("action_type", "")),
                    str(item.get("activity_type", "")),
                    str(item.get("description", "")),
                    str(item.get("date_time", "")),
                ]).lower()

                if search not in searchable:
                    continue

            filtered.append(item)

        self.prepared_logs = filtered
        self._load_table()
        self._build_empty_details()

    def _load_table(self):
        self.tree.delete(*self.tree.get_children())

        if not self.prepared_logs:
            self.tree.insert(
                "",
                "end",
                values=(
                    "—",
                    "No user found",
                    "—",
                    "—",
                    "No activity logs found. Try changing Role, Action, or Activity Type.",
                    "—"
                ),
                tags=("even",)
            )
            self.result_label.config(text="0 records found")
            return

        for index, item in enumerate(self.prepared_logs):
            base_tag = "odd" if index % 2 else "even"
            role_tag = item["role"] if item["role"] in ("admin", "cashier", "inventory") else "unknown"

            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    item["log_id"],
                    item["username"],
                    item["role_label"],
                    item["action_label"],
                    short_text(item["description"], 125),
                    item["date_time"]
                ),
                tags=(base_tag, role_tag)
            )

        self.result_label.config(text=f"{len(self.prepared_logs)} records found")

    def _refresh_all(self):
        try:
            self._fetch_all_logs()
            self._load_filter_options()
            self._load_summary_cards()
            self._apply_filters()

        except Exception as e:
            messagebox.showerror(
                "History Error",
                f"Unable to load activity logs.\n\n{e}",
                parent=self
            )

    def _clear_filters(self):
        self.search_var.set("")
        self.role_var.set("All")
        self.action_var.set("All")
        self.activity_type_var.set("All")
        self._apply_filters()

    # ============================================================
    # DETAILS PANEL
    # ============================================================
    def _clear_details(self):
        for widget in self.details_card.winfo_children():
            widget.destroy()

    def _build_empty_details(self):
        self._clear_details()

        tk.Label(
            self.details_card,
            text="📌 Selected Activity",
            font=("Segoe UI", 13, "bold"),
            bg="#FFF8E1",
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(14, 6))

        tk.Label(
            self.details_card,
            text="Select a record from the table to view the full activity details.",
            font=("Segoe UI", 10),
            bg="#FFF8E1",
            fg=TEXT,
            wraplength=315,
            justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 12))

        guide_items = [
            ("Role Filter", "Admin, Cashier, and Inventory now work even for older logs with missing role data."),
            ("Action Filter", "Uses readable action names like Created Order, Updated Account, and Edited Product."),
            ("Activity Type", "Groups logs into Orders, Receipts, Inventory, Accounts, Reports, System, and General."),
        ]

        for title, desc in guide_items:
            box = tk.Frame(
                self.details_card,
                bg="#FFFDF2",
                highlightbackground="#E6C76E",
                highlightthickness=1
            )
            box.pack(fill="x", padx=12, pady=5)

            tk.Label(
                box,
                text=title,
                font=("Segoe UI", 9, "bold"),
                bg="#FFFDF2",
                fg=DARK_RED
            ).pack(anchor="w", padx=10, pady=(7, 0))

            tk.Label(
                box,
                text=desc,
                font=("Segoe UI", 9),
                bg="#FFFDF2",
                fg=TEXT,
                wraplength=300,
                justify="left"
            ).pack(anchor="w", padx=10, pady=(0, 7))

    def _detail_row(self, parent, title, value):
        box = tk.Frame(
            parent,
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
            text=safe_text(value),
            font=("Segoe UI", 10),
            bg="#FFFDF2",
            fg=TEXT,
            wraplength=310,
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 7))

    def _on_select_log(self, event=None):
        selected = self.tree.selection()

        if not selected:
            return

        try:
            index = int(selected[0])
        except Exception:
            return

        if index < 0 or index >= len(self.prepared_logs):
            return

        item = self.prepared_logs[index]
        self.selected_log = item

        self._clear_details()

        tk.Label(
            self.details_card,
            text="📌 Selected Activity",
            font=("Segoe UI", 13, "bold"),
            bg="#FFF8E1",
            fg=DARK_RED
        ).pack(anchor="w", padx=14, pady=(14, 3))

        tk.Label(
            self.details_card,
            text=f"{item['role_label']} Action",
            font=("Segoe UI", 10, "italic"),
            bg="#FFF8E1",
            fg=role_color(item["role"])
        ).pack(anchor="w", padx=14, pady=(0, 10))

        self._detail_row(self.details_card, "ID", item["log_id"])
        self._detail_row(self.details_card, "User", item["username"])
        self._detail_row(self.details_card, "Role", item["role_label"])
        self._detail_row(self.details_card, "Action", item["action_label"])
        self._detail_row(self.details_card, "Activity Type", item["activity_type"])
        self._detail_row(self.details_card, "Description", item["description"])
        self._detail_row(self.details_card, "Date & Time", item["date_time"])

    # ============================================================
    # EXPORT
    # ============================================================
    def _export_csv(self):
        if not getattr(self, "prepared_logs", []):
            messagebox.showinfo(
                "No Data",
                "There are no logs to export.",
                parent=self
            )
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile=f"activity_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)

                writer.writerow([
                    "ID",
                    "User",
                    "Role",
                    "Action",
                    "Activity Type",
                    "Description",
                    "Date & Time"
                ])

                for item in self.prepared_logs:
                    writer.writerow([
                        item["log_id"],
                        item["username"],
                        item["role_label"],
                        item["action_label"],
                        item["activity_type"],
                        item["description"],
                        item["date_time"]
                    ])

            messagebox.showinfo(
                "Export Successful",
                "Activity history exported successfully.",
                parent=self
            )

        except Exception as e:
            messagebox.showerror(
                "Export Error",
                f"Failed to export CSV.\n\nError: {e}",
                parent=self
            )


# ============================================================
# COMPATIBILITY
# ============================================================
class AdminHistoryPage(tk.Frame):
    """
    Compatibility only.
    Use AdminHistory for the full navigation module.
    """

    def __init__(self, parent, current_user=None):
        super().__init__(parent, bg=BG)

        user_name = "Admin"

        if isinstance(current_user, dict):
            user_name = current_user.get("username", "Admin")

        tk.Label(
            self,
            text="Please open AdminHistory as a full module.",
            font=F_HEAD,
            bg=BG,
            fg=DARK_RED
        ).pack(pady=30)

        primary_btn(
            self,
            "Open History",
            lambda: AdminHistory(user_name).mainloop(),
            height=38,
            width=180
        ).pack()


def create_history_page(parent, current_user=None):
    return AdminHistoryPage(parent, current_user=current_user)


if __name__ == "__main__":
    AdminHistory("Admin").mainloop()