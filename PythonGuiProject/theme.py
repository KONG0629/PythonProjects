"""
theme.py — Shared palette, fonts, sidebar, helpers.

Place in the project ROOT folder.
All modules do:

from theme import *
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

import os
import runpy


# ============================================================
# PROJECT PATHS
# ============================================================
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGIN_FILE = os.path.join(PROJECT_DIR, "logins", "login.py")


# ============================================================
# PALETTE
# ============================================================
BG       = "#FDF6EC"
SIDEBAR  = "#7B1C1C"
SIDE_ACT = "#C8960C"
SIDE_HV  = "#4A0E0E"
GOLD     = "#C8960C"
CREAM    = "#FAF0DC"
DARK_RED = "#4A0E0E"
TEXT     = "#2C1A00"
WHITE    = "#FFFFFF"
CARD     = "#FFFFFF"
CARD_BG  = "#FFFFFF"
BORDER   = "#E8D5B0"
ODD_ROW  = "#FFF8F0"
ERR      = "#B03A2E"
GREEN    = "#1E8449"


# ============================================================
# FONTS
# ============================================================
FT = ("Georgia", 20, "bold")
FH = ("Georgia", 14, "bold")
FB = ("Segoe UI", 11, "bold")
FN = ("Segoe UI", 11)
FS = ("Segoe UI", 9)
FK = ("Segoe UI", 11, "bold")

F_TITLE = FT
F_HEAD = FH
F_BOLD = FB
F_BODY = FN
F_SMALL = FS


# ============================================================
# BUTTON HELPERS
# ============================================================
def _b(parent, text, cmd, fc, hc, tc=WHITE, **kw):
    return ctk.CTkButton(
        parent,
        text=text,
        command=cmd,
        fg_color=fc,
        hover_color=hc,
        text_color=tc,
        font=FK,
        corner_radius=8,
        **kw
    )


def primary_btn(parent, text, cmd, **kw):
    return _b(parent, text, cmd, SIDEBAR, SIDE_HV, WHITE, **kw)


def gold_btn(parent, text, cmd, **kw):
    return _b(parent, text, cmd, GOLD, "#A07808", DARK_RED, **kw)


def danger_btn(parent, text, cmd, **kw):
    return _b(parent, text, cmd, "#B03A2E", "#7B241C", WHITE, **kw)


def success_btn(parent, text, cmd, **kw):
    return _b(parent, text, cmd, GREEN, "#145A32", WHITE, **kw)


def btn(parent, text, cmd, **kw):
    return primary_btn(parent, text, cmd, **kw)


def btn_gold(parent, text, cmd, **kw):
    return gold_btn(parent, text, cmd, **kw)


def btn_red(parent, text, cmd, **kw):
    return danger_btn(parent, text, cmd, **kw)


def btn_green(parent, text, cmd, **kw):
    return success_btn(parent, text, cmd, **kw)


# ============================================================
# TREEVIEW STYLE HELPERS
# ============================================================
_styles_done = set()


def apply_tree_style(name):
    if name in _styles_done:
        return

    style = ttk.Style()

    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        f"{name}.Treeview",
        background=CARD_BG,
        fieldbackground=CARD_BG,
        foreground=TEXT,
        rowheight=38,
        font=("Segoe UI", 11)
    )

    style.configure(
        f"{name}.Treeview.Heading",
        background=SIDEBAR,
        foreground=WHITE,
        font=("Segoe UI", 11, "bold"),
        relief="flat"
    )

    style.map(
        f"{name}.Treeview",
        background=[("selected", GOLD)],
        foreground=[("selected", DARK_RED)]
    )

    _styles_done.add(name)


def tree_widget(parent, columns, widths, height=None, style_name="Base"):
    apply_tree_style(style_name)

    kw = {"height": height} if height else {}

    tv = ttk.Treeview(
        parent,
        columns=columns,
        show="headings",
        style=f"{style_name}.Treeview",
        **kw
    )

    for col, width in zip(columns, widths):
        tv.heading(col, text=col)
        tv.column(col, width=width, anchor="center", minwidth=40)

    sb = ttk.Scrollbar(parent, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)

    sb.pack(side="right", fill="y")
    tv.pack(fill="both", expand=True, padx=4, pady=4)

    tv.tag_configure("odd", background=ODD_ROW)
    tv.tag_configure("even", background=CARD_BG)

    return tv


def zebra(tv, rows):
    tv.delete(*tv.get_children())

    for index, row in enumerate(rows):
        tv.insert(
            "",
            "end",
            values=row,
            tags=("odd" if index % 2 else "even",)
        )


# ============================================================
# LOGOUT / RETURN TO LOGIN
# ============================================================
def _open_login_again():
    try:
        os.chdir(PROJECT_DIR)

        if not os.path.exists(LOGIN_FILE):
            messagebox.showerror(
                "Logout Error",
                f"Cannot find login file:\n\n{LOGIN_FILE}"
            )
            return

        runpy.run_path(LOGIN_FILE, run_name="__main__")

    except SystemExit:
        raise

    except Exception as e:
        messagebox.showerror(
            "Logout Error",
            f"Unable to return to login.\n\n{e}"
        )


def _do_logout(win):
    confirm = messagebox.askyesno(
        "Logout",
        "Are you sure you want to logout?",
        parent=win
    )

    if not confirm:
        return

    try:
        win.destroy()
        _open_login_again()

    except Exception as e:
        messagebox.showerror(
            "Logout Error",
            f"Unable to logout properly.\n\n{e}"
        )


# ============================================================
# SIDEBAR
# ============================================================
def make_sidebar(win, username, role_label, nav_items, active_key):
    old_sidebar = getattr(win, "_sidebar_frame", None)

    if old_sidebar is not None:
        try:
            old_sidebar.destroy()
        except Exception:
            pass

    sb = tk.Frame(win, bg=SIDEBAR, width=215)
    sb.pack(side="left", fill="y")
    sb.pack_propagate(False)

    win._sidebar_frame = sb

    tk.Label(
        sb,
        text="🐔",
        font=("Segoe UI Emoji", 44),
        bg=SIDEBAR,
        fg=CREAM
    ).pack(pady=(18, 0))

    tk.Label(
        sb,
        text="Chicken Dressed\nStall",
        font=("Georgia", 13, "bold"),
        bg=SIDEBAR,
        fg=CREAM,
        justify="center"
    ).pack(pady=(2, 0))

    tk.Frame(sb, bg=GOLD, height=2).pack(fill="x", padx=20, pady=10)

    tk.Label(
        sb,
        text=f"👤  {username}",
        font=("Segoe UI", 10, "bold"),
        bg=SIDEBAR,
        fg=GOLD
    ).pack()

    if role_label:
        tk.Label(
            sb,
            text=role_label,
            font=("Segoe UI", 9),
            bg=SIDEBAR,
            fg="#F5DEB3"
        ).pack(pady=(2, 14))
    else:
        tk.Frame(sb, bg=SIDEBAR, height=14).pack()

    for key, icon, label, cb in nav_items:
        is_active = key == active_key

        tk.Button(
            sb,
            text=f"  {icon}  {label}",
            anchor="w",
            bg=SIDE_ACT if is_active else SIDEBAR,
            fg=DARK_RED if is_active else CREAM,
            activebackground=SIDE_HV,
            activeforeground=WHITE,
            font=("Segoe UI", 11, "bold" if is_active else "normal"),
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=10,
            pady=10,
            command=cb
        ).pack(fill="x", padx=8, pady=2)

    tk.Frame(
        sb,
        bg="#5C0A0A",
        height=1
    ).pack(fill="x", padx=16, side="bottom", pady=6)

    tk.Button(
        sb,
        text="  🚪  Logout",
        anchor="w",
        bg=SIDEBAR,
        fg="#F5DEB3",
        activebackground=SIDE_HV,
        activeforeground=WHITE,
        font=("Segoe UI", 10),
        relief="flat",
        cursor="hand2",
        bd=0,
        padx=10,
        pady=8,
        command=lambda: _do_logout(win)
    ).pack(fill="x", padx=8, side="bottom", pady=2)

    return sb


def refresh_sidebar(win, username, role_label, nav_items, active_key):
    return make_sidebar(win, username, role_label, nav_items, active_key)


# ============================================================
# MISC UI HELPERS
# ============================================================
def make_header(parent, title):
    hdr = tk.Frame(parent, bg=CREAM, height=65)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)

    tk.Label(
        hdr,
        text=title,
        font=FT,
        bg=CREAM,
        fg=DARK_RED
    ).pack(side="left", padx=22, pady=10)

    return hdr


def card_frame(parent, **kw):
    return tk.Frame(
        parent,
        bg=CARD_BG,
        highlightbackground=BORDER,
        highlightthickness=1,
        **kw
    )


def kpi_strip(parent, items):
    for widget in parent.winfo_children():
        widget.destroy()

    for index, (label, value, color) in enumerate(items):
        card = tk.Frame(parent, bg=color)
        card.grid(row=0, column=index, sticky="ew", padx=6)

        parent.columnconfigure(index, weight=1)

        tk.Label(
            card,
            text=label,
            font=("Segoe UI", 10, "bold"),
            bg=color,
            fg=CREAM
        ).pack(pady=(14, 2), padx=12)

        tk.Label(
            card,
            text=value,
            font=("Georgia", 19, "bold"),
            bg=color,
            fg=WHITE
        ).pack(pady=(0, 14))