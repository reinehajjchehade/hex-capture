# Hex Capture Duel

A two-player territory game on a hex board, with an AI opponent that uses
minimax search with alpha-beta pruning (AI course, Optional Game Project, Group 16).

## How to run

Needs Python 3.8+ only (tkinter ships with Python on Windows and macOS; on Linux
install `python3-tk`). No other packages.

```
python hex_capture.py     # play the game (GUI)
python benchmark.py       # minimax vs alpha-beta node counts
```

## Rules

1. Red starts in the bottom-left corner, Blue in the top-right. Red moves first.
2. On your turn, claim one empty cell that touches a cell you own.
3. Every enemy cell touching your new cell flips to you if it now touches
   3 or more of your cells (the new cell counts).
4. If you have no legal move you pass. The game ends when nobody can move.
5. Each cell is worth 1-3 points (the dots). Highest total wins.

## Files

| File | Contents |
|---|---|
| `game.py` | Board, rules, make/undo of moves |
| `ai.py` | Evaluation function, move ordering, minimax, alpha-beta |
| `hex_capture.py` | tkinter GUI |
| `benchmark.py` | Compares node counts of minimax / alpha-beta / alpha-beta + ordering |

## Mac troubleshooting

- The window may open **behind the terminal**. Look in the Dock for the Python
  rocket icon and click it, or press Cmd+Tab. The game now tries to bring itself
  to the front automatically.
- Check that tkinter works: `python -m tkinter` should open a small test window.
- If the test window is blank or never appears (an old Tk in Anaconda), either run
  `conda install -c conda-forge tk` or use the python.org Python:
  `python3 hex_capture.py` with Python from https://www.python.org/downloads/macos/.
