"""Run-length encoding (RLE) support for Sokoban levels.

RLE format is more compact and efficient, especially for mobile devices.
In this format, digits show how many elements of the same type follow.

Example:
    ####  becomes  4#
    $$    becomes  2$

Rows are separated by "|" characters.
Empty squares can be represented by "-" (preferred) or "_".
"""

import re


def decode_rle(rle_string: str) -> str:
    """Decode a run-length encoded level string.

    Args:
        rle_string: RLE-encoded level string (rows separated by "|").

    Returns:
        Standard XSB format level string (rows separated by newlines).

    Example:
        >>> decode_rle("4#|#.@-#|#$*-#|4#")
        '####\\n#.@ #\\n#$* #\\n####'
    """
    # Handle both single-line RLE and multi-line RLE
    # Normalize line endings and join if multi-line
    lines = rle_string.strip().split("\n")
    rle_string = "|".join(line.rstrip("|") for line in lines)

    # Split by row separator
    rows = rle_string.split("|")

    decoded_rows: list[str] = []
    for row in rows:
        decoded_rows.append(_decode_rle_row(row))

    return "\n".join(decoded_rows)


def _decode_rle_row(row: str) -> str:
    """Decode a single RLE-encoded row."""
    result: list[str] = []
    i = 0

    while i < len(row):
        # Check for run-length prefix (digits)
        count = 0
        while i < len(row) and row[i].isdigit():
            count = count * 10 + int(row[i])
            i += 1

        if i >= len(row):
            break

        char = row[i]
        i += 1

        # Convert "-" and "_" to space (floor)
        if char in "-_":
            char = " "

        # If no count specified, default to 1
        if count == 0:
            count = 1

        result.append(char * count)

    return "".join(result)


def encode_rle(level_string: str, use_hyphen: bool = True) -> str:
    """Encode a level string using run-length encoding.

    Args:
        level_string: Standard XSB format level string.
        use_hyphen: If True, use "-" for empty squares (recommended).
                   If False, use "_".

    Returns:
        RLE-encoded level string (single line, rows separated by "|").

    Example:
        >>> encode_rle("####\\n#.@ #\\n####")
        '4#|#.@-#|4#'
    """
    floor_char = "-" if use_hyphen else "_"

    lines = level_string.strip().split("\n")
    encoded_rows: list[str] = []

    for line in lines:
        encoded_rows.append(_encode_rle_row(line, floor_char))

    return "|".join(encoded_rows)


def _encode_rle_row(row: str, floor_char: str) -> str:
    """Encode a single row using RLE."""
    if not row:
        return ""

    # Strip trailing spaces (not needed in RLE)
    row = row.rstrip()

    result: list[str] = []
    i = 0

    while i < len(row):
        char = row[i]
        count = 1

        # Count consecutive identical characters
        while i + count < len(row) and row[i + count] == char:
            count += 1

        # Convert space to floor character
        if char == " ":
            char = floor_char

        # Only use count prefix if > 1 (or optionally if >= 2)
        if count > 1:
            result.append(f"{count}{char}")
        else:
            result.append(char)

        i += count

    return "".join(result)


def is_rle_format(level_string: str) -> bool:
    """Check if a level string appears to be RLE encoded.

    Heuristics:
    - Contains "|" as row separator
    - Contains digits followed by level characters
    - Does not contain newlines (or contains "|" with newlines)

    Args:
        level_string: Level string to check.

    Returns:
        True if likely RLE format, False otherwise.
    """
    stripped = level_string.strip()

    # If contains "|", likely RLE
    if "|" in stripped:
        return True

    # If contains digit followed by level character, likely RLE
    if re.search(r"\d+[#@+$*.\-_ ]", stripped):
        return True

    # If single line with no spaces between level chars, likely RLE
    lines = stripped.split("\n")
    if len(lines) == 1 and "#" in stripped:
        # Check for typical RLE pattern
        return bool(re.search(r"\d+#", stripped))

    return False
