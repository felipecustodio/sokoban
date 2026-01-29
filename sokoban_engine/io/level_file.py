"""Level file loading and saving.

Supports:
- Standard XSB format
- RLE (run-length encoded) format
- Alternative floor characters (-, _)
- Alternative entity characters (B for box, & for player, X for box-on-goal)
- Level collections (multiple levels in one file)
- Named level selection from collections
"""

import re
from dataclasses import dataclass
from pathlib import Path

from sokoban_engine.engine.game import Game
from sokoban_engine.io.rle import decode_rle, encode_rle, is_rle_format

# Pattern matching "Level: <title>" with optional "| <solution>" suffix
_TITLE_RE = re.compile(r"^Level:\s*(.+?)(?:\s*\|.*)?$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class LevelInfo:
    """A level loaded from a collection, with its metadata."""

    title: str
    index: int
    game: Game


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
    return [info.game for info in _parse_collection(content)]


def load_collection_with_info(file_path: str | Path) -> list[LevelInfo]:
    """Load a collection file, returning levels with titles and indices.

    Each level is wrapped in a LevelInfo with its title (parsed from
    "Level: <title>" lines) and 0-based index within the file. If a level
    has no title line, a fallback is generated from the filename and the
    level's position in the file (e.g. "Microban 3").

    Args:
        file_path: Path to the level collection file.

    Returns:
        List of LevelInfo objects.
    """
    path = Path(file_path)
    collection_name = path.stem
    content = path.read_text(encoding="utf-8")
    return _parse_collection(content, collection_name)


def load_level_by_index(file_path: str | Path, index: int) -> LevelInfo:
    """Load a single level from a collection file by its 0-based index.

    Args:
        file_path: Path to the level collection file.
        index: 0-based index of the level within the file.

    Returns:
        LevelInfo for the requested level.

    Raises:
        IndexError: If index is out of range.
    """
    path = Path(file_path)
    collection_name = path.stem
    content = path.read_text(encoding="utf-8")
    levels = _parse_collection(content, collection_name)
    if index < 0 or index >= len(levels):
        raise IndexError(
            f"Level index {index} out of range "
            f"(collection has {len(levels)} levels)"
        )
    return levels[index]


def load_level_by_title(file_path: str | Path, title: str) -> LevelInfo:
    """Load a single level from a collection file by its title.

    Title matching is case-insensitive.

    Args:
        file_path: Path to the level collection file.
        title: Title to search for (case-insensitive).

    Returns:
        LevelInfo for the first level matching the title.

    Raises:
        KeyError: If no level with the given title is found.
    """
    path = Path(file_path)
    collection_name = path.stem
    content = path.read_text(encoding="utf-8")
    levels = _parse_collection(content, collection_name)
    title_lower = title.lower()
    for info in levels:
        if info.title.lower() == title_lower:
            return info
    available = [info.title for info in levels]
    raise KeyError(
        f"No level titled {title!r} in collection. "
        f"Available: {available}"
    )


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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_collection(
    content: str,
    collection_name: str = "",
) -> list[LevelInfo]:
    """Parse a collection string into LevelInfo objects.

    Splits on non-level lines (titles, blank lines, comments), extracts
    "Level: <title>" headers, and parses each level block.
    """
    results: list[LevelInfo] = []
    current_level_lines: list[str] = []
    current_title: str | None = None
    level_index = 0

    for line in content.split("\n"):
        stripped = line.strip()

        if _is_level_line(stripped):
            current_level_lines.append(line)
        else:
            # Non-level line — flush any accumulated level
            if current_level_lines:
                _try_parse_level(
                    current_level_lines,
                    current_title,
                    level_index,
                    collection_name,
                    results,
                )
                level_index = len(results)
                current_level_lines = []
                current_title = None

            # Check if this line is a title
            title_match = _TITLE_RE.match(stripped)
            if title_match:
                current_title = title_match.group(1).strip()

    # Flush last level
    if current_level_lines:
        _try_parse_level(
            current_level_lines,
            current_title,
            level_index,
            collection_name,
            results,
        )

    return results


def _try_parse_level(
    lines: list[str],
    title: str | None,
    index: int,
    collection_name: str,
    results: list[LevelInfo],
) -> None:
    """Try to parse a level block and append to results."""
    level_str = "\n".join(lines)
    try:
        game = load_level(level_str)
    except Exception:
        return

    if title:
        resolved_title = title
    elif collection_name:
        resolved_title = f"{collection_name} {index + 1}"
    else:
        resolved_title = f"Level {index + 1}"

    game.title = resolved_title
    results.append(LevelInfo(title=resolved_title, index=index, game=game))


def _normalize_level_string(level_string: str) -> str:
    """Normalize a level string for parsing."""
    # Remove carriage returns
    normalized = level_string.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.strip("\n\r")


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

    # Level lines contain level characters (including alternatives B, &, X)
    level_chars = set("#@+$*. -_|B&X")

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
