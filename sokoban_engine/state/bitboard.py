"""Bitboard operations for fast collision detection.

A bitboard is an integer where each bit position corresponds to a tile index.
Bit is 1 if a box occupies that tile, 0 otherwise.

This enables O(1) collision checks and efficient set operations.
"""

from sokoban_engine.core.types import Bitboard, TileIndex


class BitboardOps:
    """Static methods for bitboard manipulation.

    All operations return new bitboards (immutable style).
    """

    @staticmethod
    def has_box(bitboard: Bitboard, tile_index: TileIndex) -> bool:
        """Check if tile contains a box. O(1)."""
        return bool(bitboard & (1 << tile_index))

    @staticmethod
    def set_box(bitboard: Bitboard, tile_index: TileIndex) -> Bitboard:
        """Add box at tile. Returns new bitboard."""
        return bitboard | (1 << tile_index)

    @staticmethod
    def clear_box(bitboard: Bitboard, tile_index: TileIndex) -> Bitboard:
        """Remove box from tile. Returns new bitboard."""
        return bitboard & ~(1 << tile_index)

    @staticmethod
    def move_box(
        bitboard: Bitboard,
        from_index: TileIndex,
        to_index: TileIndex,
    ) -> Bitboard:
        """Move box from one tile to another. Returns new bitboard."""
        # Clear source, set destination
        return (bitboard & ~(1 << from_index)) | (1 << to_index)

    @staticmethod
    def count_boxes(bitboard: Bitboard) -> int:
        """Count number of boxes (popcount)."""
        return bitboard.bit_count()

    @staticmethod
    def boxes_on_goals(box_bitboard: Bitboard, goal_mask: Bitboard) -> int:
        """Count how many boxes are on goal tiles."""
        return (box_bitboard & goal_mask).bit_count()

    @staticmethod
    def all_boxes_on_goals(box_bitboard: Bitboard, goal_mask: Bitboard) -> bool:
        """Check win condition: all boxes on goals.

        All box bits must be within the goal mask.
        """
        return (box_bitboard & goal_mask) == box_bitboard

    @staticmethod
    def from_indices(indices: tuple[TileIndex, ...]) -> Bitboard:
        """Create a bitboard from a tuple of tile indices."""
        bitboard: Bitboard = 0
        for idx in indices:
            bitboard |= 1 << idx
        return bitboard

    @staticmethod
    def to_indices(bitboard: Bitboard) -> tuple[TileIndex, ...]:
        """Convert a bitboard back to a sorted tuple of tile indices."""
        indices: list[TileIndex] = []
        remaining = bitboard
        while remaining:
            # Get index of lowest set bit
            idx = (remaining & -remaining).bit_length() - 1
            indices.append(idx)
            # Clear lowest set bit
            remaining &= remaining - 1
        return tuple(indices)
