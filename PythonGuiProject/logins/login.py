from PIL import Image as PILImage, ImageTk, ImageDraw, ImageFilter
from tkinter import *
import os
import sys

# ------------------- Project Path Setup ------------------- #
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)

if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

from databases.auth_backend import login_user

# ------------------- Window Setup ------------------- #
window = Tk()
window.title("Eugene Dressed Chicken Stall - Sign In")
window.state("zoomed")
window.minsize(1100, 700)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "..", "images", "logo.png")


# ------------------- Color Palette (Analogous Warm Theme) ------------------- #
BG_DARK = "#2A120B"          # deep cocoa
BG_DARK_2 = "#3B1A0F"        # roasted brown
BG_PANEL = "#FFF4E3"         # warm cream
BG_CARD = "#FFFFFF"
BG_INPUT = "#FFF8EE"

ACCENT = "#B9472B"           # warm brick red
ACCENT_DARK = "#8F301D"
ACCENT_LIGHT = "#E9793D"     # orange
GOLD = "#F2A93B"
GOLD_SOFT = "#FFE1A8"

TEXT_MAIN = "#2A1810"
TEXT_DIM = "#7C5A49"
TEXT_LIGHT = "#FFF8EE"
BORDER = "#E8CDAE"
SHADOW = "#E3CDB6"
PLACEHOLDER = "#A98773"
WHITE = "#FFFFFF"

INFO = "#3A7CA5"
SUCCESS = "#3E8E4D"
WARNING = "#D39B2B"
ERROR = "#B9472B"


# ------------------- Fonts ------------------- #
FONT_BRAND = ("Georgia", 32, "bold")
FONT_TAGLINE = ("Georgia", 15, "italic")
FONT_TITLE = ("Georgia", 36, "bold")
FONT_SUBTITLE = ("Segoe UI", 12)
FONT_LABEL = ("Segoe UI", 10, "bold")
FONT_ENTRY = ("Segoe UI", 15)
FONT_BUTTON = ("Segoe UI", 15, "bold")
FONT_FOOTER = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 10)
FONT_FEATURE = ("Segoe UI", 11)


# ------------------- Set Window Icon ------------------- #
def set_window_icon():
    try:
        if os.path.exists(logo_path):
            logo_icon = PhotoImage(file=logo_path)
            window.iconphoto(False, logo_icon)
            window.logo_icon = logo_icon
    except Exception as e:
        print("Warning: Logo icon not loaded:", e)


