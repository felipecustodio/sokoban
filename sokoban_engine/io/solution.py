"""Solution string parsing and generation.

Solutions are represented by the movements of the player:
- u/U = up (U = push)
- d/D = down (D = push)
- l/L = left (L = push)
- r/R = right (R = push)

Uppercase letters indicate that a box was pushed during that move.
"""

from sokoban_engine.core.direction import Direction
from sokoban_engine.history.move_record import MoveRecord

# Direction character mappings
_CHAR_TO_DIRECTION: dict[str, Direction] = {
    "u": Direction.UP,
    "U": Direction.UP,
    "d": Direction.DOWN,
    "D": Direction.DOWN,
    "l": Direction.LEFT,
    "L": Direction.LEFT,
    "r": Direction.RIGHT,
    "R": Direction.RIGHT,
}

_DIRECTION_TO_CHAR: dict[Direction, str] = {
    Direction.UP: "u",
    Direction.DOWN: "d",
    Direction.LEFT: "l",
    Direction.RIGHT: "r",
}

_DIRECTION_TO_PUSH_CHAR: dict[Direction, str] = {
    Direction.UP: "U",
    Direction.DOWN: "D",
    Direction.LEFT: "L",
    Direction.RIGHT: "R",
}


def parse_solution(solution_string: str) -> list[MoveRecord]:
    """Parse a solution string into a list of MoveRecords.

    Args:
        solution_string: Solution string using u/d/l/r notation.
                        Uppercase indicates a push.

    Returns:
        List of MoveRecord objects.

    Example:
        >>> records = parse_solution("DDrdrruLruLLDllU")
        >>> records[0]
        MoveRecord(DOWN, push)
    """
    records: list[MoveRecord] = []

    for char in solution_string:
        if char not in _CHAR_TO_DIRECTION:
            # Skip unknown characters (whitespace, etc.)
            continue

        direction = _CHAR_TO_DIRECTION[char]
        was_push = char.isupper()
        records.append(MoveRecord(direction, was_push))

    return records


def solution_to_string(
    records: list[MoveRecord],
    include_pushes: bool = True,
) -> str:
    """Convert a list of MoveRecords to a solution string.

    Args:
        records: List of MoveRecord objects.
        include_pushes: If True, use uppercase for pushes.
                       If False, all lowercase.

    Returns:
        Solution string.

    Example:
        >>> records = [MoveRecord(Direction.DOWN, True), MoveRecord(Direction.RIGHT, False)]
        >>> solution_to_string(records)
        'Dr'
    """
    chars: list[str] = []

    for record in records:
        if include_pushes and record.was_push:
            chars.append(_DIRECTION_TO_PUSH_CHAR[record.direction])
        else:
            chars.append(_DIRECTION_TO_CHAR[record.direction])

    return "".join(chars)


def solution_to_directions(solution_string: str) -> list[Direction]:
    """Parse a solution string into a list of Directions (ignoring push info).

    Args:
        solution_string: Solution string using u/d/l/r notation.

    Returns:
        List of Direction values.

    Example:
        >>> directions = solution_to_directions("DDrd")
        >>> directions
        [Direction.DOWN, Direction.DOWN, Direction.RIGHT, Direction.DOWN]
    """
    directions: list[Direction] = []

    for char in solution_string:
        if char.lower() in _CHAR_TO_DIRECTION:
            directions.append(_CHAR_TO_DIRECTION[char.lower()])

    return directions


def validate_solution_format(solution_string: str) -> bool:
    """Check if a solution string contains only valid characters.

    Args:
        solution_string: Solution string to validate.

    Returns:
        True if all characters are valid direction characters or whitespace.
    """
    valid_chars = set("uUdDlLrR \t\n")
    return all(char in valid_chars for char in solution_string)
