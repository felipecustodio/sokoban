"""XSB format level parser.

Standard Sokoban level format (XSB):
    # = wall
    @ = player
    + = player on goal
    $ = box
    * = box on goal
    . = goal
    (space) = floor
    - = floor (alternative)
    _ = floor (alternative)
"""

from dataclasses import dataclass

from sokoban_engine.core.types import CellType, Position


@dataclass(frozen=True, slots=True)
class ParsedLevel:
    """Result of parsing a level string."""

    width: int
    height: int
    grid: tuple[tuple[CellType, ...], ...]  # [row][col]
    player_position: Position
    box_positions: tuple[Position, ...]
    goal_positions: tuple[Position, ...]


class ParseError(Exception):
    """Error during level parsing."""


def parse_level(level_string: str) -> ParsedLevel:
    """Parse a level string in XSB format.

    Args:
        level_string: Multi-line string in standard Sokoban format.

    Returns:
        ParsedLevel with grid, player, boxes, and goals.

    Raises:
        ParseError: If level is invalid.
    """
    lines = level_string.strip().split("\n")

    if not lines:
        raise ParseError("Empty level")

    # Determine dimensions
    height = len(lines)
    width = max(len(line) for line in lines)

    # Pad lines to uniform width
    lines = [line.ljust(width) for line in lines]

    # Parse grid
    grid: list[list[CellType]] = []
    player_pos: Position | None = None
    boxes: list[Position] = []
    goals: list[Position] = []

    for row, line in enumerate(lines):
        grid_row: list[CellType] = []
        for col, char in enumerate(line):
            cell_type, has_player, has_box, has_goal = _parse_char(char)

            grid_row.append(cell_type)

            if has_player:
                if player_pos is not None:
                    raise ParseError(f"Multiple players at ({row}, {col})")
                player_pos = (row, col)

            if has_box:
                boxes.append((row, col))

            if has_goal:
                goals.append((row, col))

        grid.append(grid_row)

    if player_pos is None:
        raise ParseError("No player found in level")

    if len(boxes) != len(goals):
        raise ParseError(f"Box count ({len(boxes)}) != goal count ({len(goals)})")

    if len(boxes) == 0:
        raise ParseError("No boxes found in level")

    # Convert to immutable tuples
    immutable_grid = tuple(tuple(row) for row in grid)

    return ParsedLevel(
        width=width,
        height=height,
        grid=immutable_grid,
        player_position=player_pos,
        box_positions=tuple(boxes),
        goal_positions=tuple(goals),
    )


def _parse_char(char: str) -> tuple[CellType, bool, bool, bool]:
    """Parse a single character.

    Returns:
        (cell_type, has_player, has_box, has_goal)
    """
    match char:
        case "#":
            return CellType.WALL, False, False, False
        case " " | "-" | "_":
            return CellType.FLOOR, False, False, False
        case ".":
            return CellType.GOAL, False, False, True
        case "@":
            return CellType.FLOOR, True, False, False
        case "+":
            return CellType.GOAL, True, False, True
        case "$":
            return CellType.FLOOR, False, True, False
        case "*":
            return CellType.GOAL, False, True, True
        case _:
            # Treat unknown as floor (for robustness)
            return CellType.FLOOR, False, False, False
