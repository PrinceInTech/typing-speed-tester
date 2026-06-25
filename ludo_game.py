"""
Ludo Game — Python + Tkinter
==============================
Features:
  • 2–4 players (Human or AI)
  • Full Ludo rules: safe squares, home column, captures, six-re-roll
  • AI opponent with smart move selection
  • Animated token movement
  • Winner detection & scoreboard
  • Beautiful board with classic color zones
"""

import tkinter as tk
from tkinter import messagebox, font as tkfont
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict

# ═══════════════════════════════════════════════════════════
#  CONSTANTS & BOARD LAYOUT
# ═══════════════════════════════════════════════════════════

CELL   = 52          # pixels per cell
COLS   = 15          # board grid columns
ROWS   = 15

# Colors for 4 players
PLAYER_COLORS = {
    0: {"name": "Red",    "main": "#E53935", "light": "#FFCDD2", "dark": "#B71C1C", "home": "#FFEBEE"},
    1: {"name": "Green",  "main": "#43A047", "light": "#C8E6C9", "dark": "#1B5E20", "home": "#E8F5E9"},
    2: {"name": "Yellow", "main": "#F9A825", "light": "#FFF9C4", "dark": "#F57F17", "home": "#FFFDE7"},
    3: {"name": "Blue",   "main": "#1E88E5", "light": "#BBDEFB", "dark": "#0D47A1", "home": "#E3F2FD"},
}

BOARD_BG   = "#F5F0E8"
SAFE_COLOR = "#A5D6A7"
CENTER_COL = "#FFFFFF"
BORDER_COL = "#5D4037"

# Safe squares (0-indexed path positions)
SAFE_SQUARES = {0, 8, 13, 21, 26, 34, 39, 47}

# Each player's path: list of (row, col) grid coords
# The path is the standard 52-step outer path + 5-step home column
def _build_paths():
    """Build the (row,col) path for each of the 4 players."""
    # Standard Ludo outer path — 52 squares, starting positions differ per player
    outer = [
        # Bottom of left col going up (col=6, rows 14→8)
        (14,6),(13,6),(12,6),(11,6),(10,6),(9,6),(8,6),
        # Top-left corner going right (row=8, cols 6→0... wait)
        # We'll use standard ludo cell mapping:
        # Row 6 going left col 6→0
        (8,5),(8,4),(8,3),(8,2),(8,1),(8,0),
        # Up col 0 row 8→6
        (7,0),(6,0),
        # Right row 6 cols 0→6
        (6,1),(6,2),(6,3),(6,4),(6,5),
        # Up col 6 row 6→0 (entry to green home col)
        (5,6),(4,6),(3,6),(2,6),(1,6),(0,6),
        # Right row 0 cols 6→8
        (0,7),(0,8),
        # Down col 8 rows 0→6
        (1,8),(2,8),(3,8),(4,8),(5,8),
        # Right row 6 cols 8→14
        (6,9),(6,10),(6,11),(6,12),(6,13),(6,14),
        # Down col 14 rows 6→8
        (7,14),(8,14),
        # Left row 8 cols 14→8
        (8,13),(8,12),(8,11),(8,10),(8,9),
        # Down col 8 rows 8→14
        (9,8),(10,8),(11,8),(12,8),(13,8),(14,8),
        # Left row 14 cols 8→6
        (14,7),
    ]
    # Player start indices on outer path
    starts = [0, 13, 26, 39]
    paths = []
    for p in range(4):
        s = starts[p]
        path = outer[s:] + outer[:s]
        # Home columns (5 steps inward)
        home_cols = [
            [(13,7),(12,7),(11,7),(10,7),(9,7)],   # Red
            [(7,1),(7,2),(7,3),(7,4),(7,5)],         # Green
            [(1,7),(2,7),(3,7),(4,7),(5,7)],         # Yellow
            [(7,13),(7,12),(7,11),(7,10),(7,9)],     # Blue
        ]
        path = path + home_cols[p]
        paths.append(path)
    return paths

PATHS = _build_paths()

# Yard (starting home) positions for each player's 4 tokens
YARDS: Dict[int, List[Tuple[int,int]]] = {
    0: [(12,2),(12,3),(13,2),(13,3)],   # Red  — bottom-left
    1: [(2,2),(2,3),(3,2),(3,3)],        # Green — top-left
    2: [(2,11),(2,12),(3,11),(3,12)],   # Yellow — top-right
    3: [(12,11),(12,12),(13,11),(13,12)],# Blue  — bottom-right
}

