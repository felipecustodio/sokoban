"""Level file loading and saving.

Supports:
- Standard XSB format
- RLE (run-length encoded) format
- Alternative floor characters (-, _)
- Level collections (multiple levels in one file)
"""

from pathlib import Path

from sokoban_engine.engine.game import Game
from sokoban_engine.io.rle import decode_rle, encode_rle, is_rle_format


def load_level(level_string: str) -> Game:
    """Load a level from a string, auto-detecting format.

    Supports both standard XSB format and RLE format.

    Args:
        level_string: Level string in XSB or RLE format.

    Returns:
        Game instance initialized with the level.

    Example:
        >>> game = load_level("4#|#@$.#|4#")  # RLE format
        >>> game = load_level("#####\\n#@$.#\\n#####")  # XSB format
    """
    # Normalize the level string
    normalized = _normalize_level_string(level_string)

    # Check if RLE format and decode if necessary
    if is_rle_format(normalized):
        normalized = decode_rle(normalized)

    # Convert alternative floor characters to spaces
    normalized = _convert_floor_characters(normalized)

    return Game(normalized)


def load_level_file(file_path: str | Path) -> Game:
    """Load a level from a file.

    Args:
        file_path: Path to the level file.

    Returns:
        Game instance initialized with the level.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ParseError: If level format is invalid.
    """
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    return load_level(content)


def load_level_collection(file_path: str | Path) -> list[Game]:
    """Load multiple levels from a collection file.

    Levels in a collection are typically separated by blank lines
    or lines starting with a title/comment.

    Args:
        file_path: Path to the level collection file.

    Returns:
        List of Game instances.
    """
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    return load_levels_from_string(content)


def load_levels_from_string(content: str) -> list[Game]:
    """Load multiple levels from a string containing a level collection.

    Args:
        content: String containing multiple levels.

    Returns:
        List of Game instances.
    """
    levels: list[Game] = []
    current_level_lines: list[str] = []

    for line in content.split("\n"):
        stripped = line.strip()

        # Check if this is a level line (contains level characters)
        if _is_level_line(stripped):
            current_level_lines.append(line)
        elif current_level_lines:
            # End of current level, try to parse it
            level_str = "\n".join(current_level_lines)
            try:
                game = load_level(level_str)
                levels.append(game)
            except Exception:
                # Skip invalid levels
                pass
            current_level_lines = []

    # Don't forget the last level
    if current_level_lines:
        level_str = "\n".join(current_level_lines)
        try:
            game = load_level(level_str)
            levels.append(game)
        except Exception:
            pass

    return levels


def save_level(game: Game, use_rle: bool = False) -> str:
    """Save a game's current state to a level string.

    Args:
        game: Game instance to save.
        use_rle: If True, output RLE format. If False, standard XSB format.

    Returns:
        Level string representation.
    """
    level_string = _game_to_level_string(game)

    if use_rle:
        return encode_rle(level_string)

    return level_string


def save_level_file(
    game: Game,
    file_path: str | Path,
    use_rle: bool = False,
) -> None:
    """Save a game's current state to a file.

    Args:
        game: Game instance to save.
        file_path: Path to save the level to.
        use_rle: If True, output RLE format.
    """
    path = Path(file_path)
    content = save_level(game, use_rle=use_rle)
    path.write_text(content, encoding="utf-8")


def _normalize_level_string(level_string: str) -> str:
    """Normalize a level string for parsing."""
    # Remove carriage returns
    normalized = level_string.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.strip()


def _convert_floor_characters(level_string: str) -> str:
    """Convert alternative floor characters to spaces."""
    # Replace "-" and "_" with space when they appear as floor
    # Only replace when they're between level characters
    result = level_string.replace("-", " ").replace("_", " ")
    return result


def _is_level_line(line: str) -> bool:
    """Check if a line appears to be part of a level definition."""
    if not line:
        return False

    # Level lines contain level characters
    level_chars = set("#@+$*. -_|")

    # Must contain at least one wall character to be a level line
    if "#" not in line and "|" not in line:
        return False

    # Check if most characters are level characters
    level_char_count = sum(1 for c in line if c in level_chars or c.isdigit())
    return level_char_count > len(line) * 0.5


def _game_to_level_string(game: Game) -> str:
    """Convert a game's current state to a level string.

    This creates a level representation of the current game state,
    not the initial state.
    """
    rows: list[str] = []

    for row in range(game.height):
        row_chars: list[str] = []
        for col in range(game.width):
            char = _get_cell_char(game, row, col)
            row_chars.append(char)
        rows.append("".join(row_chars))

    return "\n".join(rows)


def _get_cell_char(game: Game, row: int, col: int) -> str:
    """Get the XSB character for a cell."""
    is_wall = game.is_wall(row, col)
    is_goal = game.is_goal(row, col)
    is_box = game.is_box(row, col)
    is_player = game.is_player(row, col)

    if is_wall:
        return "#"
    if is_player and is_goal:
        return "+"
    if is_player:
        return "@"
    if is_box and is_goal:
        return "*"
    if is_box:
        return "$"
    if is_goal:
        return "."
    return " "
