# Xiangqi (Chinese Chess) AI — Pikafish + Web GUI

A fully offline, local Xiangqi program: the **Pikafish** engine (NNUE) + a self-contained **web interface** + a **51,101-node professional opening book**.

![Cyber neon theme](docs/screenshot-cyber.png)
![Classic wood theme](docs/screenshot-wood.png)

## Features

- **Strong engine**: Pikafish 2026-09-06, 8 threads / 512MB hash, five difficulty levels (default: 2s/move, thinking time scales up as the game deepens)
- **Professional opening book**: a 51,101-node tree translated from Eleeye's `BOOK.DAT`, weighted by real professional game statistics — zero-latency master-level openings
- **Clickable candidate moves**: every AI move shows its top-3 candidates (Chinese notation + score + follow-up lines); **click any candidate to make the AI play that move instead**
- **Plain-language evaluation card**: verdicts like "slight advantage" / "winning" instead of raw centipawns, plus an evaluation bar and Chinese-notation principal variation
- **Full rule enforcement**: perpetual check / perpetual chase violations, threefold repetition, 60-move draw rule
- **Polished UI**: 4 switchable themes (cyber neon / classic wood / celadon / ink), sliding move animation, capture shatter effects, full-screen check/checkmate banners, move-path arrows, captured-pieces display, move sounds
- **Opening-repertoire mode**: the AI sticks to a chosen repertoire (Central Cannon, Elephant Opening, etc.) while adapting to your replies

## Quick Start (Windows)

```bat
开始下棋.bat
```

or manually:

```bat
cd gui-web
python server.py
```

Then open <http://127.0.0.1:8731> in your browser. Requires Python 3.8+, no third-party packages needed.

Or grab the ready-to-run zip from [Releases](../../releases) — unzip and double-click `开始下棋.bat`.

## Opening Book Format (reusable)

`gui-web/book_tree.json` is converted from Eleeye's `BOOK.DAT` (see `build_book.py`) and can be reused by any Xiangqi program:

```json
{
  "":            {"c3c4": 546, "b2e2": 1473, "c0e2": 311, ...},
  "c3c4":        {"h9g7": 50, "b7c7": 149, "g6g5": 57, ...},
  "c3c4 h9g7":   {"g3g4": 34, "b0c2": 38, ...}
}
```

- **Key**: the move sequence from the initial position, in UCI-style coordinate notation (e.g. `h2e2`), space-separated; the empty string `""` is the start position
- **Value**: `{next_move: weight}` where the weight comes from Eleeye's professional game statistics — pick weighted-randomly or by rank
- **Lookup**: use the current move sequence as the key; on a miss, fall back to the engine

Coordinate system: `a0` is the bottom-left corner from Red's perspective; files `a`–`i`, ranks `0`–`9` — same convention as Pikafish.

## Repository Layout

```
engine/          Pikafish binaries (Windows/Linux/macOS/Android) + NNUE weights + licenses
gui-web/         Web UI and server
  index.html     Single-file frontend (SVG board, rule engine, animations, themes)
  server.py      HTTP server + UCI engine bridge (book, MultiPV candidates, perpetual-check avoidance)
  book_tree.json Opening book (51,101 nodes, generated from BOOK.DAT)
  build_book.py  BOOK.DAT → book_tree.json converter
docs/            Screenshots
开始下棋.bat      One-click launcher
usage.md         Usage guide (Chinese)
```

## Licenses

- Pikafish engine & NNUE weights: GPL-3.0 (see `engine/Copying.txt`, `engine/NNUE-License.md`)
- Opening book source data (BOOK.DAT from Eleeye): GPL
- Original code in this repo (gui-web, scripts, docs): MIT
