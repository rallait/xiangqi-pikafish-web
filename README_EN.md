<div align="center">

# Xiangqi (Chinese Chess) AI — Pikafish + Web GUI

**A fully offline, local Xiangqi program**<br>
Top-tier engine · 51,101-node professional opening book · clickable candidate moves · cyber aesthetics

[![Release](https://img.shields.io/github/v/release/rallait/xiangqi-pikafish-web?style=flat-square&color=00e5ff)](../../releases)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078d4?style=flat-square&logo=windows&logoColor=white)](../../releases)
[![License](https://img.shields.io/badge/License-MIT%20%2B%20GPL--3.0-green?style=flat-square)](#licenses)
[![Stars](https://img.shields.io/github/stars/rallait/xiangqi-pikafish-web?style=flat-square&color=ffd24d)](../../stargazers)

**[中文 README](README.md)** · [Ready-to-run zip](../../releases) · [Usage guide](usage.md)

</div>

![Cyber neon theme](docs/screenshot-cyber.png)

<details>
<summary>More theme screenshots (8 total)</summary>

| Sakura | Porcelain |
|---|---|
| ![Sakura](docs/screenshot-sakura.png) | ![Porcelain](docs/screenshot-porcelain.png) |
| **Nocturne** | **Black Gold** |
| ![Nocturne](docs/screenshot-nocturne.png) | ![Black Gold](docs/screenshot-gold.png) |
| **Classic Wood** | **Jade** |
| ![Classic Wood](docs/screenshot-wood.png) | ![Jade](docs/screenshot-jade.png) |
| **Ink Wash** | |
| ![Ink Wash](docs/screenshot-ink.png) | |

</details>

## Features

- **Strong engine**: Pikafish 2026-09-06, 8 threads / 512MB hash, five difficulty levels (default: 2s/move, thinking time scales up as the game deepens)
- **Professional opening book**: a 51,101-node tree translated from Eleeye's `BOOK.DAT`, weighted by real professional game statistics — zero-latency master-level openings
- **Clickable candidate moves**: every AI move shows its top-3 candidates (Chinese notation + score + follow-up lines); **click any candidate to make the AI play that move instead**
- **Plain-language evaluation card**: verdicts like "slight advantage" / "winning" instead of raw centipawns, plus an evaluation bar and Chinese-notation principal variation
- **Full rule enforcement**: perpetual check / perpetual chase violations, threefold repetition, 60-move draw rule
- **Polished UI**: 8 switchable themes (cyber neon / classic wood / jade / ink wash / porcelain / nocturne / black gold / sakura, `?theme=xxx` URL param supported), sliding move animation, capture shatter effects, full-screen check/checkmate banners, move-path arrows, captured-pieces display, move sounds
- **Opening-repertoire mode**: the AI sticks to a chosen repertoire (Central Cannon, Elephant Opening, etc.) while adapting to your replies

## Quick Start (Windows)

**Prerequisite**: install [Python 3.8+](https://www.python.org/downloads/) (make sure to check **Add python.exe to PATH**). No third-party packages needed.

**Option 1 (recommended)**: download the zip from [Releases](../../releases), extract anywhere, double-click `开始下棋.bat`.

**Option 2 (clone the source)**:

```bat
git clone https://github.com/rallait/xiangqi-pikafish-web.git
cd xiangqi-pikafish-web
开始下棋.bat
```

Your browser should open <http://127.0.0.1:8731> automatically (open it manually if not). Close the console window to quit.

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
