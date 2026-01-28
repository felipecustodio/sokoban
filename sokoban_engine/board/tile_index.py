"""Floor tile indexing system.

Assigns sequential indices (0, 1, 2, ...) only to passable floor tiles.
Walls get index -1.
"""

from sokoban_engine.core.types import CellType, Position, TileIndex


def build_tile_index(
    grid: tuple[tuple[CellType, ...], ...],
    width: int,
    height: int,
) -> tuple[
    tuple[tuple[TileIndex, ...], ...],  # position_to_index[row][col]
    tuple[Position, ...],  # index_to_position
    int,  # num_floor_tiles
]:
    """Build bidirectional mappings between positions and tile indices.

    Only floor tiles (FLOOR and GOAL) get indices.
    Walls get index -1.

    Args:
        grid: 2D grid of CellType values.
        width: Grid width.
        height: Grid height.

    Returns:
        (position_to_index, index_to_position, num_floor_tiles)
    """
    position_to_index: list[list[TileIndex]] = []
    index_to_position: list[Position] = []
    current_index = 0

    for row in range(height):
        row_indices: list[TileIndex] = []
        for col in range(width):
            cell = grid[row][col]
            if cell == CellType.WALL:
                row_indices.append(-1)
            else:
                # Floor or Goal - assign an index
                row_indices.append(current_index)
                index_to_position.append((row, col))
                current_index += 1
        position_to_index.append(row_indices)

    return (
        tuple(tuple(row) for row in position_to_index),
        tuple(index_to_position),
        current_index,
    )
