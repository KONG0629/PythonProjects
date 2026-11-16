"""
admin/manageAccounts.py

UI upgraded to match Admin Dashboard style.

Functional logic preserved:
- Add account
- Edit account
- Deactivate account
- Restore account
- Admin credential verification
- Password security validation
- Username validation
- Role and status filtering
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from theme import *
from databases.db import get_connection

from databases.auth_backend import (
    get_all_users,
    get_user_by_id,
    username_exists,
    add_user,
    update_user,
    delete_user,
    restore_user
)

ctk.set_appearance_mode("light")


# ============================================================
# HELPERS
# ============================================================
def mask_password(password):
    if not password:
        return ""
    return "●" * len(str(password))


def format_datetime(value):
    if not value:
        return "—"
    return str(value)[:16]


def check_password_security(password):
    errors = []

    if len(password) < 8:
        errors.append("• At least 8 characters")

    if not re.search(r"[a-z]", password):
        errors.append("• At least 1 lowercase letter")

    if not re.search(r"[A-Z]", password):
        errors.append("• At least 1 uppercase letter")

    if not re.search(r"[0-9]", password):
        errors.append("• At least 1 number")

    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("• At least 1 special character")

    return errors


def check_username(username):
    if len(username) < 4:
        return "Username must be at least 4 characters long."

    if not re.fullmatch(r"[A-Za-z0-9_.]+", username):
        return "Username can only contain letters, numbers, underscore, and dot."

    return None


def verify_admin_credentials(username, password):
    """
    Checks if the entered credential belongs to an ACTIVE ADMIN account.
    """
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT user_id, full_name, username, role, status
            FROM users
            WHERE username = %s
              AND password = %s
              AND role = 'admin'
              AND status = 'active'
            LIMIT 1
            """,
            (username, password)
        )

        return cursor.fetchone()

    except Exception as e:
        print("Admin credential verification error:", e)
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def touch_user_date(user_id):
    """
    Updates the displayed date of the account after editing.
    Your table currently uses created_at, so this updates created_at.
    """
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET created_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
            """,
            (user_id,)
        )

        conn.commit()
        return True

    except Exception as e:
        print("Touch user date error:", e)

        if conn:
            conn.rollback()

        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# MANAGE ACCOUNTS CLASS
# ============================================================
class ManageAccounts(ctk.CTk):
    def __init__(self, user_name="Admin", admin_id=None):
        super().__init__()

        self.user_name = user_name
        self.admin_id = admin_id

        self.title("Admin — Manage Accounts")
        self.configure(fg_color=BG)
        self.attributes("-fullscreen", True)

        self._build()

    # ============================================================
    # CENTER WINDOW
    # ============================================================
    def _center_window(self, win, width, height):
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

    # ============================================================
    # ADMIN CREDENTIAL CONFIRMATION
    # ============================================================
    def _admin_credential_dialog(self, action_title="Admin Security Login"):
        result = {}

        win = ctk.CTkToplevel(self)
        win.title(action_title)
        win.geometry("500x430")
        win.resizable(False, False)
        win.configure(fg_color=BG)

        win.transient(self)
        win.grab_set()
        win.lift()
        win.focus_force()

        self._center_window(win, 500, 430)

        banner = tk.Frame(win, bg=SIDEBAR, height=60)
        banner.pack(side="top", fill="x")
        banner.pack_propagate(False)

        tk.Label(
            banner,
            text="🔐 Admin Security Login",
            font=("Georgia", 16, "bold"),
            bg=SIDEBAR,
            fg=CREAM
        ).pack(side="left", padx=22, pady=14)

        container = tk.Frame(win, bg=BG)
        container.pack(fill="both", expand=True, padx=24, pady=20)

        body = tk.Frame(
            container,
            bg=CREAM,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        body.pack(fill="both", expand=True)

        tk.Label(
            body,
            text="Please login using the active admin credentials.",
            font=F_BODY,
            bg=CREAM,
            fg=TEXT,
            justify="left"
        ).pack(anchor="w", padx=22, pady=(22, 10))

        tk.Label(
            body,
            text="This security check is required before you can continue.",
            font=F_SMALL,
            bg=CREAM,
            fg="#7D4E00",
            justify="left"
        ).pack(anchor="w", padx=22, pady=(0, 16))

        admin_username_var = tk.StringVar(master=win)
        admin_password_var = tk.StringVar(master=win)

        tk.Label(
            body,
            text="Admin Username",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w", padx=22, pady=(0, 4))

        e_username = ctk.CTkEntry(
            body,
            textvariable=admin_username_var,
            height=40,
            placeholder_text="Enter admin username",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=F_BODY,
            corner_radius=8
        )
        e_username.pack(fill="x", padx=22, pady=(0, 12))

        tk.Label(
            body,
            text="Admin Password",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w", padx=22, pady=(0, 4))

        pass_row = tk.Frame(body, bg=CREAM)
        pass_row.pack(fill="x", padx=22, pady=(0, 12))
        pass_row.columnconfigure(0, weight=1)

        e_password = ctk.CTkEntry(
            pass_row,
            textvariable=admin_password_var,
            height=40,
            placeholder_text="Enter admin password",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=F_BODY,
            corner_radius=8,
            show="●"
        )
        e_password.grid(row=0, column=0, sticky="ew")

        show_password = tk.BooleanVar(master=win, value=False)

        def toggle_password():
            e_password.configure(show="" if show_password.get() else "●")

        tk.Checkbutton(
            pass_row,
            text="Show",
            variable=show_password,
            bg=CREAM,
            fg=TEXT,
            font=F_SMALL,
            command=toggle_password
        ).grid(row=0, column=1, padx=(8, 0))

        btns = tk.Frame(body, bg=CREAM)
        btns.pack(side="bottom", fill="x", padx=22, pady=(8, 22))

        def confirm_credentials():
            admin_username = admin_username_var.get().strip()
            admin_password = admin_password_var.get().strip()

            if not admin_username or not admin_password:
                messagebox.showwarning(
                    "Admin Security Login",
                    "Please enter the admin username and password.",
                    parent=win
                )
                return

            admin_user = verify_admin_credentials(admin_username, admin_password)

            if not admin_user:
                messagebox.showerror(
                    "Access Denied",
                    "Invalid admin credentials.\n\nOnly an active admin account can authorize this action.",
                    parent=win
                )
                return

            result.update(admin_user)
            win.destroy()

        ctk.CTkButton(
            btns,
            text="✅ Login Admin",
            command=confirm_credentials,
            height=44,
            fg_color=GOLD,
            hover_color=DARK_RED,
            text_color=DARK_RED,
            font=("Segoe UI", 13, "bold"),
            corner_radius=8
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            btns,
            text="✖ Cancel",
            command=win.destroy,
            height=44,
            fg_color="#B03A2E",
            hover_color="#922B21",
            text_color=WHITE,
            font=("Segoe UI", 13, "bold"),
            corner_radius=8
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

        win.bind("<Return>", lambda event: confirm_credentials())
        win.bind("<Escape>", lambda event: win.destroy())

        e_username.focus_set()
        win.wait_window()

        return result if result else None

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
                app = ManageAccounts(self.user_name, self.admin_id)


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

        make_sidebar(self, self.user_name, "Administrator", nav, "accounts")

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
            text="👥 Manage Accounts",
            font=F_TITLE,
            bg=CREAM,
            fg=DARK_RED
        ).pack(anchor="w")

        tk.Label(
            left_hdr,
            text="Create, update, deactivate, and restore system user accounts.",
            font=("Segoe UI", 10, "italic"),
            bg=CREAM,
            fg=TEXT
        ).pack(anchor="w")

        right_hdr = tk.Frame(hdr, bg=CREAM)
        right_hdr.pack(side="right", padx=20, pady=10)

        from datetime import datetime

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
        # KPI CARDS — DASHBOARD STYLE
        # ========================================================
        self.kpi_frame = tk.Frame(self.main, bg=BG)
        self.kpi_frame.pack(fill="x", padx=22, pady=(14, 10))

        # ========================================================
        # QUICK ACTIONS BAR — DASHBOARD STYLE
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
            text="Account Tools",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left", padx=14, pady=12)

        tk.Label(
            action_card,
            text="Admin verification is required for creating, editing, deactivating, and restoring accounts.",
            font=("Segoe UI", 9, "italic"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=10)

        gold_btn(
            action_card,
            "➕ Add Account",
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

        danger_btn(
            action_card,
            "🚫 Deactivate",
            self._delete,
            height=34,
            width=130
        ).pack(side="right", padx=4, pady=10)

        try:
            success_btn(
                action_card,
                "♻️ Restore",
                self._restore,
                height=34,
                width=110
            ).pack(side="right", padx=4, pady=10)
        except NameError:
            primary_btn(
                action_card,
                "♻️ Restore",
                self._restore,
                height=34,
                width=110
            ).pack(side="right", padx=4, pady=10)

        # ========================================================
        # FILTER PANEL — CLEANER DASHBOARD STYLE
        # ========================================================
        filter_card = tk.Frame(
            self.main,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        filter_card.pack(fill="x", padx=22, pady=(0, 10))

        self.role_var = tk.StringVar(master=self, value="All")
        self.status_var = tk.StringVar(master=self, value="Active")

        tk.Label(
            filter_card,
            text="Filters",
            font=F_HEAD,
            bg=CARD_BG,
            fg=DARK_RED
        ).pack(side="left", padx=14, pady=12)

        tk.Label(
            filter_card,
            text="Role:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(8, 4))

        for role in ("All", "admin", "cashier", "inventory"):
            tk.Radiobutton(
                filter_card,
                text=role.capitalize(),
                variable=self.role_var,
                value=role,
                font=F_BODY,
                bg=CARD_BG,
                fg=DARK_RED,
                selectcolor=GOLD,
                activebackground=CARD_BG,
                command=self._load
            ).pack(side="left", padx=5)

        tk.Label(
            filter_card,
            text="Status:",
            font=F_BOLD,
            bg=CARD_BG,
            fg=TEXT
        ).pack(side="left", padx=(24, 4))

        for status in ("Active", "Inactive", "All"):
            tk.Radiobutton(
                filter_card,
                text=status,
                variable=self.status_var,
                value=status,
                font=F_BODY,
                bg=CARD_BG,
                fg=DARK_RED,
                selectcolor=GOLD,
                activebackground=CARD_BG,
                command=self._load
            ).pack(side="left", padx=5)

        primary_btn(
            filter_card,
            "🔄 Refresh",
            self._load,
            height=34,
            width=110
        ).pack(side="right", padx=12, pady=10)

        # ========================================================
        # TABLE TITLE
        # ========================================================
        table_title = tk.Frame(self.main, bg=BG)
        table_title.pack(fill="x", padx=22)

        tk.Label(
            table_title,
            text="Account Records",
            font=F_HEAD,
            bg=BG,
            fg=DARK_RED
        ).pack(side="left")

        tk.Label(
            table_title,
            text="Admin, cashier, and inventory accounts",
            font=("Segoe UI", 10, "italic"),
            bg=BG,
            fg=TEXT
        ).pack(side="left", padx=10)

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
            "Acc.Treeview",
            background=CARD_BG,
            fieldbackground=CARD_BG,
            foreground=TEXT,
            rowheight=40,
            font=("Segoe UI", 11)
        )

        style.configure(
            "Acc.Treeview.Heading",
            background=SIDEBAR,
            foreground=WHITE,
            font=("Segoe UI", 11, "bold"),
            relief="flat"
        )

        style.map(
            "Acc.Treeview",
            background=[("selected", GOLD)],
            foreground=[("selected", DARK_RED)]
        )

        cols = ("ID", "Username", "Full Name", "Role", "Status", "Password", "Date")
        widths = [55, 160, 240, 120, 110, 170, 160]

        self.tree = ttk.Treeview(
            tbl,
            columns=cols,
            show="headings",
            style="Acc.Treeview"
        )

        for col_name, width in zip(cols, widths):
            self.tree.heading(col_name, text=col_name)
            self.tree.column(col_name, width=width, anchor="center", minwidth=40)

        vsb = ttk.Scrollbar(tbl, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbl, orient="horizontal", command=self.tree.xview)

        self.tree.configure(
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

        self.tree.tag_configure("admin", background="#FCE4EC")
        self.tree.tag_configure("cashier", background="#EBF5FB")
        self.tree.tag_configure("inventory", background="#EAFAF1")
        self.tree.tag_configure("inactive", background="#FDECEA", foreground="#B03A2E")

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

    def _update_kpis(self, users):
        for widget in self.kpi_frame.winfo_children():
            widget.destroy()

        valid_users = [
            user for user in users
            if str(user["role"]).lower() in ("admin", "cashier", "inventory")
        ]

        total_accounts = len(valid_users)
        active_accounts = sum(1 for user in valid_users if str(user["status"]).lower() == "active")
        inactive_accounts = sum(1 for user in valid_users if str(user["status"]).lower() == "inactive")
        admin_accounts = sum(1 for user in valid_users if str(user["role"]).lower() == "admin")
        staff_accounts = sum(
            1 for user in valid_users
            if str(user["role"]).lower() in ("cashier", "inventory")
        )

        stats = [
            ("👥 Total Accounts", str(total_accounts), SIDEBAR, "All system users"),
            ("✅ Active", str(active_accounts), "#27AE60", "Can access system"),
            ("🚫 Inactive", str(inactive_accounts), "#B03A2E", "Login disabled"),
            ("🔐 Admins", str(admin_accounts), "#6C3483", "Full access"),
            ("🧑‍💼 Staff", str(staff_accounts), GOLD, "Cashier / inventory"),
        ]

        for index, (label, value, color, subtext) in enumerate(stats):
            self._make_kpi_card(index, label, value, color, subtext)

    # ============================================================
    # LOAD DATA
    # ============================================================
    def _load(self):
        self.tree.delete(*self.tree.get_children())

        selected_role = self.role_var.get()
        selected_status = self.status_var.get().lower()

        users = get_all_users()

        self._update_kpis(users)

        for user in users:
            role = str(user["role"]).lower()
            status = str(user["status"]).lower()

            if role not in ("admin", "cashier", "inventory"):
                continue

            if selected_role != "All" and role != selected_role:
                continue

            if selected_status != "all" and status != selected_status:
                continue

            tag = "inactive" if status == "inactive" else role

            self.tree.insert(
                "",
                "end",
                values=(
                    user["user_id"],
                    user["username"],
                    user["full_name"],
                    role.capitalize(),
                    status.capitalize(),
                    mask_password(user["password"]),
                    format_datetime(user["created_at"])
                ),
                tags=(tag,)
            )

    # ============================================================
    # ACCOUNT FORM
    # ============================================================
    def _account_form(self, title, defaults=None):
        result = {}
        is_edit = defaults is not None

        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("800x590")
        win.resizable(False, False)
        win.configure(fg_color=BG)

        win.transient(self)
        win.grab_set()
        win.lift()
        win.focus_force()

        self._center_window(win, 800, 590)

        banner = tk.Frame(win, bg=SIDEBAR, height=58)
        banner.pack(side="top", fill="x")
        banner.pack_propagate(False)

        icon = "➕" if "Add" in title else "✏️"

        tk.Label(
            banner,
            text=f"{icon} {title}",
            font=("Georgia", 16, "bold"),
            bg=SIDEBAR,
            fg=CREAM
        ).pack(side="left", padx=20, pady=12)

        button_area = tk.Frame(win, bg=BG, height=70)
        button_area.pack(side="bottom", fill="x", padx=24, pady=(0, 16))
        button_area.pack_propagate(False)

        form = tk.Frame(
            win,
            bg=CREAM,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        form.pack(side="top", fill="both", expand=True, padx=24, pady=16)

        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        current_password = str(defaults.get("password", "")) if defaults else ""

        full_name_var = tk.StringVar(
            master=win,
            value=defaults.get("full_name", "") if defaults else ""
        )
        username_var = tk.StringVar(
            master=win,
            value=defaults.get("username", "") if defaults else ""
        )
        password_var = tk.StringVar(
            master=win,
            value=current_password if is_edit else ""
        )
        confirm_password_var = tk.StringVar(
            master=win,
            value=current_password if is_edit else ""
        )
        role_var = tk.StringVar(
            master=win,
            value=defaults.get("role", "cashier") if defaults else "cashier"
        )
        status_var = tk.StringVar(
            master=win,
            value=defaults.get("status", "active") if defaults else "active"
        )

        tk.Label(
            form,
            text="Full Name",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED,
            anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 4))

        e_name = ctk.CTkEntry(
            form,
            textvariable=full_name_var,
            height=38,
            placeholder_text="e.g. Maria Santos",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=F_BODY,
            corner_radius=8
        )
        e_name.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 10))

        tk.Label(
            form,
            text="Username",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED,
            anchor="w"
        ).grid(row=0, column=1, sticky="ew", padx=22, pady=(18, 4))

        e_user = ctk.CTkEntry(
            form,
            textvariable=username_var,
            height=38,
            placeholder_text="e.g. cashier_01",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=F_BODY,
            corner_radius=8
        )
        e_user.grid(row=1, column=1, sticky="ew", padx=22, pady=(0, 10))

        tk.Label(
            form,
            text="Password",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED,
            anchor="w"
        ).grid(row=2, column=0, sticky="ew", padx=22, pady=(4, 4))

        pass_frame = tk.Frame(form, bg=CREAM)
        pass_frame.grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 10))
        pass_frame.columnconfigure(0, weight=1)

        e_pass = ctk.CTkEntry(
            pass_frame,
            textvariable=password_var,
            height=38,
            placeholder_text="Enter password",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=F_BODY,
            corner_radius=8,
            show="●"
        )
        e_pass.grid(row=0, column=0, sticky="ew")

        tk.Label(
            form,
            text="Confirm Password",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED,
            anchor="w"
        ).grid(row=2, column=1, sticky="ew", padx=22, pady=(4, 4))

        e_confirm = ctk.CTkEntry(
            form,
            textvariable=confirm_password_var,
            height=38,
            placeholder_text="Re-type password",
            fg_color=WHITE,
            border_color=GOLD,
            border_width=1,
            text_color=TEXT,
            font=F_BODY,
            corner_radius=8,
            show="●"
        )
        e_confirm.grid(row=3, column=1, sticky="ew", padx=22, pady=(0, 10))

        show_password = tk.BooleanVar(master=win, value=False)

        def toggle_password():
            show_value = "" if show_password.get() else "●"
            e_pass.configure(show=show_value)
            e_confirm.configure(show=show_value)

        tk.Checkbutton(
            pass_frame,
            text="Show",
            variable=show_password,
            bg=CREAM,
            fg=TEXT,
            font=F_SMALL,
            command=toggle_password
        ).grid(row=0, column=1, padx=(8, 0))

        tk.Label(
            form,
            text="Role",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED,
            anchor="w"
        ).grid(row=4, column=0, sticky="ew", padx=22, pady=(4, 4))

        role_frame = tk.Frame(form, bg=CREAM)
        role_frame.grid(row=5, column=0, sticky="ew", padx=22, pady=(0, 10))

        role_options = [
            ("Admin", "admin"),
            ("Inventory", "inventory"),
            ("Cashier", "cashier"),
        ]

        for label, value in role_options:
            tk.Radiobutton(
                role_frame,
                text=label,
                variable=role_var,
                value=value,
                font=F_BODY,
                bg=CREAM,
                fg=TEXT,
                selectcolor=GOLD,
                activebackground=CREAM
            ).pack(side="left", padx=(0, 18))

        tk.Label(
            form,
            text="Status",
            font=F_BOLD,
            bg=CREAM,
            fg=DARK_RED,
            anchor="w"
        ).grid(row=4, column=1, sticky="ew", padx=22, pady=(4, 4))

        status_frame = tk.Frame(form, bg=CREAM)
        status_frame.grid(row=5, column=1, sticky="ew", padx=22, pady=(0, 10))

        tk.Radiobutton(
            status_frame,
            text="Active",
            variable=status_var,
            value="active",
            font=F_BODY,
            bg=CREAM,
            fg=TEXT,
            selectcolor=GOLD,
            activebackground=CREAM
        ).pack(side="left", padx=(0, 24))

        tk.Radiobutton(
            status_frame,
            text="Inactive",
            variable=status_var,
            value="inactive",
            font=F_BODY,
            bg=CREAM,
            fg=TEXT,
            selectcolor=GOLD,
            activebackground=CREAM
        ).pack(side="left")

        notice_text = (
            "All selected account credentials are loaded in the fields."
            if is_edit else
            "Password must contain uppercase, lowercase, number, and special character."
        )

        tk.Label(
            form,
            text=notice_text,
            font=F_SMALL,
            bg=CREAM,
            fg="#7D4E00",
            anchor="w",
            justify="left"
        ).grid(row=6, column=0, columnspan=2, sticky="ew", padx=22, pady=(8, 10))

        def save_form():
            full_name = full_name_var.get().strip()
            username = username_var.get().strip()
            password = password_var.get().strip()
            confirm_password = confirm_password_var.get().strip()
            role = role_var.get().strip().lower()
            status = status_var.get().strip().lower()

            if not full_name or not username or not password or not confirm_password:
                messagebox.showwarning(
                    "Input Error",
                    "All fields are required.",
                    parent=win
                )
                return

            username_error = check_username(username)

            if username_error:
                messagebox.showwarning(
                    "Invalid Username",
                    username_error,
                    parent=win
                )
                return

            if role not in ("admin", "inventory", "cashier"):
                messagebox.showwarning(
                    "Input Error",
                    "Please select Admin, Inventory, or Cashier only.",
                    parent=win
                )
                return

            if status not in ("active", "inactive"):
                messagebox.showwarning(
                    "Input Error",
                    "Please select Active or Inactive status.",
                    parent=win
                )
                return

            exclude_id = defaults["user_id"] if defaults else None

            if username_exists(username, exclude_user_id=exclude_id):
                messagebox.showwarning(
                    "Duplicate Username",
                    f"Username '{username}' already exists.",
                    parent=win
                )
                return

            if password != confirm_password:
                messagebox.showwarning(
                    "Password Error",
                    "Password and Confirm Password do not match.",
                    parent=win
                )
                return

            password_errors = check_password_security(password)

            if password_errors:
                messagebox.showwarning(
                    "Password Requirements",
                    "Please change the password according to security requirements.\n\n"
                    "The password must have:\n\n"
                    "• At least 8 characters\n"
                    "• At least 1 lowercase letter\n"
                    "• At least 1 uppercase letter\n"
                    "• At least 1 number\n"
                    "• At least 1 special character\n\n"
                    "Example: Chels@123",
                    parent=win
                )
                return

            result.update(
                {
                    "full_name": full_name,
                    "username": username,
                    "password": password,
                    "role": role,
                    "status": status
                }
            )

            win.destroy()

        ctk.CTkButton(
            button_area,
            text="💾 Save Account",
            command=save_form,
            height=44,
            fg_color=GOLD,
            hover_color=DARK_RED,
            text_color=DARK_RED,
            font=("Segoe UI", 13, "bold"),
            corner_radius=8
        ).pack(side="left", fill="x", expand=True, padx=(0, 8), pady=10)

        ctk.CTkButton(
            button_area,
            text="✖ Cancel",
            command=win.destroy,
            height=44,
            fg_color="#B03A2E",
            hover_color="#922B21",
            text_color=WHITE,
            font=("Segoe UI", 13, "bold"),
            corner_radius=8
        ).pack(side="left", fill="x", expand=True, padx=(8, 0), pady=10)

        e_name.focus_set()
        win.wait_window()

        return result if result else None

    # ============================================================
    # ADD ACCOUNT
    # ============================================================
    def _add_dlg(self):
        data = self._account_form("Add Account")

        if not data:
            return

        admin_auth = self._admin_credential_dialog("Confirm Add Account")

        if not admin_auth:
            messagebox.showinfo(
                "Cancelled",
                "Add account was cancelled because admin verification was not completed.",
                parent=self
            )
            return

        authorized_admin_id = admin_auth.get("user_id", self.admin_id)

        user_id = add_user(
            data["full_name"],
            data["username"],
            data["password"],
            data["role"],
            authorized_admin_id
        )

        if user_id:
            if data["status"] == "inactive":
                update_user(
                    user_id,
                    data["full_name"],
                    data["username"],
                    data["password"],
                    data["role"],
                    data["status"],
                    authorized_admin_id
                )
                touch_user_date(user_id)

            messagebox.showinfo(
                "Added",
                f"Account '{data['username']}' created successfully.",
                parent=self
            )
            self._load()

        else:
            messagebox.showerror(
                "Add Failed",
                "Unable to add account. Username may already exist.",
                parent=self
            )

    # ============================================================
    # EDIT ACCOUNT
    # ============================================================
    def _edit_dlg(self):
        selected_row = self.tree.focus()

        if not selected_row:
            messagebox.showwarning(
                "Edit",
                "Select an account to edit.",
                parent=self
            )
            return

        user_id = int(self.tree.item(selected_row, "values")[0])
        user = get_user_by_id(user_id)

        if not user:
            messagebox.showerror(
                "Edit",
                "Selected account was not found.",
                parent=self
            )
            return

        admin_auth = self._admin_credential_dialog("Login Admin Before Editing")

        if not admin_auth:
            messagebox.showinfo(
                "Cancelled",
                "Edit account was cancelled because admin login was not completed.",
                parent=self
            )
            return

        data = self._account_form("Edit Account", user)

        if not data:
            return

        authorized_admin_id = admin_auth.get("user_id", self.admin_id)

        success = update_user(
            user_id,
            data["full_name"],
            data["username"],
            data["password"],
            data["role"],
            data["status"],
            authorized_admin_id
        )

        if success:
            touch_user_date(user_id)

            messagebox.showinfo(
                "Updated",
                "Account updated successfully.",
                parent=self
            )
            self._load()
        else:
            messagebox.showerror(
                "Update Failed",
                "Unable to update account. Username may already exist.",
                parent=self
            )

    # ============================================================
    # DEACTIVATE ACCOUNT
    # ============================================================
    def _delete(self):
        selected_row = self.tree.focus()

        if not selected_row:
            messagebox.showwarning(
                "Deactivate",
                "Select an account to deactivate.",
                parent=self
            )
            return

        values = self.tree.item(selected_row, "values")
        user_id = int(values[0])
        username = values[1]
        status = values[4].lower()

        if status == "inactive":
            messagebox.showinfo(
                "Deactivate",
                "This account is already inactive.",
                parent=self
            )
            return

        if self.admin_id is not None and user_id == self.admin_id:
            messagebox.showwarning(
                "Deactivate",
                "You cannot deactivate your own active admin account while using the system.",
                parent=self
            )
            return

        confirm = messagebox.askyesno(
            "Deactivate",
            f"Deactivate account '{username}'?\n\nThe user will not be able to log in.",
            parent=self
        )

        if not confirm:
            return

        admin_auth = self._admin_credential_dialog("Confirm Deactivate Account")

        if not admin_auth:
            messagebox.showinfo(
                "Cancelled",
                "Deactivate account was cancelled because admin verification was not completed.",
                parent=self
            )
            return

        authorized_admin_id = admin_auth.get("user_id", self.admin_id)

        success = delete_user(user_id, authorized_admin_id)

        if success:
            touch_user_date(user_id)

            messagebox.showinfo(
                "Deactivated",
                f"Account '{username}' has been deactivated.",
                parent=self
            )
            self._load()
        else:
            messagebox.showerror(
                "Deactivate Failed",
                "Unable to deactivate account.",
                parent=self
            )

    # ============================================================
    # RESTORE ACCOUNT
    # ============================================================
    def _restore(self):
        selected_row = self.tree.focus()

        if not selected_row:
            messagebox.showwarning(
                "Restore",
                "Select an account to restore.",
                parent=self
            )
            return

        values = self.tree.item(selected_row, "values")
        user_id = int(values[0])
        username = values[1]
        status = values[4].lower()

        if status == "active":
            messagebox.showinfo(
                "Restore",
                "This account is already active.",
                parent=self
            )
            return

        confirm = messagebox.askyesno(
            "Restore",
            f"Restore account '{username}'?",
            parent=self
        )

        if not confirm:
            return

        admin_auth = self._admin_credential_dialog("Confirm Restore Account")

        if not admin_auth:
            messagebox.showinfo(
                "Cancelled",
                "Restore account was cancelled because admin verification was not completed.",
                parent=self
            )
            return

        authorized_admin_id = admin_auth.get("user_id", self.admin_id)

        success = restore_user(user_id, authorized_admin_id)

        if success:
            touch_user_date(user_id)

            messagebox.showinfo(
                "Restored",
                f"Account '{username}' has been restored.",
                parent=self
            )
            self._load()
        else:
            messagebox.showerror(
                "Restore Failed",
                "Unable to restore account.",
                parent=self
            )


# ============================================================
# RUN DIRECTLY FOR TESTING
# ============================================================
if __name__ == "__main__":
    ManageAccounts("Admin").mainloop()