# ------------------- Create Circular Logo ------------------- #
def create_circle_logo(image_path, size=(260, 260)):
    """
    Creates a circular logo with:
    - soft shadow
    - gold outer ring
    - cream background
    - circular crop of actual image
    """
    img = PILImage.open(image_path).convert("RGBA")
    img = img.resize((size[0] - 70, size[1] - 70), PILImage.LANCZOS)

    # Make image circular
    mask = PILImage.new("L", img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)

    circular_img = PILImage.new("RGBA", img.size, (0, 0, 0, 0))
    circular_img.paste(img, (0, 0), mask)

    canvas = PILImage.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Soft shadow
    shadow = PILImage.new("RGBA", size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse((18, 20, size[0] - 6, size[1] - 4), fill=(0, 0, 0, 65))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    canvas.alpha_composite(shadow)

    # Outer gold ring
    draw.ellipse((8, 8, size[0] - 8, size[1] - 8), fill=GOLD)

    # Inner cream ring
    draw.ellipse((20, 20, size[0] - 20, size[1] - 20), fill=BG_PANEL)

    # Thin accent ring
    draw.ellipse((30, 30, size[0] - 30, size[1] - 30), outline=ACCENT, width=3)

    # Paste centered circular logo
    x = (size[0] - circular_img.width) // 2
    y = (size[1] - circular_img.height) // 2
    canvas.paste(circular_img, (x, y), circular_img)

    return ImageTk.PhotoImage(canvas)


# ------------------- Placeholder Helpers ------------------- #
USER_PLACEHOLDER = "Enter your username"
PASS_PLACEHOLDER = "Enter your password"


def clear_placeholder(entry, placeholder, is_password=False):
    if entry.get() == placeholder:
        entry.delete(0, END)
        entry.config(fg=TEXT_MAIN)
        if is_password:
            entry.config(show="●")


def add_placeholder(entry, placeholder, is_password=False):
    if not entry.get():
        entry.insert(0, placeholder)
        entry.config(fg=PLACEHOLDER)
        if is_password:
            entry.config(show="")


def focus_entry(entry):
    entry.config(highlightbackground=ACCENT_LIGHT, highlightcolor=ACCENT_LIGHT)


def blur_entry(entry):
    entry.config(highlightbackground=BORDER, highlightcolor=BORDER)


def toggle_password():
    current_text = pwd_entry.get()
    if current_text == PASS_PLACEHOLDER:
        pwd_entry.config(show="")
        return
    pwd_entry.config(show="" if show_pass.get() else "●")


# ------------------- Button Hover ------------------- #
def on_button_enter(btn):
    btn.config(bg=ACCENT_DARK)


def on_button_leave(btn):
    btn.config(bg=ACCENT)


# ------------------- Custom Message Box ------------------- #
def show_message(title="Message", message="", kind="info"):
    colors = {
        "info": INFO,
        "success": SUCCESS,
        "warning": WARNING,
        "error": ERROR
    }

    icons = {
        "info": "i",
        "success": "✓",
        "warning": "!",
        "error": "X"
    }

    color = colors.get(kind, INFO)

    msg_win = Toplevel(window)
    msg_win.title(title)
    msg_win.configure(bg=BG_CARD)
    msg_win.grab_set()
    msg_win.transient(window)
    msg_win.resizable(False, False)

    mw, mh = 480, 250
    sw = msg_win.winfo_screenwidth()
    sh = msg_win.winfo_screenheight()
    msg_win.geometry(f"{mw}x{mh}+{(sw - mw) // 2}+{(sh - mh) // 2}")

    header = Frame(msg_win, bg=color, height=65)
    header.pack(fill="x")
    header.pack_propagate(False)

    Label(
        header,
        text=icons.get(kind, "i"),
        font=("Georgia", 22, "bold"),
        bg=color,
        fg=WHITE
    ).pack(side="left", padx=(22, 12))

    Label(
        header,
        text=title,
        font=("Georgia", 16, "bold"),
        bg=color,
        fg=WHITE
    ).pack(side="left")

    body = Frame(msg_win, bg=BG_CARD, padx=24, pady=22)
    body.pack(expand=True, fill="both")

    Label(
        body,
        text=message,
        font=("Segoe UI", 12),
        bg=BG_CARD,
        fg=TEXT_MAIN,
        wraplength=410,
        justify="left"
    ).pack(anchor="w")

    Button(
        msg_win,
        text="OK",
        font=("Segoe UI", 11, "bold"),
        bg=color,
        fg=WHITE,
        relief="flat",
        activebackground=color,
        activeforeground=WHITE,
        cursor="hand2",
        command=msg_win.destroy
    ).pack(pady=(0, 18), ipadx=28, ipady=6)


# ------------------- Login Logic ------------------- #
def login():
    username_val = user_entry.get().strip()
    password_val = pwd_entry.get()

    if username_val == USER_PLACEHOLDER:
        username_val = ""

    if password_val == PASS_PLACEHOLDER:
        password_val = ""

    if not username_val or not password_val:
        show_message("Missing Fields", "Please enter both username and password.", "warning")
        return

    login_btn.config(text="SIGNING IN...", state=DISABLED, bg=ACCENT_DARK)
    window.update_idletasks()

    try:
        user = login_user(username_val, password_val)

        if user:
            role = user["role"]
            full_name = user["full_name"]

            window.destroy()

            if role == "admin":
                from admin.adminDashboard import AdminDashboard
                app = AdminDashboard(full_name)
                app.mainloop()

            elif role == "inventory":
                from inventory.inventoryDashboard import InventoryDashboard
                app = InventoryDashboard(full_name)
                app.mainloop()

            elif role == "cashier":
                from cashier.cashierDashboard import CashierDashboard
                app = CashierDashboard(full_name)
                app.mainloop()

            else:
                show_message("Access Denied", "Your account role is not allowed.", "error")

        else:
            show_message("Access Denied", "Invalid username or password.", "error")
            pwd_entry.delete(0, END)
            add_placeholder(pwd_entry, PASS_PLACEHOLDER, is_password=True)

    except Exception as e:
        show_message("Login Error", f"Unable to sign in.\n\n{e}", "error")

    finally:
        try:
            login_btn.config(text="SIGN IN", state=NORMAL, bg=ACCENT)
        except Exception:
            pass


# ------------------- Build UI ------------------- #
set_window_icon()

main_container = Frame(window, bg=BG_PANEL)
main_container.pack(fill="both", expand=True)

# ------------------- Left Side ------------------- #
left = Frame(main_container, bg=BG_DARK)
left.place(relx=0, rely=0, relwidth=0.44, relheight=1)

top_band = Frame(left, bg=BG_DARK_2, height=90)
top_band.pack(fill="x", side="top")

gold_strip = Frame(left, bg=GOLD, width=10)
gold_strip.pack(side="right", fill="y")

orange_strip = Frame(left, bg=ACCENT_LIGHT, width=4)
orange_strip.pack(side="right", fill="y")

brand_frame = Frame(left, bg=BG_DARK)
brand_frame.place(relx=0.5, rely=0.48, anchor="center")

try:
    logo_photo = create_circle_logo(logo_path, (280, 280))
    logo_lbl = Label(brand_frame, image=logo_photo, bg=BG_DARK, bd=0)
    logo_lbl.image = logo_photo
    logo_lbl.pack(pady=(0, 26))
except Exception as e:
    print("Logo display error:", e)
    Label(
        brand_frame,
        text="🍗",
        font=("Segoe UI Emoji", 110),
        bg=BG_DARK,
        fg=GOLD
    ).pack(pady=(0, 24))

Label(
    brand_frame,
    text="Eugene Dressed",
    font=FONT_BRAND,
    bg=BG_DARK,
    fg=GOLD_SOFT
).pack()

Label(
    brand_frame,
    text="Chicken Stall",
    font=FONT_BRAND,
    bg=BG_DARK,
    fg=GOLD
).pack()

Label(
    brand_frame,
    text="Fresh products, faster service, better management.",
    font=FONT_TAGLINE,
    bg=BG_DARK,
    fg="#F6D6BA"
).pack(pady=(12, 0))

feature_wrap = Frame(brand_frame, bg=BG_DARK)
feature_wrap.pack(pady=(28, 0))

for feature in ["Point of Sale", "Inventory Monitoring", "Cashier Management"]:
    row = Frame(feature_wrap, bg=BG_DARK)
    row.pack(anchor="center", pady=4)

    Label(
        row,
        text="●",
        font=("Segoe UI", 10, "bold"),
        bg=BG_DARK,
        fg=ACCENT_LIGHT
    ).pack(side="left", padx=(0, 8))

    Label(
        row,
        text=feature,
        font=FONT_FEATURE,
        bg=BG_DARK,
        fg="#F8DDC5"
    ).pack(side="left")

Label(
    left,
    text="Eugene Dressed Chicken Stall © 2026",
    font=FONT_FOOTER,
    bg=BG_DARK,
    fg="#CDA98B"
).place(relx=0.5, rely=0.95, anchor="center")


# ------------------- Right Side ------------------- #
right = Frame(main_container, bg=BG_PANEL)
right.place(relx=0.44, rely=0, relwidth=0.56, relheight=1)

# Decorative circles
decor_top = Canvas(right, width=180, height=180, bg=BG_PANEL, highlightthickness=0)
decor_top.place(relx=0.86, rely=0.10, anchor="center")
decor_top.create_oval(10, 10, 170, 170, fill="#FFE8BD", outline="")

decor_bottom = Canvas(right, width=150, height=150, bg=BG_PANEL, highlightthickness=0)
decor_bottom.place(relx=0.12, rely=0.88, anchor="center")
decor_bottom.create_oval(10, 10, 140, 140, fill="#F7D7C3", outline="")

# Card shadow
card_shadow = Frame(right, bg=SHADOW)
card_shadow.place(relx=0.505, rely=0.505, anchor="center", relwidth=0.66, relheight=0.68)

# Login card
card = Frame(
    right,
    bg=BG_CARD,
    highlightbackground=BORDER,
    highlightthickness=1,
    padx=60,
    pady=45
)
card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.66, relheight=0.70)

