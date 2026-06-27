"""
Password Generator
==================
Features:
  • User-defined length (4–64)
  • Uppercase, Lowercase, Numbers, Symbols toggles
  • Real-time password strength meter
  • One-click copy to clipboard
  • Password history (last 10)
  • Bulk generate mode
  • Exclude ambiguous characters option
  • Dark theme GUI
"""

import tkinter as tk
from tkinter import messagebox
import random
import string
import re
from datetime import datetime

# ─────────────────────────── Theme ───────────────────────────

T = {
    "bg":       "#0F1117",
    "surface":  "#1A1D27",
    "card":     "#22263A",
    "border":   "#2E3350",
    "accent":   "#7C6FF7",
    "accent2":  "#4ECDC4",
    "text":     "#E8EAF6",
    "subtext":  "#8B90B8",
    "weak":     "#FF6B6B",
    "medium":   "#F9A825",
    "strong":   "#4ECDC4",
    "vstrong":  "#7C6FF7",
    "btn":      "#7C6FF7",
    "btn_fg":   "#FFFFFF",
    "copy_btn": "#4ECDC4",
    "copy_fg":  "#0F1117",
    "green":    "#43A047",
}

AMBIGUOUS = set("0O1lI|`")

# ─────────────────────────── Logic ───────────────────────────

class PasswordGenerator:
    def __init__(self):
        self.history = []

    def generate(self, length, use_upper, use_lower,
                 use_digits, use_symbols, exclude_ambiguous=False):
        charset = ""
        guaranteed = []

        if use_lower:
            chars = string.ascii_lowercase
            if exclude_ambiguous:
                chars = "".join(c for c in chars if c not in AMBIGUOUS)
            charset += chars
            if chars:
                guaranteed.append(random.choice(chars))

        if use_upper:
            chars = string.ascii_uppercase
            if exclude_ambiguous:
                chars = "".join(c for c in chars if c not in AMBIGUOUS)
            charset += chars
            if chars:
                guaranteed.append(random.choice(chars))

        if use_digits:
            chars = string.digits
            if exclude_ambiguous:
                chars = "".join(c for c in chars if c not in AMBIGUOUS)
            charset += chars
            if chars:
                guaranteed.append(random.choice(chars))

        if use_symbols:
            chars = string.punctuation
            if exclude_ambiguous:
                chars = "".join(c for c in chars if c not in AMBIGUOUS)
            charset += chars
            if chars:
                guaranteed.append(random.choice(chars))

        if not charset:
            return ""

        remaining = length - len(guaranteed)
        if remaining < 0:
            guaranteed = guaranteed[:length]
            remaining = 0

        password_chars = guaranteed + [random.choice(charset) for _ in range(remaining)]
        random.shuffle(password_chars)
        password = "".join(password_chars)

        self.history.insert(0, {
            "password": password,
            "time": datetime.now().strftime("%H:%M:%S"),
            "length": length,
        })
        self.history = self.history[:10]
        return password

    def check_strength(self, password):
        """Returns (score 0-4, label, color)"""
        if not password:
            return 0, "", T["subtext"]

        score = 0
        length = len(password)

        if length >= 8:  score += 1
        if length >= 12: score += 1
        if length >= 16: score += 1

        has_lower  = bool(re.search(r'[a-z]', password))
        has_upper  = bool(re.search(r'[A-Z]', password))
        has_digit  = bool(re.search(r'\d', password))
        has_symbol = bool(re.search(r'[^a-zA-Z0-9]', password))

        variety = sum([has_lower, has_upper, has_digit, has_symbol])
        if variety >= 2: score += 1
        if variety >= 3: score += 1
        if variety == 4: score += 1

        score = min(score, 4)

        labels = {0: "Weak", 1: "Fair", 2: "Good", 3: "Strong", 4: "Very Strong"}
        colors = {
            0: T["weak"], 1: T["medium"],
            2: T["medium"], 3: T["strong"], 4: T["vstrong"]
        }
        return score, labels[score], colors[score]


# ─────────────────────────── GUI ─────────────────────────────

class PasswordApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Password Generator")
        self.root.configure(bg=T["bg"])
        self.root.resizable(False, False)
        self.gen = PasswordGenerator()
        self._build_ui()
        self._generate()

    def _build_ui(self):
        # Top bar
        bar = tk.Frame(self.root, bg=T["surface"], pady=12)
        bar.pack(fill="x")
        tk.Label(bar, text="🔐  Password Generator",
                 font=("Helvetica", 17, "bold"),
                 fg=T["accent"], bg=T["surface"]).pack(side="left", padx=20)
        tk.Label(bar, text="Secure · Random · Strong",
                 font=("Helvetica", 10),
                 fg=T["subtext"], bg=T["surface"]).pack(side="right", padx=20)

        # Password Display
        disp = tk.Frame(self.root, bg=T["card"], pady=14)
        disp.pack(fill="x", padx=20, pady=(14, 0))

        self._pwd_var = tk.StringVar()
        self._pwd_entry = tk.Entry(
            disp, textvariable=self._pwd_var,
            font=("Courier New", 15, "bold"),
            bg=T["card"], fg=T["accent2"],
            relief="flat", bd=0,
            readonlybackground=T["card"],
            state="readonly", justify="center")
        self._pwd_entry.pack(fill="x", padx=16, pady=(0, 8))

        # Strength bar
        self._strength_canvas = tk.Canvas(
            disp, height=6, bg=T["border"], highlightthickness=0)
        self._strength_canvas.pack(fill="x", padx=16, pady=(0, 6))
        self._strength_bar = self._strength_canvas.create_rectangle(
            0, 0, 0, 6, fill=T["accent"], width=0)

        self._strength_var = tk.StringVar(value="")
        self._strength_lbl = tk.Label(
            disp, textvariable=self._strength_var,
            font=("Helvetica", 10, "bold"),
            fg=T["subtext"], bg=T["card"])
        self._strength_lbl.pack()

        self._copy_btn = tk.Button(
            disp, text="📋  Copy Password",
            font=("Helvetica", 12, "bold"),
            bg=T["copy_btn"], fg=T["copy_fg"],
            relief="flat", padx=20, pady=8,
            cursor="hand2",
            command=self._copy)
        self._copy_btn.pack(pady=(10, 4))

        # Settings
        settings = tk.Frame(self.root, bg=T["bg"])
        settings.pack(fill="x", padx=20, pady=12)

        # Length slider
        len_frame = tk.Frame(settings, bg=T["surface"], pady=10, padx=14)
        len_frame.pack(fill="x", pady=(0, 8))
        tk.Label(len_frame, text="Password Length",
                 font=("Helvetica", 11, "bold"),
                 fg=T["text"], bg=T["surface"]).pack(side="left")
        self._len_var = tk.IntVar(value=16)
        self._len_lbl = tk.Label(len_frame, text="16",
                                  font=("Helvetica", 13, "bold"),
                                  fg=T["accent"], bg=T["surface"], width=3)
        self._len_lbl.pack(side="right")
        self._len_slider = tk.Scale(
            len_frame, from_=4, to=64,
            orient="horizontal", variable=self._len_var,
            bg=T["surface"], fg=T["text"],
            highlightthickness=0, troughcolor=T["border"],
            activebackground=T["accent"],
            sliderrelief="flat", bd=0, showvalue=False,
            command=self._on_len_change)
        self._len_slider.set(16)
        self._len_slider.pack(side="right", fill="x", expand=True, padx=10)

        # Checkboxes
        checks_frame = tk.Frame(settings, bg=T["surface"], pady=10, padx=14)
        checks_frame.pack(fill="x", pady=(0, 8))
        tk.Label(checks_frame, text="Character Types",
                 font=("Helvetica", 11, "bold"),
                 fg=T["text"], bg=T["surface"]).pack(anchor="w", pady=(0, 8))

        self._upper_var   = tk.BooleanVar(value=True)
        self._lower_var   = tk.BooleanVar(value=True)
        self._digits_var  = tk.BooleanVar(value=True)
        self._symbols_var = tk.BooleanVar(value=True)

        for text, var in [
            ("🔠  Uppercase Letters (A-Z)", self._upper_var),
            ("🔡  Lowercase Letters (a-z)", self._lower_var),
            ("🔢  Numbers (0-9)",           self._digits_var),
            ("🔣  Symbols (!@#$...)",        self._symbols_var),
        ]:
            tk.Checkbutton(checks_frame, text=text, variable=var,
                           font=("Helvetica", 11),
                           fg=T["text"], bg=T["surface"],
                           selectcolor=T["accent"],
                           activebackground=T["surface"],
                           activeforeground=T["accent"],
                           bd=0, cursor="hand2",
                           command=self._generate).pack(anchor="w", pady=2)

        # Extra options
        extra = tk.Frame(settings, bg=T["surface"], pady=10, padx=14)
        extra.pack(fill="x", pady=(0, 8))
        tk.Label(extra, text="Options",
                 font=("Helvetica", 11, "bold"),
                 fg=T["text"], bg=T["surface"]).pack(anchor="w", pady=(0, 6))
        self._ambig_var = tk.BooleanVar(value=False)
        tk.Checkbutton(extra,
                       text="❌  Exclude Ambiguous Characters (0,O,1,l,I)",
                       variable=self._ambig_var,
                       font=("Helvetica", 10),
                       fg=T["subtext"], bg=T["surface"],
                       selectcolor=T["accent"],
                       activebackground=T["surface"],
                       bd=0, cursor="hand2",
                       command=self._generate).pack(anchor="w")

        # Buttons
        btn_row = tk.Frame(self.root, bg=T["bg"])
        btn_row.pack(pady=6)
        tk.Button(btn_row, text="🔄  Generate New",
                  font=("Helvetica", 12, "bold"),
                  bg=T["btn"], fg=T["btn_fg"],
                  relief="flat", padx=20, pady=9,
                  cursor="hand2",
                  command=self._generate).pack(side="left", padx=8)
        tk.Button(btn_row, text="📦  Bulk (x5)",
                  font=("Helvetica", 12),
                  bg=T["card"], fg=T["text"],
                  relief="flat", padx=20, pady=9,
                  cursor="hand2",
                  command=self._bulk_generate).pack(side="left", padx=8)

        # History
        hist_outer = tk.Frame(self.root, bg=T["bg"])
        hist_outer.pack(fill="x", padx=20, pady=(4, 12))
        tk.Label(hist_outer, text="RECENT PASSWORDS",
                 font=("Helvetica", 9, "bold"),
                 fg=T["border"], bg=T["bg"]).pack(anchor="w")
        self._hist_text = tk.Text(
            hist_outer, height=5,
            bg=T["surface"], fg=T["subtext"],
            font=("Courier New", 10),
            relief="flat", state="disabled",
            padx=10, pady=6)
        self._hist_text.pack(fill="x")
        self._hist_text.tag_configure("pwd",  foreground=T["accent2"])
        self._hist_text.tag_configure("time", foreground=T["border"])

    def _on_len_change(self, val):
        self._len_lbl.config(text=str(int(float(val))))
        self._generate()

    def _generate(self):
        length  = self._len_var.get()
        upper   = self._upper_var.get()
        lower   = self._lower_var.get()
        digits  = self._digits_var.get()
        symbols = self._symbols_var.get()
        ambig   = self._ambig_var.get()

        if not any([upper, lower, digits, symbols]):
            self._pwd_var.set("Select at least one type!")
            return

        pwd = self.gen.generate(length, upper, lower, digits, symbols, ambig)
        self._pwd_var.set(pwd)
        self._update_strength(pwd)
        self._update_history()

    def _update_strength(self, pwd):
        score, label, color = self.gen.check_strength(pwd)
        self._strength_var.set(f"Strength: {label}")
        self._strength_lbl.config(fg=color)
        self._strength_canvas.update_idletasks()
        w = self._strength_canvas.winfo_width()
        ratio = score / 4 if score > 0 else 0
        self._strength_canvas.coords(
            self._strength_bar, 0, 0, int(w * ratio), 6)
        self._strength_canvas.itemconfig(self._strength_bar, fill=color)

    def _copy(self):
        pwd = self._pwd_var.get()
        if not pwd or "Select" in pwd:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(pwd)
        self._copy_btn.config(text="✅  Copied!", bg=T["green"], fg="white")
        self.root.after(1500, lambda: self._copy_btn.config(
            text="📋  Copy Password", bg=T["copy_btn"], fg=T["copy_fg"]))

    def _update_history(self):
        self._hist_text.config(state="normal")
        self._hist_text.delete("1.0", "end")
        for entry in self.gen.history:
            self._hist_text.insert("end", f"[{entry['time']}]  ", "time")
            self._hist_text.insert("end", f"{entry['password']}\n", "pwd")
        self._hist_text.config(state="disabled")

    def _bulk_generate(self):
        length  = self._len_var.get()
        upper   = self._upper_var.get()
        lower   = self._lower_var.get()
        digits  = self._digits_var.get()
        symbols = self._symbols_var.get()
        ambig   = self._ambig_var.get()

        if not any([upper, lower, digits, symbols]):
            messagebox.showwarning("Password Generator", "Select at least one type!")
            return

        win = tk.Toplevel(self.root)
        win.title("Bulk Passwords")
        win.configure(bg=T["bg"])
        win.geometry("500x320")
        win.resizable(False, False)

        tk.Label(win, text="📦 5 Generated Passwords",
                 font=("Helvetica", 14, "bold"),
                 fg=T["accent"], bg=T["bg"]).pack(pady=(14, 8))

        for i in range(5):
            pwd = self.gen.generate(length, upper, lower, digits, symbols, ambig)
            row = tk.Frame(win, bg=T["surface"], pady=6, padx=12)
            row.pack(fill="x", padx=16, pady=3)
            tk.Label(row, text=pwd, font=("Courier New", 12),
                     fg=T["accent2"], bg=T["surface"]).pack(side="left")
            def copy_this(p=pwd):
                win.clipboard_clear()
                win.clipboard_append(p)
            tk.Button(row, text="Copy", font=("Helvetica", 9),
                      bg=T["btn"], fg="white", relief="flat",
                      padx=8, cursor="hand2",
                      command=copy_this).pack(side="right")

        self._update_history()
        tk.Button(win, text="Close", font=("Helvetica", 11),
                  bg=T["card"], fg=T["text"],
                  relief="flat", padx=16, pady=6,
                  command=win.destroy).pack(pady=12)


def main():
    root = tk.Tk()
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = 560, 720
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
    PasswordApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
