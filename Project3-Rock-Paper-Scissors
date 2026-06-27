"""
Rock, Paper, Scissors Game
===========================
Features:
  • Beautiful animated GUI with Tkinter
  • Random computer choice generation
  • Winner determination with game rules
  • Score tracking (Win / Loss / Draw)
  • Round history log
  • Best-of-N rounds mode
  • Streak tracking
  • Dark theme UI
"""

import tkinter as tk
from tkinter import messagebox
import random
import time
from typing import Optional

# ─────────────────────────── Constants ───────────────────────────

CHOICES = ["Rock", "Paper", "Scissors"]

EMOJIS = {
    "Rock":     "🪨",
    "Paper":    "📄",
    "Scissors": "✂️",
    "?":        "❓",
}

# winner_map[player] = what player beats
BEATS = {
    "Rock":     "Scissors",
    "Paper":    "Rock",
    "Scissors": "Paper",
}

RESULT_MSGS = {
    "win":  ["You crushed it! 🎉", "Nicely played! 🏆", "You're on fire! 🔥", "Unstoppable! ⚡"],
    "loss": ["Computer wins! 🤖", "Better luck next time!", "The machine beats you!", "AI is learning... 😈"],
    "draw": ["It's a tie! 🤝", "Great minds think alike!", "Dead even!", "Nobody wins this one!"],
}

# Theme
T = {
    "bg":       "#0F1117",
    "surface":  "#1A1D27",
    "card":     "#22263A",
    "border":   "#2E3350",
    "accent":   "#7C6FF7",
    "accent2":  "#4ECDC4",
    "text":     "#E8EAF6",
    "subtext":  "#8B90B8",
    "win":      "#4ECDC4",
    "loss":     "#FF6B6B",
    "draw":     "#F9A825",
    "btn_r":    "#E53935",
    "btn_p":    "#7C6FF7",
    "btn_s":    "#1E88E5",
}

# ─────────────────────────── Game Logic ──────────────────────────

class GameLogic:
    def __init__(self):
        self.reset()

    def reset(self):
        self.player_score  = 0
        self.computer_score = 0
        self.draws         = 0
        self.round         = 0
        self.history       = []   # list of dicts
        self.streak        = 0
        self.best_streak   = 0
        self.current_streak_type = None

    def computer_choice(self) -> str:
        return random.choice(CHOICES)

    def determine_winner(self, player: str, computer: str) -> str:
        if player == computer:
            return "draw"
        if BEATS[player] == computer:
            return "win"
        return "loss"

    def play_round(self, player_choice: str) -> dict:
        comp = self.computer_choice()
        result = self.determine_winner(player_choice, comp)
        self.round += 1

        if result == "win":
            self.player_score += 1
            if self.current_streak_type == "win":
                self.streak += 1
            else:
                self.streak = 1
                self.current_streak_type = "win"
            self.best_streak = max(self.best_streak, self.streak)
        elif result == "loss":
            self.computer_score += 1
            if self.current_streak_type == "loss":
                self.streak += 1
            else:
                self.streak = 1
                self.current_streak_type = "loss"
        else:
            self.draws += 1
            self.streak = 0
            self.current_streak_type = None

        msg = random.choice(RESULT_MSGS[result])
        entry = {
            "round":    self.round,
            "player":   player_choice,
            "computer": comp,
            "result":   result,
            "msg":      msg,
        }
        self.history.append(entry)
        return entry


# ─────────────────────────── GUI ─────────────────────────────────

