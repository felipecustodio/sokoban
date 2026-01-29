"""Sokoban Engine - A high-performance 2D Sokoban game engine.

This package provides a pure-logic Sokoban engine with no rendering.
It is designed to be used as a foundation for building Sokoban games,
solvers, or other applications.

Example:
    >>> from sokoban_engine import Game, Direction, MoveResult
    >>>
    >>> level = '''
    ... #####
    ... #@$.#
    ... #####
    ... '''
    >>> game = Game(level)
    >>> result = game.move(Direction.RIGHT)
    >>> print(f"Move result: {result}")
    >>> print(f"Solved: {game.is_solved}")

Features:
    - Compact state representation using tile indices and bitboards
    - O(1) collision detection using bitwise operations
    - Efficient undo/redo with minimal memory usage
    - Push-centric API for solver development
    - Bitwise flood-fill for player reachability
"""

from sokoban_engine.board.parser import ParseError
from sokoban_engine.core.direction import Direction
from sokoban_engine.core.types import (
    Bitboard,
    CellType,
    MoveResult,
    Position,
    TileIndex,
)
from sokoban_engine.engine.game import Game
from sokoban_engine.history.move_record import MoveRecord
from sokoban_engine.io.level_file import (
    LevelInfo,
    load_collection_with_info,
    load_level,
    load_level_by_index,
    load_level_by_title,
    load_level_collection,
    load_level_file,
    load_levels_from_string,
    save_level,
    save_level_file,
)
from sokoban_engine.io.rle import decode_rle, encode_rle
from sokoban_engine.io.solution import (
    parse_solution,
    solution_to_directions,
    solution_to_string,
)
from sokoban_engine.state.transposition import TranspositionTable
from sokoban_engine.state.zobrist import ZobristHasher

__version__ = "0.1.0"

__all__ = [
    "Bitboard",
    "CellType",
    "Direction",
    "Game",
    "MoveRecord",
    "MoveResult",
    "ParseError",
    "Position",
    "TileIndex",
    "TranspositionTable",
    "ZobristHasher",
    "LevelInfo",
    # I/O functions
    "decode_rle",
    "encode_rle",
    "load_collection_with_info",
    "load_level",
    "load_level_by_index",
    "load_level_by_title",
    "load_level_collection",
    "load_level_file",
    "load_levels_from_string",
    "parse_solution",
    "save_level",
    "save_level_file",
    "solution_to_directions",
    "solution_to_string",
]
