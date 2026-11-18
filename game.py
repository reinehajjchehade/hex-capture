"""
Hex Capture Duel - game rules.

Board: a hexagon of hexagonal cells (radius 3 -> 37 cells), axial coordinates (q, r).
Every cell is worth 1, 2 or 3 points. Values are point-symmetric, so neither side
gets a better board.

Rules
  1. RED starts in one corner, BLUE in the opposite corner. RED moves first.
  2. On your turn, claim one EMPTY cell that touches a cell you already own.
  3. Capture: every enemy cell touching the new cell flips to you if it now
     touches 3 or more of your cells (the new cell counts).
  4. If you have no legal move you pass. The game ends when nobody can move.
  5. Score = sum of the values of your cells. Highest score wins.
"""

import random

EMPTY, RED, BLUE = 0, 1, 2
NAMES = {RED: "Red", BLUE: "Blue"}
CAPTURE_COUNT = 3   # an enemy cell touching this many of your cells flips
DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]


def other(player):
    return BLUE if player == RED else RED


class Board:
    """Static board geometry: cell list, neighbour lists and cell values."""

    def __init__(self, radius=3, seed=7):
        self.radius = radius
        self.cells = [(q, r) for q in range(-radius, radius + 1)
                      for r in range(-radius, radius + 1)
                      if abs(q + r) <= radius]
        self.index = {c: i for i, c in enumerate(self.cells)}
        self.neighbors = []
        for (q, r) in self.cells:
            nbrs = [self.index[(q + dq, r + dr)] for dq, dr in DIRECTIONS
                    if (q + dq, r + dr) in self.index]
            self.neighbors.append(nbrs)

        # Point-symmetric values: cell (q, r) and (-q, -r) get the same value.
        rng = random.Random(seed)
        self.values = [0] * len(self.cells)
        for i, (q, r) in enumerate(self.cells):
            j = self.index[(-q, -r)]
            if i <= j:
                v = rng.choice([1, 1, 2, 2, 3])
                self.values[i] = self.values[j] = v
        self.values[self.index[(0, 0)]] = 3          # the centre is the prize

        self.red_start = self.index[(-radius, radius)]
        self.blue_start = self.index[(radius, -radius)]
        self.values[self.red_start] = self.values[self.blue_start] = 1


class GameState:
    """Mutable game state with make/undo so the search does not copy boards."""

    def __init__(self, board):
        self.board = board
        self.owner = [EMPTY] * len(board.cells)
        self.owner[board.red_start] = RED
        self.owner[board.blue_start] = BLUE
        self.to_move = RED
        self.score = {RED: board.values[board.red_start],
                      BLUE: board.values[board.blue_start]}

    # ---------- move generation ----------
    def legal_moves(self, player=None):
        player = self.to_move if player is None else player
        owner, nbrs = self.owner, self.board.neighbors
        moves = []
        for i, o in enumerate(owner):
            if o == EMPTY:
                for n in nbrs[i]:
                    if owner[n] == player:
                        moves.append(i)
                        break
        return moves

    def captures_for(self, cell, player):
        """Enemy cells that would flip if `player` claimed `cell`:
        those touching `cell` that would then touch CAPTURE_COUNT or more of player's cells."""
        owner, nbrs = self.owner, self.board.neighbors
        enemy = other(player)
        flips = []
        for e in nbrs[cell]:
            if owner[e] != enemy:
                continue
            mine = 1  # the new cell itself
            for n in nbrs[e]:
                if owner[n] == player:
                    mine += 1
            if mine >= CAPTURE_COUNT:
                flips.append(e)
        return flips

    # ---------- make / undo ----------
    def play(self, cell):
        """Play a move (or None to pass). Returns undo info."""
        player = self.to_move
        flips = []
        if cell is not None:
            flips = self.captures_for(cell, player)
            vals = self.board.values
            self.owner[cell] = player
            self.score[player] += vals[cell]
            enemy = other(player)
            for e in flips:
                self.owner[e] = player
                self.score[player] += vals[e]
                self.score[enemy] -= vals[e]
        self.to_move = other(player)
        return (cell, flips, player)

    def undo(self, info):
        cell, flips, player = info
        if cell is not None:
            vals = self.board.values
            enemy = other(player)
            for e in flips:
                self.owner[e] = enemy
                self.score[player] -= vals[e]
                self.score[enemy] += vals[e]
            self.owner[cell] = EMPTY
            self.score[player] -= vals[cell]
        self.to_move = player

    # ---------- end of game ----------
    def is_over(self):
        return not self.legal_moves(RED) and not self.legal_moves(BLUE)

    def winner(self):
        if self.score[RED] > self.score[BLUE]:
            return RED
        if self.score[BLUE] > self.score[RED]:
            return BLUE
        return None  # draw