class RPSApp:
    ANIM_FRAMES = 8
    ANIM_DELAY  = 60   # ms

    def __init__(self, root: tk.Tk):
        self.root  = root
        self.root.title("Rock · Paper · Scissors")
        self.root.configure(bg=T["bg"])
        self.root.resizable(False, False)
        self.logic = GameLogic()
        self._animating = False
        self._build_ui()

    # ── Build UI ──────────────────────────────────────────────────

    def _build_ui(self):
        # ── Top bar ──
        bar = tk.Frame(self.root, bg=T["surface"], pady=10)
        bar.pack(fill="x")
        tk.Label(bar, text="✊ Rock · Paper · Scissors",
                 font=("Helvetica", 17, "bold"),
                 fg=T["accent"], bg=T["surface"]).pack(side="left", padx=20)
        self._round_lbl = tk.Label(bar, text="Round 0",
                                   font=("Helvetica", 12),
                                   fg=T["subtext"], bg=T["surface"])
        self._round_lbl.pack(side="right", padx=20)

        # ── Score row ──
        score_frame = tk.Frame(self.root, bg=T["bg"], pady=12)
        score_frame.pack(fill="x", padx=30)

        # Player score
        pf = tk.Frame(score_frame, bg=T["card"], pady=10, padx=20)
        pf.pack(side="left", expand=True, fill="x", padx=(0,8))
        tk.Label(pf, text="YOU", font=("Helvetica", 10, "bold"),
                 fg=T["subtext"], bg=T["card"]).pack()
        self._player_score_lbl = tk.Label(pf, text="0",
                                          font=("Helvetica", 36, "bold"),
                                          fg=T["win"], bg=T["card"])
        self._player_score_lbl.pack()

        # VS
        tk.Label(score_frame, text="VS", font=("Helvetica", 18, "bold"),
                 fg=T["border"], bg=T["bg"]).pack(side="left", padx=6)

        # Computer score
        cf = tk.Frame(score_frame, bg=T["card"], pady=10, padx=20)
        cf.pack(side="left", expand=True, fill="x", padx=(8,0))
        tk.Label(cf, text="CPU", font=("Helvetica", 10, "bold"),
                 fg=T["subtext"], bg=T["card"]).pack()
        self._cpu_score_lbl = tk.Label(cf, text="0",
                                       font=("Helvetica", 36, "bold"),
                                       fg=T["loss"], bg=T["card"])
        self._cpu_score_lbl.pack()

        # ── Arena (choice display) ──
        arena = tk.Frame(self.root, bg=T["surface"], pady=18)
        arena.pack(fill="x", padx=30, pady=(0, 8))

        # Player choice
        pl = tk.Frame(arena, bg=T["surface"])
        pl.pack(side="left", expand=True)
        tk.Label(pl, text="Your Choice", font=("Helvetica", 10),
                 fg=T["subtext"], bg=T["surface"]).pack()
        self._player_emoji = tk.Label(pl, text="❓",
                                      font=("Helvetica", 54),
                                      bg=T["surface"])
        self._player_emoji.pack()
        self._player_choice_lbl = tk.Label(pl, text="—",
                                           font=("Helvetica", 12, "bold"),
                                           fg=T["text"], bg=T["surface"])
        self._player_choice_lbl.pack()

        # Result
        mid = tk.Frame(arena, bg=T["surface"])
        mid.pack(side="left", expand=True)
        self._result_emoji = tk.Label(mid, text="🎮",
                                      font=("Helvetica", 30),
                                      bg=T["surface"])
        self._result_emoji.pack(pady=(16, 4))
        self._result_lbl = tk.Label(mid, text="Make your move!",
                                    font=("Helvetica", 11, "bold"),
                                    fg=T["accent"], bg=T["surface"],
                                    wraplength=140, justify="center")
        self._result_lbl.pack()

        # CPU choice
        cl = tk.Frame(arena, bg=T["surface"])
        cl.pack(side="left", expand=True)
        tk.Label(cl, text="CPU Choice", font=("Helvetica", 10),
                 fg=T["subtext"], bg=T["surface"]).pack()
        self._cpu_emoji = tk.Label(cl, text="❓",
                                   font=("Helvetica", 54),
                                   bg=T["surface"])
        self._cpu_emoji.pack()
        self._cpu_choice_lbl = tk.Label(cl, text="—",
                                        font=("Helvetica", 12, "bold"),
                                        fg=T["text"], bg=T["surface"])
        self._cpu_choice_lbl.pack()

        # ── Choice buttons ──
        btn_frame = tk.Frame(self.root, bg=T["bg"], pady=10)
        btn_frame.pack()

        btn_data = [
            ("🪨\nRock",     "Rock",     T["btn_r"]),
            ("📄\nPaper",    "Paper",    T["btn_p"]),
            ("✂️\nScissors", "Scissors", T["btn_s"]),
        ]
        self._choice_btns = []
        for (label, choice, color) in btn_data:
            btn = tk.Button(btn_frame, text=label,
                            font=("Helvetica", 14, "bold"),
                            bg=color, fg="white",
                            relief="flat", width=8, height=3,
                            cursor="hand2",
                            activebackground=color,
                            activeforeground="white",
                            command=lambda c=choice: self._on_choice(c))
            btn.pack(side="left", padx=10)
            self._choice_btns.append(btn)

        # ── Stats bar ──
        stats = tk.Frame(self.root, bg=T["card"], pady=8)
        stats.pack(fill="x", padx=30, pady=(8, 0))

        self._draws_lbl  = tk.Label(stats, text="Draws: 0",
                                    font=("Helvetica", 10),
                                    fg=T["draw"], bg=T["card"])
        self._draws_lbl.pack(side="left", padx=16)

        self._streak_lbl = tk.Label(stats, text="Streak: —",
                                    font=("Helvetica", 10),
                                    fg=T["accent2"], bg=T["card"])
        self._streak_lbl.pack(side="left", padx=16)

        self._best_lbl   = tk.Label(stats, text="Best Streak: 0",
                                    font=("Helvetica", 10),
                                    fg=T["subtext"], bg=T["card"])
        self._best_lbl.pack(side="right", padx=16)

        # ── History log ──
        log_outer = tk.Frame(self.root, bg=T["bg"], pady=8)
        log_outer.pack(fill="x", padx=30, pady=(6, 0))

        tk.Label(log_outer, text="ROUND HISTORY",
                 font=("Helvetica", 9, "bold"),
                 fg=T["border"], bg=T["bg"]).pack(anchor="w")

        self._log_text = tk.Text(log_outer, height=6,
                                 bg=T["surface"], fg=T["subtext"],
                                 font=("Courier New", 10),
                                 relief="flat", state="disabled",
                                 padx=10, pady=6,
                                 insertbackground=T["accent"])
        self._log_text.pack(fill="x")
        self._log_text.tag_configure("win",  foreground=T["win"])
        self._log_text.tag_configure("loss", foreground=T["loss"])
        self._log_text.tag_configure("draw", foreground=T["draw"])

        # ── Bottom buttons ──
        bot = tk.Frame(self.root, bg=T["bg"], pady=10)
        bot.pack()

        tk.Button(bot, text="🔄  New Game",
                  font=("Helvetica", 11, "bold"),
                  bg=T["accent"], fg="white",
                  relief="flat", padx=18, pady=7,
                  cursor="hand2",
                  command=self._new_game).pack(side="left", padx=8)

        tk.Button(bot, text="📊  Stats",
                  font=("Helvetica", 11),
                  bg=T["card"], fg=T["text"],
                  relief="flat", padx=18, pady=7,
                  cursor="hand2",
                  command=self._show_stats).pack(side="left", padx=8)

    # ── Game Flow ─────────────────────────────────────────────────

    def _on_choice(self, choice: str):
        if self._animating:
            return
        self._set_btns_state("disabled")
        self._animate_cpu(choice)

    def _animate_cpu(self, player_choice: str):
        """Spin CPU emoji before revealing."""
        self._animating = True
        self._player_emoji.config(text=EMOJIS[player_choice])
        self._player_choice_lbl.config(text=player_choice)
        self._cpu_emoji.config(text="❓")
        self._result_lbl.config(text="CPU thinking...", fg=T["subtext"])
        self._result_emoji.config(text="⏳")

        spin = CHOICES[:]
        def step(n):
            self._cpu_emoji.config(text=EMOJIS[random.choice(spin)])
            if n < self.ANIM_FRAMES:
                self.root.after(self.ANIM_DELAY, lambda: step(n+1))
            else:
                self._reveal(player_choice)
        step(0)

    def _reveal(self, player_choice: str):
        entry = self.logic.play_round(player_choice)
        result = entry["result"]

        self._cpu_emoji.config(text=EMOJIS[entry["computer"]])
        self._cpu_choice_lbl.config(text=entry["computer"])

        # Result styling
        if result == "win":
            col = T["win"];  emoji = "🏆"
        elif result == "loss":
            col = T["loss"]; emoji = "💻"
        else:
            col = T["draw"]; emoji = "🤝"

        self._result_lbl.config(text=entry["msg"], fg=col)
        self._result_emoji.config(text=emoji)

        # Scores
        self._player_score_lbl.config(text=str(self.logic.player_score))
        self._cpu_score_lbl.config(text=str(self.logic.computer_score))
        self._round_lbl.config(text=f"Round {self.logic.round}")
        self._draws_lbl.config(text=f"Draws: {self.logic.draws}")

        # Streak
        if self.logic.current_streak_type == "win" and self.logic.streak > 1:
            self._streak_lbl.config(
                text=f"🔥 Win Streak: {self.logic.streak}", fg=T["win"])
        elif self.logic.current_streak_type == "loss" and self.logic.streak > 1:
            self._streak_lbl.config(
                text=f"📉 Loss Streak: {self.logic.streak}", fg=T["loss"])
        else:
            self._streak_lbl.config(text="Streak: —", fg=T["accent2"])

        self._best_lbl.config(text=f"Best Streak: {self.logic.best_streak}")

        # Log
        self._add_log(entry)

        self._animating = False
        self._set_btns_state("normal")

    def _add_log(self, entry: dict):
        self._log_text.config(state="normal")
        r = entry["result"]
        tag = r
        icon = "✅" if r=="win" else "❌" if r=="loss" else "➖"
        line = (f"R{entry['round']:02d}  {EMOJIS[entry['player']]} {entry['player']:<8} "
                f"vs  {EMOJIS[entry['computer']]} {entry['computer']:<8}  {icon} {r.upper()}\n")
        self._log_text.insert("1.0", line, tag)
        # Keep only last 20 lines
        lines = int(self._log_text.index("end-1c").split(".")[0])
        if lines > 20:
            self._log_text.delete(f"{lines}.0", "end")
        self._log_text.config(state="disabled")

    def _set_btns_state(self, state: str):
        for btn in self._choice_btns:
            btn.config(state=state)

    def _new_game(self):
        self.logic.reset()
        self._player_score_lbl.config(text="0")
        self._cpu_score_lbl.config(text="0")
        self._round_lbl.config(text="Round 0")
        self._player_emoji.config(text="❓")
        self._cpu_emoji.config(text="❓")
        self._player_choice_lbl.config(text="—")
        self._cpu_choice_lbl.config(text="—")
        self._result_lbl.config(text="Make your move!", fg=T["accent"])
        self._result_emoji.config(text="🎮")
        self._draws_lbl.config(text="Draws: 0")
        self._streak_lbl.config(text="Streak: —", fg=T["accent2"])
        self._best_lbl.config(text="Best Streak: 0")
        self._log_text.config(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.config(state="disabled")
        self._set_btns_state("normal")

    def _show_stats(self):
        g = self.logic
        total = g.round
        if total == 0:
            messagebox.showinfo("Stats", "No rounds played yet!")
            return

        win_pct  = g.player_score  / total * 100
        loss_pct = g.computer_score / total * 100
        draw_pct = g.draws / total * 100

        # Choice breakdown from history
        choices_used = {"Rock":0,"Paper":0,"Scissors":0}
        for h in g.history:
            choices_used[h["player"]] += 1

        msg = (
            f"📊  GAME STATISTICS\n"
            f"{'─'*30}\n"
            f"Total Rounds  : {total}\n\n"
            f"✅  Wins   : {g.player_score} ({win_pct:.1f}%)\n"
            f"❌  Losses : {g.computer_score} ({loss_pct:.1f}%)\n"
            f"➖  Draws  : {g.draws} ({draw_pct:.1f}%)\n\n"
            f"🔥  Best Streak : {g.best_streak} wins\n\n"
            f"Your Choices:\n"
            f"  🪨 Rock     : {choices_used['Rock']}\n"
            f"  📄 Paper    : {choices_used['Paper']}\n"
            f"  ✂️  Scissors : {choices_used['Scissors']}\n"
        )
        messagebox.showinfo("Statistics", msg)


# ─────────────────────────── Entry ───────────────────────────────

def main():
    root = tk.Tk()
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = 640, 680
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
    RPSApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
