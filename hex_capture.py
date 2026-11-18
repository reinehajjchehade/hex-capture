"""
Hex Capture Duel - tkinter GUI.  Run:  python hex_capture.py

Click a highlighted cell to claim it. Hover a cell to preview which enemy cells
would flip. The panel on the right shows what the AI searched on its last move.
"""

import math
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

from ai import best_move
from game import BLUE, EMPTY, NAMES, RED, Board, GameState

COLORS = {
    "bg": "#1e1f26", "panel": "#2a2c36", "text": "#eceff4", "muted": "#9aa0b4",
    EMPTY: "#3b3e4c", RED: "#e05a5a", BLUE: "#4f8fe6",
    "legal": "#59606f", "outline": "#14151a", "last": "#ffd166", "flip": "#ffffff",
}
DIFFICULTY = {"Easy (depth 1)": 1, "Medium (depth 3)": 3, "Hard (depth 5)": 5}
BOARD_SIZES = {"Small (37 cells)": 3, "Normal (61 cells)": 4}
AI_DELAY_MS = 450


class HexCaptureApp:
    def __init__(self, root):
        self.root = root
        root.title("Hex Capture Duel")
        root.configure(bg=COLORS["bg"])

        self.canvas = tk.Canvas(root, width=640, height=600, bg=COLORS["bg"], highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_hover)

        panel = tk.Frame(root, bg=COLORS["panel"], padx=16, pady=16)
        panel.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)
        lab = dict(bg=COLORS["panel"], fg=COLORS["text"], anchor="w", justify="left")

        tk.Label(panel, text="Hex Capture Duel", font=("Helvetica", 18, "bold"), **lab).pack(fill="x")
        self.score_lbl = tk.Label(panel, font=("Helvetica", 15), **lab)
        self.score_lbl.pack(fill="x", pady=(10, 0))
        self.turn_lbl = tk.Label(panel, font=("Helvetica", 12, "bold"), **lab)
        self.turn_lbl.pack(fill="x", pady=(4, 12))

        self.mode = tk.StringVar(value="You (Red) vs AI")
        self.diff = tk.StringVar(value="Medium (depth 3)")
        self.size = tk.StringVar(value="Normal (61 cells)")
        for title, var, options in (
                ("Mode", self.mode, ["You (Red) vs AI", "You (Blue) vs AI", "AI vs AI", "Two players"]),
                ("AI difficulty", self.diff, list(DIFFICULTY)),
                ("Board", self.size, list(BOARD_SIZES))):
            tk.Label(panel, text=title, font=("Helvetica", 10), bg=COLORS["panel"],
                     fg=COLORS["muted"], anchor="w").pack(fill="x")
            ttk.Combobox(panel, textvariable=var, values=options, state="readonly",
                         width=20).pack(fill="x", pady=(0, 8))

        tk.Button(panel, text="New game", command=self.new_game).pack(fill="x", pady=(4, 14))

        tk.Label(panel, text="AI search (last move)", font=("Helvetica", 10),
                 bg=COLORS["panel"], fg=COLORS["muted"], anchor="w").pack(fill="x")
        self.stats_lbl = tk.Label(panel, font=("Courier", 11), **lab)
        self.stats_lbl.pack(fill="x")

        rules = ("Rules\n"
                 "1. Claim an empty cell next to\n   one of yours.\n"
                 "2. Enemy cells touching it flip\n   if they now touch 3 or more\n   of your cells.\n"
                 "3. No move? You pass.\n"
                 "4. Most points when nobody\n   can move wins.")
        tk.Label(panel, text=rules, font=("Helvetica", 10), bg=COLORS["panel"],
                 fg=COLORS["muted"], anchor="w", justify="left").pack(fill="x", pady=(14, 0))

        self.pending_ai = None
        self.new_game()

    # ---------- game flow ----------
    def new_game(self):
        if self.pending_ai:
            self.root.after_cancel(self.pending_ai)
            self.pending_ai = None
        self.board = Board(radius=BOARD_SIZES[self.size.get()])
        self.state = GameState(self.board)
        self.last_move, self.last_flips, self.hover_flips = None, [], []
        self.stats_lbl.config(text="-")
        r = self.board.radius
        self.hex_size = min(600 / (math.sqrt(3) * (2 * r + 1)), 560 / (3 * r + 2))
        self.redraw()
        self.schedule_ai()

    def is_human(self, player):
        mode = self.mode.get()
        if mode == "Two players":
            return True
        if mode == "AI vs AI":
            return False
        human = RED if "Red" in mode else BLUE
        return player == human

    def apply(self, cell):
        info = self.state.play(cell)
        self.last_move, self.last_flips = cell, info[1]
        self.hover_flips = []
        self.redraw()
        self.schedule_ai()

    def schedule_ai(self):
        if self.state.is_over():
            return
        if not self.state.legal_moves():          # forced pass, for humans too
            self.pending_ai = self.root.after(AI_DELAY_MS, lambda: self.apply(None))
            return
        if not self.is_human(self.state.to_move):
            self.pending_ai = self.root.after(AI_DELAY_MS, self.ai_move)

    def ai_move(self):
        self.pending_ai = None
        depth = DIFFICULTY[self.diff.get()]
        move, value, stats = best_move(self.state, depth)
        self.stats_lbl.config(text=(f"player : {NAMES[self.state.to_move]}\n"
                                    f"depth  : {depth}\n"
                                    f"nodes  : {stats.nodes:,}\n"
                                    f"cutoffs: {stats.cutoffs:,}\n"
                                    f"time   : {stats.time * 1000:.0f} ms\n"
                                    f"eval   : {value:+.0f}"))
        self.apply(move)

    # ---------- input ----------
    def cell_at(self, x, y):
        best, best_d = None, self.hex_size * 0.95
        for i, (q, r) in enumerate(self.board.cells):
            cx, cy = self.center(q, r)
            d = math.hypot(x - cx, y - cy)
            if d < best_d:
                best, best_d = i, d
        return best

    def human_turn(self):
        return (not self.state.is_over() and self.is_human(self.state.to_move)
                and self.pending_ai is None)

    def on_click(self, event):
        if not self.human_turn():
            return
        cell = self.cell_at(event.x, event.y)
        if cell is not None and cell in self.state.legal_moves():
            self.apply(cell)

    def on_hover(self, event):
        flips = []
        if self.human_turn():
            cell = self.cell_at(event.x, event.y)
            if cell is not None and cell in self.state.legal_moves():
                flips = self.state.captures_for(cell, self.state.to_move)
        if flips != self.hover_flips:
            self.hover_flips = flips
            self.redraw()

    # ---------- drawing ----------
    def center(self, q, r):
        s = self.hex_size
        return 320 + s * math.sqrt(3) * (q + r / 2), 300 + s * 1.5 * r

    def hex_points(self, cx, cy, size):
        pts = []
        for k in range(6):
            a = math.radians(60 * k - 30)
            pts += [cx + size * math.cos(a), cy + size * math.sin(a)]
        return pts

    def redraw(self):
        c, st = self.canvas, self.state
        c.delete("all")
        legal = set(st.legal_moves()) if self.human_turn() else set()
        for i, (q, r) in enumerate(self.board.cells):
            cx, cy = self.center(q, r)
            owner = st.owner[i]
            fill = COLORS[owner] if owner != EMPTY else (COLORS["legal"] if i in legal else COLORS[EMPTY])
            outline, width = COLORS["outline"], 2
            if i == self.last_move:
                outline, width = COLORS["last"], 4
            elif i in self.last_flips:
                outline, width = COLORS["flip"], 3
            if i in self.hover_flips:
                outline, width = COLORS[st.to_move], 5
            c.create_polygon(self.hex_points(cx, cy, self.hex_size - 2), fill=fill,
                             outline=outline, width=width)
            dots = "•" * self.board.values[i]
            c.create_text(cx, cy, text=dots, fill=COLORS["text"],
                          font=("Helvetica", int(self.hex_size * 0.45), "bold"))

        self.score_lbl.config(text=f"Red {st.score[RED]}   :   {st.score[BLUE]} Blue")
        if st.is_over():
            w = st.winner()
            msg = "Draw!" if w is None else f"{NAMES[w]} wins!"
            self.turn_lbl.config(text=f"Game over - {msg}", fg=COLORS["last"])
        else:
            who = NAMES[st.to_move]
            tag = "your move" if self.is_human(st.to_move) else "AI thinking..."
            self.turn_lbl.config(text=f"{who} to move ({tag})", fg=COLORS[st.to_move])


def bring_to_front(root):
    """macOS often opens a Python/Tk window BEHIND the terminal. Force it to the front."""
    root.update_idletasks()
    root.deiconify()
    root.lift()
    root.attributes("-topmost", True)
    root.after(400, lambda: root.attributes("-topmost", False))
    root.focus_force()
    if sys.platform == "darwin":
        # Make the Python app the active macOS app (no extra install needed).
        try:
            subprocess.Popen(
                ["osascript", "-e",
                 'tell application "System Events" to set frontmost of the first '
                 f'process whose unix id is {os.getpid()} to true'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass


def main():
    root = tk.Tk()
    root.resizable(False, False)
    HexCaptureApp(root)
    bring_to_front(root)
    print("Hex Capture Duel window is open (close it, or press Ctrl+C here, to quit).")
    print(f"Tk version {tk.TkVersion}. If you see no window, check behind this terminal or in the Dock.")
    root.mainloop()


if __name__ == "__main__":
    main()
