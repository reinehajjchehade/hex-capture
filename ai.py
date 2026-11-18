"""
Hex Capture Duel - AI player.

Minimax with alpha-beta pruning, a depth limit, a heuristic evaluation function
and move ordering. Plain minimax (no pruning) is kept too, so the two can be
compared in benchmark.py.
"""

import math
import time

from game import CAPTURE_COUNT, EMPTY, other

# Evaluation weights (tuned by hand + self-play, see summary)
W_MATERIAL = 10   # each point of score difference
W_MOBILITY = 1    # each extra legal move we have
W_WEAK = 4        # each point of value sitting in a cell that can be flipped next turn
WIN_SCORE = 10_000


def evaluate(state, me):
    """Heuristic value of `state` from the point of view of player `me`."""
    opp = other(me)
    owner, nbrs, vals = state.owner, state.board.neighbors, state.board.values

    if state.is_over():
        diff = state.score[me] - state.score[opp]
        if diff > 0:
            return WIN_SCORE + diff
        if diff < 0:
            return -WIN_SCORE + diff
        return 0

    material = state.score[me] - state.score[opp]
    mobility = len(state.legal_moves(me)) - len(state.legal_moves(opp))

    # Weak cells: a cell is in danger when it already touches CAPTURE_COUNT-1
    # enemy cells and has an empty neighbour - one enemy move there flips it.
    weak = 0
    for i, o in enumerate(owner):
        if o == EMPTY:
            continue
        foe = other(o)
        enemy = empty = 0
        for n in nbrs[i]:
            if owner[n] == foe:
                enemy += 1
            elif owner[n] == EMPTY:
                empty += 1
        if empty and enemy >= CAPTURE_COUNT - 1:
            weak += vals[i] if o == me else -vals[i]

    return W_MATERIAL * material + W_MOBILITY * mobility - W_WEAK * weak


def ordered_moves(state):
    """Most promising moves first: biggest immediate gain (cell value + captured values)."""
    moves = state.legal_moves()
    vals = state.board.values
    player = state.to_move

    def gain(cell):
        return vals[cell] + 2 * sum(vals[e] for e in state.captures_for(cell, player))

    moves.sort(key=gain, reverse=True)
    return moves


class SearchStats:
    def __init__(self):
        self.nodes = 0
        self.cutoffs = 0
        self.time = 0.0


def alphabeta(state, depth, alpha, beta, maximizing, me, stats, use_ordering=True):
    stats.nodes += 1
    if depth == 0 or state.is_over():
        return evaluate(state, me)

    moves = ordered_moves(state) if use_ordering else state.legal_moves()
    if not moves:
        moves = [None]  # forced pass

    if maximizing:
        value = -math.inf
        for m in moves:
            info = state.play(m)
            value = max(value, alphabeta(state, depth - 1, alpha, beta, False, me, stats, use_ordering))
            state.undo(info)
            alpha = max(alpha, value)
            if alpha >= beta:
                stats.cutoffs += 1
                break           # beta cut-off: MIN will never allow this branch
        return value
    else:
        value = math.inf
        for m in moves:
            info = state.play(m)
            value = min(value, alphabeta(state, depth - 1, alpha, beta, True, me, stats, use_ordering))
            state.undo(info)
            beta = min(beta, value)
            if alpha >= beta:
                stats.cutoffs += 1
                break           # alpha cut-off: MAX will never allow this branch
        return value


def minimax(state, depth, maximizing, me, stats):
    """Plain minimax, no pruning (for comparison only)."""
    stats.nodes += 1
    if depth == 0 or state.is_over():
        return evaluate(state, me)
    moves = state.legal_moves() or [None]
    best = -math.inf if maximizing else math.inf
    for m in moves:
        info = state.play(m)
        v = minimax(state, depth - 1, not maximizing, me, stats)
        state.undo(info)
        best = max(best, v) if maximizing else min(best, v)
    return best


def best_move(state, depth, use_pruning=True, use_ordering=True):
    """Return (move, value, stats) for the player to move. move is None for a pass."""
    me = state.to_move
    stats = SearchStats()
    start = time.perf_counter()

    moves = ordered_moves(state) if use_ordering else state.legal_moves()
    if not moves:
        stats.time = time.perf_counter() - start
        return None, evaluate(state, me), stats

    best, best_val = moves[0], -math.inf
    alpha, beta = -math.inf, math.inf
    for m in moves:
        info = state.play(m)
        if use_pruning:
            v = alphabeta(state, depth - 1, alpha, beta, False, me, stats, use_ordering)
        else:
            v = minimax(state, depth - 1, False, me, stats)
        state.undo(info)
        if v > best_val:
            best, best_val = m, v
        alpha = max(alpha, best_val)
    stats.nodes += 1
    stats.time = time.perf_counter() - start
    return best, best_val, stats
