"""Board representation and parsing for the Sokoban engine."""

from sokoban_engine.board.parser import ParsedLevel, parse_level
from sokoban_engine.board.static_map import StaticMap

__all__ = [
    "ParsedLevel",
    "StaticMap",
    "parse_level",
]