# ═══════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════

@dataclass
class Token:
    player_id: int
    token_id:  int
    pos: int = -1          # -1 = yard, 0-51 = outer path, 52-56 = home col, 57 = home
    finished: bool = False

    @property
    def in_yard(self): return self.pos == -1
    @property
    def at_home(self): return self.finished

    def can_move(self, steps: int) -> bool:
        if self.finished: return False
        if self.in_yard:  return steps == 6
        new_pos = self.pos + steps
        return new_pos <= 57

@dataclass
class Player:
    player_id: int
    name: str
    is_ai: bool = False
    tokens: List[Token] = field(default_factory=list)
    finished_tokens: int = 0

    def __post_init__(self):
        self.tokens = [Token(self.player_id, i) for i in range(4)]

    @property
    def has_won(self): return self.finished_tokens == 4

    def movable_tokens(self, dice: int) -> List[Token]:
        return [t for t in self.tokens if t.can_move(dice)]

# ═══════════════════════════════════════════════════════════
#  GAME LOGIC
# ═══════════════════════════════════════════════════════════

class LudoGame:
    def __init__(self, player_configs: List[dict]):
        self.players: List[Player] = []
        for i, cfg in enumerate(player_configs):
            self.players.append(Player(i, cfg["name"], cfg.get("ai", False)))
        self.current_player = 0
        self.dice_value = 0
        self.winner: Optional[Player] = None
        self.consecutive_sixes = 0
        self.turn_count = 0

    @property
    def current(self) -> Player:
        return self.players[self.current_player]

    def roll_dice(self) -> int:
        self.dice_value = random.randint(1, 6)
        return self.dice_value

    def get_board_pos(self, token: Token) -> Tuple[int,int]:
        """Return (row,col) for drawing."""
        if token.in_yard:
            return YARDS[token.player_id][token.token_id]
        if token.finished:
            return (7, 7)  # center
        idx = min(token.pos, len(PATHS[token.player_id]) - 1)
        return PATHS[token.player_id][idx]

    def _path_pos_to_global(self, player_id: int, path_pos: int) -> Tuple[int,int]:
        if path_pos < 0 or path_pos >= len(PATHS[player_id]):
            return (-1,-1)
        return PATHS[player_id][path_pos]

    def move_token(self, token: Token) -> dict:
        """Move token by dice_value. Returns result dict."""
        result = {"captured": [], "got_six": self.dice_value == 6,
                  "entered": False, "finished": False}

        if token.in_yard and self.dice_value == 6:
            token.pos = 0
            result["entered"] = True
        else:
            token.pos += self.dice_value

        # Check finish
        if token.pos >= 57:
            token.pos = 57
            token.finished = True
            token.player_id  # keep id
            self.players[token.player_id].finished_tokens += 1
            result["finished"] = True
            if self.players[token.player_id].has_won:
                self.winner = self.players[token.player_id]
            return result

        # Check capture (only on outer 52 squares)
        if token.pos < 52:
            cell = PATHS[token.player_id][token.pos]
            path_pos_on_outer = token.pos  # 0-51
            # Check if safe square
            is_safe = path_pos_on_outer in SAFE_SQUARES
            if not is_safe:
                for other_player in self.players:
                    if other_player.player_id == token.player_id:
                        continue
                    for other_token in other_player.tokens:
                        if other_token.in_yard or other_token.finished:
                            continue
                        if other_token.pos >= 52:
                            continue
                        other_cell = PATHS[other_token.player_id][other_token.pos]
                        if other_cell == cell:
                            other_token.pos = -1  # send to yard
                            result["captured"].append(other_token)

        return result

    def ai_choose_token(self) -> Optional[Token]:
        """Simple AI: prefer captures > entries > furthest token."""
        player = self.current
        movable = player.movable_tokens(self.dice_value)
        if not movable:
            return None

        # Priority 1: capture opponent
        for token in movable:
            sim_pos = 0 if token.in_yard else token.pos + self.dice_value
            if sim_pos < 52:
                cell = PATHS[player.player_id][sim_pos]
                for op in self.players:
                    if op.player_id == player.player_id: continue
                    for ot in op.tokens:
                        if ot.in_yard or ot.finished or ot.pos >= 52: continue
                        if PATHS[ot.player_id][ot.pos] == cell:
                            return token

        # Priority 2: enter token from yard
        if self.dice_value == 6:
            yard_tokens = [t for t in movable if t.in_yard]
            if yard_tokens:
                return yard_tokens[0]

        # Priority 3: move furthest token
        active = [t for t in movable if not t.in_yard]
        if active:
            return max(active, key=lambda t: t.pos)

        return movable[0]

    def next_turn(self, got_extra: bool):
        if not got_extra:
            self.consecutive_sixes = 0
            self.current_player = (self.current_player + 1) % len(self.players)
            # Skip finished players
            attempts = 0
            while self.players[self.current_player].has_won and attempts < 4:
                self.current_player = (self.current_player + 1) % len(self.players)
                attempts += 1
        self.turn_count += 1

