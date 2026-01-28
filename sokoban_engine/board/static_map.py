"""Immutable static map representation.

The StaticMap is created once per level and shared across all game states.
It contains walls, goals, floor tile indices, and precomputed neighbor relationships.
"""

from dataclasses import dataclass

from sokoban_engine.board.parser import ParsedLevel
from sokoban_engine.board.tile_index import build_tile_index
from sokoban_engine.core.direction import Direction
from sokoban_engine.core.types import Bitboard, CellType, Position, TileIndex


@dataclass(frozen=True, slots=True)
class StaticMap:
    """Immutable representation of the level's static elements.

    This is created once per level and never modified.
    It is shared across all game states for that level.
    """

    # Dimensions
    width: int
    height: int

    # Total number of passable (floor) tiles
    num_floor_tiles: int

    # Mapping: position_to_index[row][col] -> tile_index (-1 for walls)
    position_to_index: tuple[tuple[TileIndex, ...], ...]

    # Reverse mapping: index_to_position[tile_index] -> (row, col)
    index_to_position: tuple[Position, ...]

    # The original grid for cell type queries
    grid: tuple[tuple[CellType, ...], ...]

    # Bitboard masks
    floor_mask: Bitboard  # 1 for each floor tile
    goal_mask: Bitboard  # 1 for each goal tile

    # Precomputed neighbors: neighbors[tile_index] = (up, down, left, right)
    # Each value is the adjacent tile index, or -1 if wall
    neighbors: tuple[tuple[TileIndex, TileIndex, TileIndex, TileIndex], ...]

    # Goal positions for convenience
    goal_positions: tuple[Position, ...]

    @classmethod
    def from_parsed_level(cls, parsed: ParsedLevel) -> "StaticMap":
        """Create a StaticMap from a parsed level."""
        # Build tile indexing
        position_to_index, index_to_position, num_floor_tiles = build_tile_index(
            parsed.grid, parsed.width, parsed.height
        )

        # Build floor and goal masks
        floor_mask = _build_floor_mask(num_floor_tiles)
        goal_mask = _build_goal_mask(parsed.goal_positions, position_to_index)

        # Build neighbor lookup table
        neighbors = _build_neighbors(
            index_to_position,
            position_to_index,
            parsed.width,
            parsed.height,
            num_floor_tiles,
        )

        return cls(
            width=parsed.width,
            height=parsed.height,
            num_floor_tiles=num_floor_tiles,
            position_to_index=position_to_index,
            index_to_position=index_to_position,
            grid=parsed.grid,
            floor_mask=floor_mask,
            goal_mask=goal_mask,
            neighbors=neighbors,
            goal_positions=parsed.goal_positions,
        )

    def get_tile_index(self, row: int, col: int) -> TileIndex:
        """Get the tile index for a position. Returns -1 for walls."""
        if 0 <= row < self.height and 0 <= col < self.width:
            return self.position_to_index[row][col]
        return -1

    def get_position(self, tile_index: TileIndex) -> Position:
        """Get the position for a tile index."""
        return self.index_to_position[tile_index]

    def get_neighbor(self, tile_index: TileIndex, direction: Direction) -> TileIndex:
        """Get the neighboring tile index in a direction. Returns -1 if wall."""
        return self.neighbors[tile_index][direction]

    def is_wall(self, row: int, col: int) -> bool:
        """Check if a cell is a wall."""
        if 0 <= row < self.height and 0 <= col < self.width:
            return self.grid[row][col] == CellType.WALL
        return True  # Out of bounds is wall

    def is_goal(self, row: int, col: int) -> bool:
        """Check if a cell is a goal."""
        if 0 <= row < self.height and 0 <= col < self.width:
            return self.grid[row][col] == CellType.GOAL
        return False

    def is_goal_index(self, tile_index: TileIndex) -> bool:
        """Check if a tile index is a goal."""
        return bool(self.goal_mask & (1 << tile_index))


def _build_floor_mask(num_floor_tiles: int) -> Bitboard:
    """Build a bitboard with all floor tiles set."""
    # All bits from 0 to num_floor_tiles-1 are set
    return (1 << num_floor_tiles) - 1


def _build_goal_mask(
    goal_positions: tuple[Position, ...],
    position_to_index: tuple[tuple[TileIndex, ...], ...],
) -> Bitboard:
    """Build a bitboard with goal tiles set."""
    mask: Bitboard = 0
    for row, col in goal_positions:
        tile_index = position_to_index[row][col]
        mask |= 1 << tile_index
    return mask


def _build_neighbors(
    index_to_position: tuple[Position, ...],
    position_to_index: tuple[tuple[TileIndex, ...], ...],
    width: int,
    height: int,
    num_floor_tiles: int,
) -> tuple[tuple[TileIndex, TileIndex, TileIndex, TileIndex], ...]:
    """Build neighbor lookup table for all floor tiles."""
    neighbors: list[tuple[TileIndex, TileIndex, TileIndex, TileIndex]] = []

    for tile_idx in range(num_floor_tiles):
        row, col = index_to_position[tile_idx]

        # UP (row - 1)
        up = _get_neighbor_index(row - 1, col, position_to_index, width, height)
        # DOWN (row + 1)
        down = _get_neighbor_index(row + 1, col, position_to_index, width, height)
        # LEFT (col - 1)
        left = _get_neighbor_index(row, col - 1, position_to_index, width, height)
        # RIGHT (col + 1)
        right = _get_neighbor_index(row, col + 1, position_to_index, width, height)

        neighbors.append((up, down, left, right))

    return tuple(neighbors)


def _get_neighbor_index(
    row: int,
    col: int,
    position_to_index: tuple[tuple[TileIndex, ...], ...],
    width: int,
    height: int,
) -> TileIndex:
    """Get tile index at position, or -1 if out of bounds or wall."""
    if 0 <= row < height and 0 <= col < width:
        return position_to_index[row][col]
    return -1
