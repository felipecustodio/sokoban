"""Dynamic game state: player and box positions.

The GameState contains only the mutable elements that change during gameplay.
It uses tile indices for compact representation.
"""

from dataclasses import dataclass
from typing import Self

from sokoban_engine.board.parser import ParsedLevel
from sokoban_engine.board.static_map import StaticMap
from sokoban_engine.core.types import Bitboard, Position, TileIndex
from sokoban_engine.state.bitboard import BitboardOps


@dataclass(slots=True)
class GameState:
    """Dynamic game state: player position and box positions.

    Uses tile indices (not grid coordinates) for compactness.
    Box indices are always kept in sorted canonical order for consistent hashing.

    Attributes:
        player_index: The tile index where the player is located.
        box_indices: Sorted tuple of tile indices where boxes are located.
        box_bitboard: Bitboard representation of boxes for fast collision checks.
    """

    player_index: TileIndex
    box_indices: tuple[TileIndex, ...]
    box_bitboard: Bitboard

    def __hash__(self) -> int:
        """Hash based on canonical representation."""
        return hash((self.player_index, self.box_indices))

    def __eq__(self, other: object) -> bool:
        """Equality based on player and box positions."""
        if not isinstance(other, GameState):
            return NotImplemented
        return (
            self.player_index == other.player_index
            and self.box_indices == other.box_indices
        )

    def copy(self) -> Self:
        """Create a copy of the state.

        Since box_indices is a tuple (immutable), we just copy the reference.
        """
        return self.__class__(
            player_index=self.player_index,
            box_indices=self.box_indices,
            box_bitboard=self.box_bitboard,
        )

    @classmethod
    def from_positions(
        cls,
        player_index: TileIndex,
        box_indices: list[TileIndex] | tuple[TileIndex, ...],
    ) -> Self:
        """Create state with automatic canonicalization.

        Args:
            player_index: Tile index of player.
            box_indices: Collection of tile indices for boxes (will be sorted).

        Returns:
            New GameState with canonical box ordering.
        """
        sorted_boxes = tuple(sorted(box_indices))
        bitboard = BitboardOps.from_indices(sorted_boxes)
        return cls(player_index, sorted_boxes, bitboard)

    @classmethod
    def from_parsed_level(cls, parsed: ParsedLevel, static_map: StaticMap) -> Self:
        """Create initial state from a parsed level.

        Args:
            parsed: The parsed level data.
            static_map: The static map for index lookups.

        Returns:
            Initial GameState for the level.
        """
        # Convert player position to tile index
        player_row, player_col = parsed.player_position
        player_index = static_map.position_to_index[player_row][player_col]

        # Convert box positions to tile indices
        box_indices: list[TileIndex] = []
        for row, col in parsed.box_positions:
            box_indices.append(static_map.position_to_index[row][col])

        return cls.from_positions(player_index, box_indices)

    def has_box_at(self, tile_index: TileIndex) -> bool:
        """Check if there's a box at the given tile index. O(1)."""
        return BitboardOps.has_box(self.box_bitboard, tile_index)

    def get_player_position(self, static_map: StaticMap) -> Position:
        """Get the player's position as (row, col)."""
        return static_map.get_position(self.player_index)

    def get_box_positions(self, static_map: StaticMap) -> tuple[Position, ...]:
        """Get all box positions as (row, col) tuples."""
        return tuple(static_map.get_position(idx) for idx in self.box_indices)

    def is_solved(self, goal_mask: Bitboard) -> bool:
        """Check if the puzzle is solved (all boxes on goals)."""
        return BitboardOps.all_boxes_on_goals(self.box_bitboard, goal_mask)

    def boxes_on_goals(self, goal_mask: Bitboard) -> int:
        """Count how many boxes are on goal tiles."""
        return BitboardOps.boxes_on_goals(self.box_bitboard, goal_mask)

    def with_move(
        self,
        new_player_index: TileIndex,
        pushed_box_from: TileIndex | None = None,
        pushed_box_to: TileIndex | None = None,
    ) -> Self:
        """Create a new state after a move.

        Args:
            new_player_index: Where the player moves to.
            pushed_box_from: If pushing, the box's original tile.
            pushed_box_to: If pushing, the box's destination tile.

        Returns:
            New GameState reflecting the move.
        """
        if pushed_box_from is None:
            # Simple walk - no box movement
            return self.__class__(
                player_index=new_player_index,
                box_indices=self.box_indices,
                box_bitboard=self.box_bitboard,
            )

        # Push - update box position
        new_bitboard = BitboardOps.move_box(
            self.box_bitboard,
            pushed_box_from,
            pushed_box_to,  # type: ignore[arg-type]
        )
        new_box_indices = _update_box_indices(
            self.box_indices,
            pushed_box_from,
            pushed_box_to,  # type: ignore[arg-type]
        )

        return self.__class__(
            player_index=new_player_index,
            box_indices=new_box_indices,
            box_bitboard=new_bitboard,
        )


def _update_box_indices(
    box_indices: tuple[TileIndex, ...],
    from_idx: TileIndex,
    to_idx: TileIndex,
) -> tuple[TileIndex, ...]:
    """Update box indices maintaining sorted canonical order.

    Removes the box at from_idx and adds one at to_idx, keeping sorted order.
    """
    # Remove old position, add new, re-sort
    new_list = [idx for idx in box_indices if idx != from_idx]
    new_list.append(to_idx)
    return tuple(sorted(new_list))
