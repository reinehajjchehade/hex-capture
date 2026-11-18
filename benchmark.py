"""
Compare plain minimax, alpha-beta, and alpha-beta + move ordering.
All three must pick moves of equal value; only the number of nodes visited changes.

    python benchmark.py
"""

import random

from ai import best_move
from game import Board, GameState


def midgame_position(radius=4, plies=16, seed=3):
    state = GameState(Board(radius))
    rng = random.Random(seed)
    for _ in range(plies):
        state.play(rng.choice(state.legal_moves() or [None]))
    return state


def main():
    state = midgame_position()
    print(f"Mid-game position, {len(state.legal_moves())} legal moves for the side to move\n")
    print(f"{'depth':>5} | {'minimax nodes':>13} | {'alpha-beta':>10} | {'a-b + ordering':>14} | "
          f"{'saved':>6} | {'same value?':>11}")
    print("-" * 76)
    for depth in range(1, 6):
        _, v1, s1 = best_move(state, depth, use_pruning=False, use_ordering=False)
        _, v2, s2 = best_move(state, depth, use_pruning=True, use_ordering=False)
        _, v3, s3 = best_move(state, depth, use_pruning=True, use_ordering=True)
        saved = 100 * (1 - s3.nodes / s1.nodes)
        print(f"{depth:>5} | {s1.nodes:>13,} | {s2.nodes:>10,} | {s3.nodes:>14,} | "
              f"{saved:>5.1f}% | {str(v1 == v2 == v3):>11}")


if __name__ == "__main__":
    main()