# ═══════════════════════════════════════════════════════════
#  GUI
# ═══════════════════════════════════════════════════════════

class LudoApp:
    ANIM_STEPS = 8
    ANIM_DELAY = 40   # ms per animation frame

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Ludo Game")
        self.root.configure(bg="#1A1A2E")
        self.root.resizable(False, False)
        self.game: Optional[LudoGame] = None
        self.token_ovals: Dict[int, int] = {}   # token_uid -> canvas oval id
        self.token_texts: Dict[int, int] = {}   # token_uid -> canvas text id
        self._animating = False
        self._show_menu()

    def _token_uid(self, player_id, token_id):
        return player_id * 4 + token_id

    # ── Menu ──────────────────────────────────────────────────────────────

    def _show_menu(self):
        for w in self.root.winfo_children():
            w.destroy()

        menu = tk.Frame(self.root, bg="#1A1A2E")
        menu.pack(expand=True, fill="both", padx=40, pady=30)

        tk.Label(menu, text="🎲 LUDO", font=("Helvetica", 42, "bold"),
                 fg="#F9A825", bg="#1A1A2E").pack(pady=(10, 0))
        tk.Label(menu, text="Classic Board Game", font=("Helvetica", 13),
                 fg="#90CAF9", bg="#1A1A2E").pack(pady=(0, 28))

        # Player config
        self._player_vars = []
        for i in range(4):
            c = PLAYER_COLORS[i]
            row = tk.Frame(menu, bg="#16213E", bd=0)
            row.pack(fill="x", pady=5, ipady=8, ipadx=10)

            tk.Label(row, text="●", font=("Helvetica", 20),
                     fg=c["main"], bg="#16213E").pack(side="left", padx=(14,6))
            tk.Label(row, text=c["name"], font=("Helvetica", 13, "bold"),
                     fg="#E8EAF6", bg="#16213E", width=8, anchor="w").pack(side="left")

            var = tk.StringVar(value="Human" if i == 0 else "AI")
            self._player_vars.append(var)
            for opt in ("Human", "AI", "Off"):
                rb = tk.Radiobutton(row, text=opt, variable=var, value=opt,
                                    bg="#16213E", fg="#B0BEC5",
                                    selectcolor=c["main"],
                                    activebackground="#16213E",
                                    activeforeground=c["main"],
                                    font=("Helvetica", 11))
                rb.pack(side="left", padx=10)

        tk.Button(menu, text="▶  START GAME",
                  font=("Helvetica", 14, "bold"),
                  bg="#F9A825", fg="#1A1A2E",
                  relief="flat", padx=30, pady=12,
                  cursor="hand2",
                  command=self._start_game).pack(pady=28)

    def _start_game(self):
        configs = []
        for i, var in enumerate(self._player_vars):
            v = var.get()
            if v == "Off": continue
            configs.append({"name": PLAYER_COLORS[i]["name"],
                            "ai": v == "AI",
                            "_pid": i})

        if len(configs) < 2:
            messagebox.showwarning("Ludo", "Please enable at least 2 players!")
            return

        # Remap player ids to be consecutive but keep colors
        # We'll hack: just use original player ids stored in _pid
        real_configs = []
        self._active_pids = []
        for cfg in configs:
            real_configs.append({"name": cfg["name"], "ai": cfg["ai"]})
            self._active_pids.append(cfg["_pid"])

        self.game = LudoGame(real_configs)
        # Patch player ids to match colors
        for i, pid in enumerate(self._active_pids):
            self.game.players[i].player_id = pid
            for t in self.game.players[i].tokens:
                t.player_id = pid

        self._build_game_ui()
        self._update_info()
        self._maybe_ai_turn()

    # ── Game UI ───────────────────────────────────────────────────────────

    def _build_game_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        outer = tk.Frame(self.root, bg="#1A1A2E")
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        # Board canvas
        bw = CELL * COLS
        bh = CELL * ROWS
        self.canvas = tk.Canvas(outer, width=bw, height=bh,
                                bg=BOARD_BG, highlightthickness=2,
                                highlightbackground=BORDER_COL)
        self.canvas.pack(side="left")

        # Right panel
        panel = tk.Frame(outer, bg="#16213E", width=220)
        panel.pack(side="left", fill="y", padx=(10,0))
        panel.pack_propagate(False)

        tk.Label(panel, text="🎲 LUDO", font=("Helvetica", 20, "bold"),
                 fg="#F9A825", bg="#16213E").pack(pady=(18,4))

        # Turn indicator
        self._turn_label = tk.Label(panel, text="", font=("Helvetica", 13, "bold"),
                                    fg="#FFFFFF", bg="#16213E", wraplength=200)
        self._turn_label.pack(pady=6)

        # Dice display
        self._dice_label = tk.Label(panel, text="⚀", font=("Helvetica", 54),
                                    fg="#F9A825", bg="#16213E")
        self._dice_label.pack(pady=6)

        self._dice_val_label = tk.Label(panel, text="Roll the dice!",
                                        font=("Helvetica", 11), fg="#90CAF9", bg="#16213E")
        self._dice_val_label.pack()

        # Roll button
        self._roll_btn = tk.Button(panel, text="🎲  Roll Dice",
                                   font=("Helvetica", 13, "bold"),
                                   bg="#F9A825", fg="#1A1A2E",
                                   relief="flat", padx=16, pady=10,
                                   cursor="hand2",
                                   command=self._on_roll)
        self._roll_btn.pack(pady=14)

        # Status
        self._status_label = tk.Label(panel, text="", font=("Helvetica", 10),
                                      fg="#B0BEC5", bg="#16213E", wraplength=200,
                                      justify="center")
        self._status_label.pack(pady=4)

        # Scores
        tk.Label(panel, text="SCORES", font=("Helvetica", 10, "bold"),
                 fg="#546E7A", bg="#16213E").pack(pady=(16,4))

        self._score_labels = {}
        for i, pid in enumerate(self._active_pids):
            c = PLAYER_COLORS[pid]
            row = tk.Frame(panel, bg="#16213E")
            row.pack(fill="x", padx=14, pady=2)
            tk.Label(row, text="●", fg=c["main"], bg="#16213E",
                     font=("Helvetica", 14)).pack(side="left")
            lbl = tk.Label(row, text=f"{c['name']}: 0/4",
                           fg="#CFD8DC", bg="#16213E", font=("Helvetica", 11))
            lbl.pack(side="left", padx=6)
            self._score_labels[pid] = lbl

        # New Game button
        tk.Button(panel, text="↩  New Game",
                  font=("Helvetica", 11),
                  bg="#37474F", fg="#ECEFF1",
                  relief="flat", padx=12, pady=6,
                  cursor="hand2",
                  command=self._show_menu).pack(side="bottom", pady=16)

        self._draw_board()
        self._draw_all_tokens()

    # ── Board Drawing ─────────────────────────────────────────────────────

    def _cell_xy(self, row, col) -> Tuple[int,int,int,int]:
        x0 = col * CELL
        y0 = row * CELL
        return x0, y0, x0+CELL, y0+CELL

    def _draw_board(self):
        c = self.canvas

        # Background grid
        for r in range(ROWS):
            for col in range(COLS):
                x0,y0,x1,y1 = self._cell_xy(r, col)
                c.create_rectangle(x0,y0,x1,y1, fill=BOARD_BG, outline="#D7CCC8", width=1)

        # Colored zones — 3x3 home yards per player
        zones = [
            (0, 0, 5, 5, 0),    # Red — top-left... wait, standard ludo:
            # Red bottom-left, Green top-left, Yellow top-right, Blue bottom-right
        ]
        yard_rects = [
            (9, 0, 14, 5, 0),   # Red  bottom-left
            (0, 0, 5, 5, 1),    # Green top-left
            (0, 9, 5, 14, 2),   # Yellow top-right
            (9, 9, 14, 14, 3),  # Blue  bottom-right
        ]
        for (r0,c0,r1,c1,pid) in yard_rects:
            col_info = PLAYER_COLORS[pid]
            x0,y0,_,_ = self._cell_xy(r0, c0)
            _,_,x1,y1 = self._cell_xy(r1, c1)
            c.create_rectangle(x0,y0,x1,y1, fill=col_info["main"],
                                outline=col_info["dark"], width=3)
            # Inner white yard box
            pad = CELL
            c.create_rectangle(x0+pad,y0+pad,x1-pad,y1-pad,
                                fill=col_info["home"], outline=col_info["dark"], width=2)

        # Color the home columns (inner 5 squares per player)
        home_col_cells = [
            [(13,7),(12,7),(11,7),(10,7),(9,7)],   # Red
            [(7,1),(7,2),(7,3),(7,4),(7,5)],        # Green
            [(1,7),(2,7),(3,7),(4,7),(5,7)],        # Yellow
            [(7,13),(7,12),(7,11),(7,10),(7,9)],    # Blue
        ]
        for pid, cells in enumerate(home_col_cells):
            col_info = PLAYER_COLORS[pid]
            for (r,col) in cells:
                x0,y0,x1,y1 = self._cell_xy(r,col)
                c.create_rectangle(x0,y0,x1,y1,
                                   fill=col_info["light"], outline="#B0BEC5", width=1)

        # Safe squares — draw star
        for sq in SAFE_SQUARES:
            for pid in range(4):
                if sq < len(PATHS[pid]):
                    r,col = PATHS[pid][sq]
                    x0,y0,x1,y1 = self._cell_xy(r,col)
                    c.create_rectangle(x0,y0,x1,y1,fill=SAFE_COLOR,outline="#81C784",width=1)
                    cx,cy = (x0+x1)//2, (y0+y1)//2
                    c.create_text(cx,cy,text="★",font=("Helvetica",14),fill="#2E7D32")
                    break  # draw once

        # Center triangle arrows for home columns
        arrow_data = [
            ("▲", 14, 7, 0),   # Red — pointing up
            ("▶", 7, 1, 1),    # Green — pointing right
            ("▼", 1, 7, 2),    # Yellow — pointing down
            ("◀", 7, 13, 3),   # Blue — pointing left
        ]
        for (arrow, r, col, pid) in arrow_data:
            x0,y0,x1,y1 = self._cell_xy(r,col)
            cx,cy=(x0+x1)//2,(y0+y1)//2
            c.create_text(cx,cy,text=arrow,font=("Helvetica",18,"bold"),
                          fill=PLAYER_COLORS[pid]["main"])

        # Center — winning home
        cx0 = 6*CELL; cy0 = 6*CELL
        cx1 = 9*CELL; cy1 = 9*CELL
        # Draw 4 colored triangles
        mid = 7.5*CELL
        triangles = [
            ([cx0,cy0, mid,mid, cx1,cy0], 2),   # top — Yellow
            ([cx0,cy1, mid,mid, cx1,cy1], 0),   # bottom — Red
            ([cx0,cy0, mid,mid, cx0,cy1], 1),   # left — Green
            ([cx1,cy0, mid,mid, cx1,cy1], 3),   # right — Blue
        ]
        for (pts, pid) in triangles:
            c.create_polygon(pts, fill=PLAYER_COLORS[pid]["light"],
                             outline=PLAYER_COLORS[pid]["main"], width=1)
        c.create_text(mid, mid, text="🏠", font=("Helvetica", 22))

        # Outer border
        c.create_rectangle(0,0,COLS*CELL,ROWS*CELL,
                           outline=BORDER_COL, width=3)

    def _draw_all_tokens(self):
        self.canvas.delete("token")
        self.token_ovals.clear()
        self.token_texts.clear()

        for player in self.game.players:
            pid = player.player_id
            col_info = PLAYER_COLORS[pid]
            for token in player.tokens:
                uid = self._token_uid(pid, token.token_id)
                r, col = self.game.get_board_pos(token)
                x0,y0,x1,y1 = self._cell_xy(r, col)
                # Offset tokens within same cell
                off_x, off_y = self._token_offset(token.token_id)
                cx = (x0+x1)//2 + off_x
                cy = (y0+y1)//2 + off_y
                rad = 16
                ov = self.canvas.create_oval(cx-rad, cy-rad, cx+rad, cy+rad,
                                             fill=col_info["main"],
                                             outline=col_info["dark"], width=2,
                                             tags="token")
                tx = self.canvas.create_text(cx, cy,
                                             text=str(token.token_id+1),
                                             font=("Helvetica", 10, "bold"),
                                             fill="white", tags="token")
                self.token_ovals[uid] = ov
                self.token_texts[uid] = tx

    def _token_offset(self, tid):
        offsets = [(-10,-10),(10,-10),(-10,10),(10,10)]
        return offsets[tid]

    def _highlight_movable(self, tokens):
        """Pulse highlight movable tokens."""
        for t in tokens:
            uid = self._token_uid(t.player_id, t.token_id)
            ov = self.token_ovals.get(uid)
            if ov:
                self.canvas.itemconfig(ov, outline="#FFFF00", width=4)
        # Bind click
        self.canvas.tag_bind("token", "<Button-1>", self._on_token_click)
        self._movable_tokens = tokens

    def _clear_highlight(self):
        for player in self.game.players:
            pid = player.player_id
            for token in player.tokens:
                uid = self._token_uid(pid, token.token_id)
                ov = self.token_ovals.get(uid)
                if ov:
                    self.canvas.itemconfig(ov, outline=PLAYER_COLORS[pid]["dark"], width=2)
        self.canvas.tag_unbind("token", "<Button-1>")
        self._movable_tokens = []

    def _on_token_click(self, event):
        if self._animating: return
        # Find which token was clicked
        items = self.canvas.find_overlapping(event.x-5, event.y-5, event.x+5, event.y+5)
        for item in items:
            for t in self._movable_tokens:
                uid = self._token_uid(t.player_id, t.token_id)
                if item in (self.token_ovals.get(uid), self.token_texts.get(uid)):
                    self._clear_highlight()
                    self._do_move(t)
                    return

    # ── Game Flow ─────────────────────────────────────────────────────────

    def _update_info(self):
        if not self.game: return
        player = self.game.current
        pid = player.player_id
        c = PLAYER_COLORS[pid]
        ai_tag = " (AI)" if player.is_ai else ""
        self._turn_label.config(text=f"{c['name']}{ai_tag}'s Turn",
                                fg=c["main"])
        for p in self.game.players:
            ppid = p.player_id
            lbl = self._score_labels.get(ppid)
            if lbl:
                lbl.config(text=f"{PLAYER_COLORS[ppid]['name']}: {p.finished_tokens}/4")

    def _dice_face(self, val):
        faces = ["⚀","⚁","⚂","⚃","⚄","⚅"]
        return faces[val-1] if 1 <= val <= 6 else "🎲"

    def _on_roll(self):
        if self._animating: return
        player = self.game.current
        if player.is_ai: return
        self._roll_btn.config(state="disabled")
        self._animate_dice_roll(lambda: self._after_roll())

    def _animate_dice_roll(self, callback):
        self._animating = True
        steps = 8
        def step(n):
            self._dice_label.config(text=self._dice_face(random.randint(1,6)))
            if n < steps:
                self.root.after(60, lambda: step(n+1))
            else:
                val = self.game.roll_dice()
                self._dice_label.config(text=self._dice_face(val))
                self._dice_val_label.config(text=f"Rolled: {val}")
                self._animating = False
                callback()
        step(0)

    def _after_roll(self):
        player = self.game.current
        val = self.game.dice_value
        movable = player.movable_tokens(val)

        if val == 6:
            self.game.consecutive_sixes += 1
            if self.game.consecutive_sixes >= 3:
                self._status_label.config(text="3 sixes! Turn skipped.")
                self.game.consecutive_sixes = 0
                self.game.next_turn(False)
                self._update_info()
                self._roll_btn.config(state="normal")
                self._maybe_ai_turn()
                return

        if not movable:
            self._status_label.config(text="No moves available. Next turn!")
            self.root.after(900, self._pass_turn)
            return

        if len(movable) == 1:
            self._do_move(movable[0])
        else:
            self._status_label.config(text="Click a token to move it")
            self._highlight_movable(movable)

    def _pass_turn(self):
        self.game.next_turn(False)
        self._update_info()
        self._roll_btn.config(state="normal")
        self._maybe_ai_turn()

    def _do_move(self, token: Token):
        self._animating = True
        self._roll_btn.config(state="disabled")
        steps = self.game.dice_value
        start_pos = token.pos
        target_pos = -1 if token.in_yard else token.pos + steps

        # Animate step by step
        def animate_step(step_n):
            if token.in_yard and step_n == 0:
                token.pos = 0
            elif not token.in_yard:
                if step_n > 0:
                    token.pos = min(start_pos + step_n, 57)

            self._redraw_token(token)

            if step_n < (1 if start_pos == -1 else steps):
                self.root.after(self.ANIM_DELAY, lambda: animate_step(step_n+1))
            else:
                self._finish_move(token)

        animate_step(0)

    def _finish_move(self, token: Token):
        result = self.game.move_token(token)
        # Re-sync: token already at final pos from animation
        self._draw_all_tokens()
        self._animating = False

        if self.game.winner:
            self._show_winner(self.game.winner)
            return

        pid = token.player_id
        msgs = []
        if result["entered"]:  msgs.append("Token entered! 🎉")
        if result["captured"]: msgs.append(f"Captured {len(result['captured'])} token(s)! ⚔️")
        if result["finished"]: msgs.append("Token reached home! 🏠")
        self._status_label.config(text=" ".join(msgs) if msgs else "")

        got_extra = result["got_six"] or result["captured"] or result["finished"]
        self.game.next_turn(got_extra)
        self._update_info()
        self._roll_btn.config(state="normal")
        self._maybe_ai_turn()

    def _redraw_token(self, token):
        pid = token.player_id
        uid = self._token_uid(pid, token.token_id)
        r, col = self.game.get_board_pos(token)
        x0,y0,x1,y1 = self._cell_xy(r, col)
        off_x, off_y = self._token_offset(token.token_id)
        cx = (x0+x1)//2 + off_x
        cy = (y0+y1)//2 + off_y
        rad = 16
        ov = self.token_ovals.get(uid)
        tx = self.token_texts.get(uid)
        if ov:
            self.canvas.coords(ov, cx-rad, cy-rad, cx+rad, cy+rad)
        if tx:
            self.canvas.coords(tx, cx, cy)

    def _maybe_ai_turn(self):
        if not self.game or self.game.winner: return
        player = self.game.current
        if player.is_ai:
            self._roll_btn.config(state="disabled")
            self.root.after(700, self._ai_roll)

    def _ai_roll(self):
        self._animate_dice_roll(lambda: self._ai_after_roll())

    def _ai_after_roll(self):
        player = self.game.current
        val = self.game.dice_value

        if val == 6:
            self.game.consecutive_sixes += 1
            if self.game.consecutive_sixes >= 3:
                self.game.consecutive_sixes = 0
                self.game.next_turn(False)
                self._update_info()
                self._roll_btn.config(state="normal")
                self._maybe_ai_turn()
                return

        token = self.game.ai_choose_token()
        if token is None:
            self._status_label.config(text=f"{PLAYER_COLORS[player.player_id]['name']} AI: No moves.")
            self.root.after(700, self._pass_turn)
        else:
            self.root.after(400, lambda: self._do_move(token))

    def _show_winner(self, player: Player):
        pid = player.player_id
        c = PLAYER_COLORS[pid]
        self._roll_btn.config(state="disabled")
        self._turn_label.config(text=f"🏆 {c['name']} WINS!", fg=c["main"])
        self._status_label.config(text="Congratulations! 🎉")

        win_win = tk.Toplevel(self.root)
        win_win.title("Winner!")
        win_win.configure(bg="#1A1A2E")
        win_win.geometry("320x220")
        win_win.resizable(False, False)

        tk.Label(win_win, text="🏆", font=("Helvetica", 48),
                 bg="#1A1A2E").pack(pady=(20,4))
        tk.Label(win_win, text=f"{c['name']} Wins!",
                 font=("Helvetica", 22, "bold"),
                 fg=c["main"], bg="#1A1A2E").pack()
        tk.Label(win_win, text=f"In {self.game.turn_count} turns",
                 font=("Helvetica", 12), fg="#90CAF9", bg="#1A1A2E").pack(pady=4)

        tk.Button(win_win, text="Play Again",
                  font=("Helvetica", 13, "bold"),
                  bg=c["main"], fg="white",
                  relief="flat", padx=20, pady=8,
                  command=lambda: [win_win.destroy(), self._show_menu()]
                  ).pack(pady=16)


# ═══════════════════════════════════════════════════════════
#  ENTRY
# ═══════════════════════════════════════════════════════════

def main():
    root = tk.Tk()
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    bw = CELL * COLS
    pw = 230
    w = bw + pw + 30
    h = CELL * ROWS + 20
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
    LudoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
