"""
Typing Speed Tester
====================
A full-featured typing speed application with:
- Real-time WPM & accuracy tracking
- SQLite leaderboard / history
- Multiple difficulty levels
- Character-by-character color feedback
- Animated progress bar
- Dark/Light theme toggle
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import time
import random
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────── Data ────────────────────────────

WORD_POOLS = {
    "Easy": [
        "the quick brown fox jumps over the lazy dog and runs away fast into the dark forest",
        "she sells sea shells by the sea shore on a sunny summer afternoon near the blue waves",
        "all good things must come to an end but new beginnings always follow right after that",
        "time flies when you are having fun and learning new skills every single day of your life",
        "practice makes perfect so keep typing fast and try to avoid making too many mistakes today",
        "the sun rises in the east and sets in the west each and every day without any fail",
        "a journey of a thousand miles begins with a single step taken in the right direction now",
        "reading books every day helps you grow smarter and learn many new words to use in life",
    ],
    "Medium": [
        "programming is the art of telling another human what one wants the computer to do efficiently",
        "python is a versatile language used for web development data science automation and artificial intelligence",
        "algorithms and data structures form the backbone of computer science and software engineering practices",
        "keyboard shortcuts can dramatically improve your productivity when working with text editors and terminals",
        "debugging requires patience logical thinking and a systematic approach to isolate and fix code errors",
        "version control systems like git allow developers to track changes collaborate and manage project history",
        "object oriented programming organizes code into reusable classes and objects with properties and methods",
        "the internet connects billions of devices worldwide enabling instant communication and information sharing",
    ],
    "Hard": [
        "asynchronous programming paradigms such as callbacks promises and async await improve application throughput significantly",
        "cryptographic hash functions produce fixed-length deterministic outputs from arbitrary-length inputs irreversibly",
        "kubernetes orchestrates containerized workloads providing scalability fault-tolerance and declarative configuration management",
        "the fibonacci sequence demonstrates recursive problem-solving where each term equals the sum of its predecessors",
        "polymorphism encapsulation inheritance and abstraction constitute the four pillars of object-oriented programming methodology",
        "microservices architecture decomposes monolithic applications into independently deployable loosely-coupled service components",
        "neural networks approximate complex nonlinear functions through layered compositions of weighted activation transformations",
        "concurrency and parallelism differ fundamentally though both techniques aim to maximize computational resource utilization",
    ],
}

THEMES = {
    "dark": {
        "bg":          "#0f1117",
        "surface":     "#1a1d27",
        "card":        "#22263a",
        "border":      "#2e3350",
        "accent":      "#7c6ff7",
        "accent2":     "#4ecdc4",
        "text":        "#e8eaf6",
        "subtext":     "#8b90b8",
        "correct":     "#4ecdc4",
        "wrong":       "#ff6b6b",
        "pending":     "#454875",
        "cursor_bg":   "#7c6ff7",
        "stat_bg":     "#1a1d27",
        "btn_bg":      "#7c6ff7",
        "btn_fg":      "#ffffff",
        "btn_hover":   "#6355e0",
        "progress_bg": "#22263a",
        "progress_fg": "#7c6ff7",
    },
    "light": {
        "bg":          "#f0f2ff",
        "surface":     "#ffffff",
        "card":        "#f7f8ff",
        "border":      "#d0d4f0",
        "accent":      "#5b4de8",
        "accent2":     "#00b0a8",
        "text":        "#1a1a2e",
        "subtext":     "#6b6f9a",
        "correct":     "#00897b",
        "wrong":       "#e53935",
        "pending":     "#c5c8e8",
        "cursor_bg":   "#5b4de8",
        "stat_bg":     "#f0f2ff",
        "btn_bg":      "#5b4de8",
        "btn_fg":      "#ffffff",
        "btn_hover":   "#4435c9",
        "progress_bg": "#dde0f8",
        "progress_fg": "#5b4de8",
    },
}

# ─────────────────────────── DB Layer ────────────────────────

class Database:
    def __init__(self, path="typing_results.db"):
        self.conn = sqlite3.connect(path)
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                date      TEXT    NOT NULL,
                difficulty TEXT   NOT NULL,
                wpm       REAL    NOT NULL,
                accuracy  REAL    NOT NULL,
                duration  REAL    NOT NULL,
                chars     INTEGER NOT NULL,
                errors    INTEGER NOT NULL
            );
        """)
        self.conn.commit()

    def save(self, difficulty, wpm, accuracy, duration, chars, errors):
        self.conn.execute(
            "INSERT INTO sessions(date,difficulty,wpm,accuracy,duration,chars,errors) "
            "VALUES(?,?,?,?,?,?,?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), difficulty,
             round(wpm, 1), round(accuracy, 1), round(duration, 1), chars, errors)
        )
        self.conn.commit()

    def get_top(self, n=10):
        cur = self.conn.execute(
            "SELECT date,difficulty,wpm,accuracy FROM sessions ORDER BY wpm DESC LIMIT ?", (n,)
        )
        return cur.fetchall()

    def get_recent(self, n=20):
        cur = self.conn.execute(
            "SELECT date,difficulty,wpm,accuracy,duration,chars,errors FROM sessions "
            "ORDER BY id DESC LIMIT ?", (n,)
        )
        return cur.fetchall()

    def get_stats(self):
        cur = self.conn.execute(
            "SELECT COUNT(*), AVG(wpm), MAX(wpm), AVG(accuracy) FROM sessions"
        )
        return cur.fetchone()

    def close(self):
        self.conn.close()


