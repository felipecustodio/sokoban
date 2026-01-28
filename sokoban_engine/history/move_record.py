"""Compact move record encoding.

Each move is stored as just a direction and whether it was a push.
This is extremely memory-efficient: only 3 bits per move.
"""

from dataclasses import dataclass

from sokoban_engine.core.direction import Direction


@dataclass(frozen=True, slots=True)
class MoveRecord:
    """Record of a single move.

    Uses only 3 bits of information:
    - 2 bits for direction (0-3)
    - 1 bit for was_push flag

    This compact representation allows storing very long move histories
    with minimal memory usage.
    """

    direction: Direction
    was_push: bool

    def encode(self) -> int:
        """Encode to a single byte.

        Bit layout: [direction (2 bits)][was_push (1 bit)]
        """
        return (self.direction.value << 1) | int(self.was_push)

    @classmethod
    def decode(cls, value: int) -> "MoveRecord":
        """Decode from a single byte."""
        return cls(
            direction=Direction(value >> 1),
            was_push=bool(value & 1),
        )

    def __repr__(self) -> str:
        push_str = "push" if self.was_push else "walk"
        return f"MoveRecord({self.direction.name}, {push_str})"