Label(
    card,
    text="Welcome Back",
    font=FONT_TITLE,
    bg=BG_CARD,
    fg=ACCENT
).pack(anchor="w")

Label(
    card,
    text="Sign in to continue to the Eugene Dressed Chicken Stall system.",
    font=FONT_SUBTITLE,
    bg=BG_CARD,
    fg=TEXT_DIM
).pack(anchor="w", pady=(4, 18))

# Divider
divider = Frame(card, bg=GOLD, height=3)
divider.pack(fill="x", pady=(0, 28))

# Small top label
Label(
    card,
    text="AUTHORIZED STAFF LOGIN",
    font=("Segoe UI", 9, "bold"),
    bg=BG_CARD,
    fg=ACCENT_LIGHT
).pack(anchor="w", pady=(0, 18))

# Username
Label(
    card,
    text="USERNAME",
    font=FONT_LABEL,
    bg=BG_CARD,
    fg=TEXT_DIM
).pack(anchor="w")

user_entry = Entry(
    card,
    font=FONT_ENTRY,
    bg=BG_INPUT,
    fg=PLACEHOLDER,
    insertbackground=ACCENT,
    relief="flat",
    highlightbackground=BORDER,
    highlightcolor=ACCENT_LIGHT,
    highlightthickness=1
)
user_entry.pack(fill="x", pady=(8, 24), ipady=13)
user_entry.insert(0, USER_PLACEHOLDER)