# ─────────────────────────── App ─────────────────────────────

@dataclass
class SessionState:
    started: bool = False
    finished: bool = False
    start_time: float = 0.0
    text: str = ""
    typed: str = ""
    errors: int = 0
    wpm: float = 0.0
    accuracy: float = 100.0
    difficulty: str = "Medium"


class TypingSpeedApp:
    TICK_MS = 100          # UI refresh rate
    TIME_LIMIT = 60        # seconds

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Typing Speed Tester")
        self.root.resizable(True, True)
        self.root.minsize(860, 620)

        self.db = Database()
        self.state = SessionState()
        self._theme_name = "dark"
        self.T = THEMES[self._theme_name]
        self._tick_id: Optional[str] = None

        self._build_ui()
        self._new_test()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Build UI ──────────────────────────────────────────────

    def _build_ui(self):
        self.root.configure(bg=self.T["bg"])

        # ── Top bar ──
        bar = tk.Frame(self.root, bg=self.T["surface"], pady=10)
        bar.pack(fill="x")

        tk.Label(bar, text="⌨  Typing Speed Tester", font=("Helvetica", 17, "bold"),
                 fg=self.T["accent"], bg=self.T["surface"]).pack(side="left", padx=20)

        right = tk.Frame(bar, bg=self.T["surface"])
        right.pack(side="right", padx=14)

        self._theme_btn = self._flat_btn(right, "☀ Light", self._toggle_theme)
        self._theme_btn.pack(side="right", padx=6)
        self._flat_btn(right, "📊 History", self._show_history).pack(side="right", padx=6)

        # ── Difficulty + time ──
        ctrl = tk.Frame(self.root, bg=self.T["bg"], pady=10)
        ctrl.pack(fill="x", padx=30)

        tk.Label(ctrl, text="Difficulty:", fg=self.T["subtext"],
                 bg=self.T["bg"], font=("Helvetica", 11)).pack(side="left")

        self._diff_var = tk.StringVar(value="Medium")
        for d in ("Easy", "Medium", "Hard"):
            rb = tk.Radiobutton(ctrl, text=d, variable=self._diff_var, value=d,
                                command=self._new_test, bg=self.T["bg"],
                                fg=self.T["text"], selectcolor=self.T["accent"],
                                activebackground=self.T["bg"],
                                activeforeground=self.T["accent"],
                                font=("Helvetica", 11), bd=0)
            rb.pack(side="left", padx=8)

        # Timer label (right side)
        self._timer_var = tk.StringVar(value="60s")
        tk.Label(ctrl, textvariable=self._timer_var, fg=self.T["accent"],
                 bg=self.T["bg"], font=("Courier", 18, "bold")).pack(side="right")
        tk.Label(ctrl, text="Time:", fg=self.T["subtext"],
                 bg=self.T["bg"], font=("Helvetica", 11)).pack(side="right", padx=4)

        # ── Stats row ──
        stats_frame = tk.Frame(self.root, bg=self.T["bg"])
        stats_frame.pack(fill="x", padx=30, pady=(0, 10))

        self._wpm_var     = tk.StringVar(value="0")
        self._acc_var     = tk.StringVar(value="100%")
        self._chars_var   = tk.StringVar(value="0")
        self._errors_var  = tk.StringVar(value="0")

        for label, var, color in [
            ("WPM",      self._wpm_var,    self.T["accent"]),
            ("Accuracy", self._acc_var,    self.T["accent2"]),
            ("Chars",    self._chars_var,  self.T["text"]),
            ("Errors",   self._errors_var, self.T["wrong"]),
        ]:
            self._stat_card(stats_frame, label, var, color).pack(
                side="left", expand=True, fill="x", padx=5)

        # ── Progress bar ──
        self._progress_canvas = tk.Canvas(
            self.root, height=6, bg=self.T["progress_bg"],
            highlightthickness=0)
        self._progress_canvas.pack(fill="x", padx=30, pady=(0, 8))
        self._prog_bar = self._progress_canvas.create_rectangle(
            0, 0, 0, 6, fill=self.T["progress_fg"], width=0)

        # ── Prompt text area ──
        prompt_outer = tk.Frame(self.root, bg=self.T["border"], bd=0)
        prompt_outer.pack(fill="x", padx=30, pady=(0, 6))

        self._prompt_text = tk.Text(
            prompt_outer, wrap="word", height=4, font=("Courier New", 15),
            bg=self.T["card"], fg=self.T["pending"],
            relief="flat", bd=16, cursor="arrow",
            state="disabled", exportselection=False,
            padx=10, pady=10)
        self._prompt_text.pack(fill="x")
        self._prompt_text.tag_configure("correct", foreground=self.T["correct"])
        self._prompt_text.tag_configure("wrong",   foreground=self.T["wrong"],
                                        background="#3a1a1a" if self._theme_name=="dark" else "#fdecea")
        self._prompt_text.tag_configure("cursor",  background=self.T["cursor_bg"],
                                        foreground=self.T["surface"])
        self._prompt_text.tag_configure("pending", foreground=self.T["pending"])

        # ── Input box ──
        input_frame = tk.Frame(self.root, bg=self.T["bg"])
        input_frame.pack(fill="x", padx=30, pady=(0, 10))

        self._input_var = tk.StringVar()
        self._input_var.trace_add("write", self._on_type)

        self._entry = tk.Entry(
            input_frame, textvariable=self._input_var,
            font=("Courier New", 14), bg=self.T["surface"],
            fg=self.T["text"], insertbackground=self.T["accent"],
            relief="flat", bd=12,
            disabledbackground=self.T["border"])
        self._entry.pack(fill="x", ipady=10)
        self._entry.bind("<space>", self._on_space)
        self._entry.bind("<BackSpace>", self._on_backspace)

        # ── Buttons ──
        btn_row = tk.Frame(self.root, bg=self.T["bg"])
        btn_row.pack(pady=6)

        self._start_btn = self._accent_btn(btn_row, "▶  Start / Restart", self._new_test)
        self._start_btn.pack(side="left", padx=8)

        # ── Status label ──
        self._status_var = tk.StringVar(value="Click Start or begin typing…")
        tk.Label(self.root, textvariable=self._status_var,
                 fg=self.T["subtext"], bg=self.T["bg"],
                 font=("Helvetica", 10)).pack(pady=(0, 8))

    # ── Helpers ──────────────────────────────────────────────

    def _stat_card(self, parent, label, var, color):
        f = tk.Frame(parent, bg=self.T["stat_bg"], bd=0)
        tk.Label(f, textvariable=var, fg=color, bg=self.T["stat_bg"],
                 font=("Helvetica", 22, "bold")).pack(pady=(8, 0))
        tk.Label(f, text=label, fg=self.T["subtext"], bg=self.T["stat_bg"],
                 font=("Helvetica", 9)).pack(pady=(0, 8))
        return f

    def _flat_btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd,
                         bg=self.T["surface"], fg=self.T["subtext"],
                         relief="flat", bd=0, padx=10, pady=4,
                         font=("Helvetica", 10), cursor="hand2",
                         activebackground=self.T["border"],
                         activeforeground=self.T["text"])

    def _accent_btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd,
                         bg=self.T["btn_bg"], fg=self.T["btn_fg"],
                         relief="flat", bd=0, padx=22, pady=8,
                         font=("Helvetica", 12, "bold"), cursor="hand2",
                         activebackground=self.T["btn_hover"],
                         activeforeground="#ffffff")

    # ── Test logic ───────────────────────────────────────────

    def _new_test(self):
        if self._tick_id:
            self.root.after_cancel(self._tick_id)
            self._tick_id = None

        diff = self._diff_var.get()
        text = random.choice(WORD_POOLS[diff])

        self.state = SessionState(text=text, difficulty=diff)

        self._input_var.set("")
        self._entry.config(state="normal")
        self._entry.focus_set()

        self._timer_var.set(f"{self.TIME_LIMIT}s")
        self._wpm_var.set("0")
        self._acc_var.set("100%")
        self._chars_var.set("0")
        self._errors_var.set("0")
        self._status_var.set("Start typing to begin the timer…")
        self._update_progress(0)
        self._render_prompt()

    def _render_prompt(self):
        typed = self.state.typed
        text  = self.state.text

        self._prompt_text.config(state="normal")
        self._prompt_text.delete("1.0", "end")

        for i, ch in enumerate(text):
            if i < len(typed):
                tag = "correct" if typed[i] == ch else "wrong"
            elif i == len(typed):
                tag = "cursor"
            else:
                tag = "pending"
            self._prompt_text.insert("end", ch, tag)

        self._prompt_text.config(state="disabled")

    def _on_type(self, *_):
        if self.state.finished:
            return

        raw = self._input_var.get()

        # Start timer on first keystroke
        if not self.state.started and raw:
            self.state.started = True
            self.state.start_time = time.time()
            self._tick()

        # Build typed string: words completed + current partial word
        words_done = self.state.text.split()[: len(raw.split()) - 1] if raw else []
        self.state.typed = " ".join(words_done) + (" " if words_done else "") + raw.split()[-1] if raw else ""

        # Count errors in typed so far
        errors = sum(1 for a, b in zip(self.state.typed, self.state.text) if a != b)
        self.state.errors = errors

        self._update_stats()
        self._render_prompt()

        # Check completion
        if self.state.typed.rstrip() == self.state.text:
            self._finish()

    def _on_space(self, event):
        """Advance word on space."""
        if self.state.finished:
            return
        current = self._input_var.get().strip()
        if not current:
            return "break"
        self._input_var.set("")
        words = self.state.text.split()
        typed_words = self.state.typed.split() if self.state.typed.strip() else []
        new_index = len(typed_words)
        if new_index < len(words):
            self.state.typed = " ".join(typed_words + [current]) + " "
        self._update_stats()
        self._render_prompt()
        if self.state.typed.rstrip() == self.state.text:
            self._finish()
        return "break"

    def _on_backspace(self, _event):
        """Allow backspace within current word only."""
        return  # default behavior is fine

    def _tick(self):
        if self.state.finished or not self.state.started:
            return
        elapsed = time.time() - self.state.start_time
        remaining = max(0, self.TIME_LIMIT - elapsed)
        self._timer_var.set(f"{int(remaining)}s")
        self._update_progress(elapsed / self.TIME_LIMIT)
        self._update_stats()
        if remaining <= 0:
            self._finish()
        else:
            self._tick_id = self.root.after(self.TICK_MS, self._tick)

    def _update_stats(self):
        if not self.state.started:
            return
        elapsed = time.time() - self.state.start_time
        correct_chars = sum(1 for a, b in zip(self.state.typed, self.state.text) if a == b)
        total_typed = len(self.state.typed)
        wpm = (correct_chars / 5) / (elapsed / 60) if elapsed > 0 else 0
        accuracy = (correct_chars / total_typed * 100) if total_typed > 0 else 100.0
        self.state.wpm = wpm
        self.state.accuracy = accuracy
        self._wpm_var.set(str(int(wpm)))
        self._acc_var.set(f"{accuracy:.1f}%")
        self._chars_var.set(str(total_typed))
        self._errors_var.set(str(self.state.errors))

    def _update_progress(self, ratio: float):
        self._progress_canvas.update_idletasks()
        w = self._progress_canvas.winfo_width()
        self._progress_canvas.coords(self._prog_bar, 0, 0, int(w * min(ratio, 1.0)), 6)

    def _finish(self):
        if self.state.finished:
            return
        self.state.finished = True
        if self._tick_id:
            self.root.after_cancel(self._tick_id)
            self._tick_id = None

        elapsed = time.time() - self.state.start_time
        self._update_stats()
        self._update_progress(elapsed / self.TIME_LIMIT)
        self._entry.config(state="disabled")
        self._timer_var.set("Done!")

        wpm = self.state.wpm
        acc = self.state.accuracy

        # Save to DB
        self.db.save(
            self.state.difficulty, wpm, acc, elapsed,
            len(self.state.typed), self.state.errors
        )

        grade = "🏆 Excellent!" if wpm >= 70 else "👍 Good!" if wpm >= 45 else "🔥 Keep practicing!"
        self._status_var.set(
            f"{grade}  |  {wpm:.1f} WPM  ·  {acc:.1f}% accuracy  ·  {elapsed:.1f}s  — Press Start to retry"
        )

    # ── History window ────────────────────────────────────────

    def _show_history(self):
        win = tk.Toplevel(self.root)
        win.title("History & Leaderboard")
        win.configure(bg=self.T["bg"])
        win.geometry("760x480")

        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=12, pady=12)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook",       background=self.T["bg"],        borderwidth=0)
        style.configure("TNotebook.Tab",   background=self.T["surface"],
                        foreground=self.T["subtext"], padding=[12, 5])
        style.map("TNotebook.Tab",
                  background=[("selected", self.T["accent"])],
                  foreground=[("selected", "#ffffff")])

        # Summary tab
        f_sum = tk.Frame(nb, bg=self.T["bg"])
        nb.add(f_sum, text="📈  Summary")
        stats = self.db.get_stats()
        if stats[0]:
            for label, val in [("Total sessions", stats[0]),
                                ("Average WPM",   f"{stats[1]:.1f}"),
                                ("Best WPM",      f"{stats[2]:.1f}"),
                                ("Avg accuracy",  f"{stats[3]:.1f}%")]:
                row = tk.Frame(f_sum, bg=self.T["card"], pady=12)
                row.pack(fill="x", padx=30, pady=5)
                tk.Label(row, text=label, bg=self.T["card"],
                         fg=self.T["subtext"], font=("Helvetica", 11)).pack(side="left", padx=16)
                tk.Label(row, text=str(val), bg=self.T["card"],
                         fg=self.T["accent"], font=("Helvetica", 15, "bold")).pack(side="right", padx=16)
        else:
            tk.Label(f_sum, text="No sessions yet.", bg=self.T["bg"],
                     fg=self.T["subtext"], font=("Helvetica", 13)).pack(pady=40)

        # Leaderboard tab
        f_lb = tk.Frame(nb, bg=self.T["bg"])
        nb.add(f_lb, text="🏆  Top Scores")
        self._table(f_lb, ["Date", "Difficulty", "WPM", "Accuracy"],
                    self.db.get_top(10))

        # Recent tab
        f_rec = tk.Frame(nb, bg=self.T["bg"])
        nb.add(f_rec, text="🕐  Recent")
        self._table(f_rec,
                    ["Date", "Diff", "WPM", "Accuracy", "Duration", "Chars", "Errors"],
                    self.db.get_recent(20))

    def _table(self, parent, headers, rows):
        style = ttk.Style()
        style.configure("Treeview",
                        background=self.T["card"], foreground=self.T["text"],
                        fieldbackground=self.T["card"], rowheight=28,
                        font=("Helvetica", 10))
        style.configure("Treeview.Heading",
                        background=self.T["border"], foreground=self.T["accent"],
                        font=("Helvetica", 10, "bold"))
        style.map("Treeview", background=[("selected", self.T["accent"])])

        tree = ttk.Treeview(parent, columns=headers, show="headings", height=14)
        for h in headers:
            tree.heading(h, text=h)
            tree.column(h, anchor="center", width=max(80, 760 // len(headers) - 10))

        for r in rows:
            tree.insert("", "end", values=[str(v) for v in r])

        sb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=10)
        sb.pack(side="right", fill="y", pady=10, padx=(0, 8))

    # ── Theme ─────────────────────────────────────────────────

    def _toggle_theme(self):
        self._theme_name = "light" if self._theme_name == "dark" else "dark"
        self.T = THEMES[self._theme_name]
        label = "🌙 Dark" if self._theme_name == "light" else "☀ Light"
        self._theme_btn.config(text=label)
        # Rebuild UI in-place (simple: just restart)
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()
        self._new_test()

    def _on_close(self):
        self.db.close()
        self.root.destroy()


# ─────────────────────────── Entry ───────────────────────────

def main():
    root = tk.Tk()
    # Center window
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = 920, 660
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
    app = TypingSpeedApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
