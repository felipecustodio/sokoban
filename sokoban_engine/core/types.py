"""Type definitions for the Sokoban engine."""

from enum import IntEnum, auto

# Tile index: small integer representing a passable floor tile
# -1 indicates a wall or invalid position
type TileIndex = int

# Position as (row, col) tuple
type Position = tuple[int, int]

# Bitboard: integer where each bit represents a tile
# Bit is 1 if occupied (by box), 0 otherwise
type Bitboard = int


class CellType(IntEnum):
    """Static cell types in the map."""

    WALL = 0
    FLOOR = 1
    GOAL = 2  # Floor with goal marker


class MoveResult(IntEnum):
    """Result of attempting a move."""

    SUCCESS_WALK = auto()  # Player walked to empty cell
    SUCCESS_PUSH = auto()  # Player pushed a box
    BLOCKED_WALL = auto()  # Wall in the way
    BLOCKED_BOX = auto()  # Box blocked (another box or wall behind)
    WIN = auto()  # Move resulted in win condition