user_entry.bind("<FocusIn>", lambda e: [clear_placeholder(user_entry, USER_PLACEHOLDER), focus_entry(user_entry)])
user_entry.bind("<FocusOut>", lambda e: [add_placeholder(user_entry, USER_PLACEHOLDER), blur_entry(user_entry)])

# Password
Label(
    card,
    text="PASSWORD",
    font=FONT_LABEL,
    bg=BG_CARD,
    fg=TEXT_DIM
).pack(anchor="w")

pwd_entry = Entry(
    card,
    font=FONT_ENTRY,
    bg=BG_INPUT,
    fg=PLACEHOLDER,
    insertbackground=ACCENT,
    relief="flat",
    highlightbackground=BORDER,
    highlightcolor=ACCENT_LIGHT,
    highlightthickness=1
)
pwd_entry.pack(fill="x", pady=(8, 12), ipady=13)
pwd_entry.insert(0, PASS_PLACEHOLDER)

pwd_entry.bind("<FocusIn>", lambda e: [clear_placeholder(pwd_entry, PASS_PLACEHOLDER, is_password=True), focus_entry(pwd_entry)])
pwd_entry.bind("<FocusOut>", lambda e: [add_placeholder(pwd_entry, PASS_PLACEHOLDER, is_password=True), blur_entry(pwd_entry)])
pwd_entry.bind("<Return>", lambda e: login())

# Show password
show_pass = BooleanVar()

chk = Checkbutton(
    card,
    text="Show password",
    variable=show_pass,
    command=toggle_password,
    bg=BG_CARD,
    fg=TEXT_DIM,
    selectcolor=BG_PANEL,
    activebackground=BG_CARD,
    activeforeground=TEXT_DIM,
    font=("Segoe UI", 11),
    cursor="hand2"
)
chk.pack(anchor="w", pady=(0, 30))

# Sign in button
login_btn = Button(
    card,
    text="SIGN IN",
    font=FONT_BUTTON,
    bg=ACCENT,
    fg=WHITE,
    relief="flat",
    activebackground=ACCENT_DARK,
    activeforeground=WHITE,
    cursor="hand2",
    command=login
)
login_btn.pack(fill="x", ipady=16)

login_btn.bind("<Enter>", lambda e: on_button_enter(login_btn))
login_btn.bind("<Leave>", lambda e: on_button_leave(login_btn))

# Footer texts inside card
Label(
    card,
    text="Authorized staff only",
    font=FONT_FOOTER,
    bg=BG_CARD,
    fg=TEXT_DIM
).pack(pady=(22, 0))

Label(
    card,
    text="POS  •  Inventory  •  Cashier",
    font=FONT_SMALL,
    bg=BG_CARD,
    fg=ACCENT_LIGHT
).pack(pady=(5, 0))


# ------------------- Shortcuts ------------------- #
window.bind("<Escape>", lambda e: window.state("normal"))

user_entry.focus()
window.mainloop()