# 📦 Sokoban Engine

[![CI](https://github.com/felipecustodio/sokoban/actions/workflows/ci.yml/badge.svg)](https://github.com/felipecustodio/sokoban/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![ty](https://img.shields.io/badge/ty-checked-5B2B82.svg)](https://github.com/astral-sh/ty)

High-performance 2D game engine for Sokoban puzzles, built with Python.

## 🎮 Features

- ⚡ **Bitboard-based state** - O(1) collision detection using bit manipulation
- 🧩 **Level parsing** - Support for XSB format and run-length encoding (RLE)
- ↩️ **Undo/Redo** - Full history management with efficient move tracking
- 🔍 **Solver API** - Push-centric API with reachability analysis
- ✅ **Type safe** - Fully typed with Python 3.13+ using Self types
- 🧪 **Well tested** - Comprehensive test suite with 100+ tests

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/felipecustodio/sokoban.git
cd sokoban

# Install with uv
uv sync
```

## 💻 Usage

```python
from sokoban_engine import Game
from sokoban_engine.core.direction import Direction

# Load a level
level = '''
#####
#@$.#
#####
'''

game = Game(level)

# Make moves
result = game.move(Direction.RIGHT)
print(f"Move result: {result}")  # SUCCESS_PUSH or WIN

# Check state
print(f"Solved: {game.is_solved}")
print(f"Pushes: {game.push_count}")
```

## 🏗️ Architecture

```
sokoban_engine/
├── board/          # Static map and level parsing
├── core/           # Types and directions
├── engine/         # Main Game facade
├── history/        # Move records and undo stack
├── io/             # File I/O (RLE, solutions)
├── logic/          # Move application and reachability
└── state/          # Game state with bitboards
```

## 🧪 Development

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run --with ty ty check sokoban_engine/

# Run all CI checks locally
uv run ruff check . && uv run --with ty ty check sokoban_engine/ && uv run pytest
```

## 📄 License

MIT License - see LICENSE file for details.
