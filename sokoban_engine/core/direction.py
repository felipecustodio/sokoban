"""Direction enum and utilities."""

from enum import IntEnum

from sokoban_engine.core.types import Position


class Direction(IntEnum):
    """Movement directions."""

    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


# Direction deltas: (row_delta, col_delta)
DIRECTION_DELTAS: dict[Direction, Position] = {
    Direction.UP: (-1, 0),
    Direction.DOWN: (1, 0),
    Direction.LEFT: (0, -1),
    Direction.RIGHT: (0, 1),
}


def opposite_direction(direction: Direction) -> Direction:
    """Get the opposite direction."""
    match direction:
        case Direction.UP:
            return Direction.DOWN
        case Direction.DOWN:
            return Direction.UP
        case Direction.LEFT:
            return Direction.RIGHT
        case Direction.RIGHT:
            return Direction.LEFT


def apply_direction(position: Position, direction: Direction) -> Position:
    """Apply a direction delta to a position."""
    delta = DIRECTION_DELTAS[direction]
    return (position[0] + delta[0], position[1] + delta[1])
