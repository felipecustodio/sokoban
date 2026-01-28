"""LIFO stack for move history with undo/redo support.

Stores only move records, not full game states.
States are reconstructed by inverting moves.
"""

from sokoban_engine.board.static_map import StaticMap
from sokoban_engine.core.direction import opposite_direction
from sokoban_engine.history.move_record import MoveRecord
from sokoban_engine.state.game_state import GameState


class UndoStack:
    """LIFO stack for move history with redo support.

    Stores only move records (direction + push flag), not full states.
    This is extremely memory-efficient.
    """

    def __init__(self) -> None:
        """Initialize empty undo stack."""
        self._history: list[MoveRecord] = []
        self._redo_stack: list[MoveRecord] = []
        self._push_count: int = 0

    def push(self, record: MoveRecord) -> None:
        """Record a move. Clears redo stack."""
        self._history.append(record)
        if record.was_push:
            self._push_count += 1
        # Any new move invalidates redo history
        self._redo_stack.clear()

    def pop(self) -> MoveRecord | None:
        """Pop last move for undo. Returns None if empty."""
        if not self._history:
            return None
        record = self._history.pop()
        if record.was_push:
            self._push_count -= 1
        self._redo_stack.append(record)
        return record

    def redo_pop(self) -> MoveRecord | None:
        """Pop from redo stack. Returns None if empty."""
        if not self._redo_stack:
            return None
        record = self._redo_stack.pop()
        self._history.append(record)
        if record.was_push:
            self._push_count += 1
        return record

    @property
    def move_count(self) -> int:
        """Total number of moves in history."""
        return len(self._history)

    @property
    def push_count(self) -> int:
        """Number of push moves in history."""
        return self._push_count

    @property
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return len(self._history) > 0

    @property
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return len(self._redo_stack) > 0

    def clear(self) -> None:
        """Clear all history."""
        self._history.clear()
        self._redo_stack.clear()
        self._push_count = 0

    def get_history(self) -> list[MoveRecord]:
        """Get a copy of the move history."""
        return self._history.copy()


def invert_move(
    static_map: StaticMap,
    state: GameState,
    record: MoveRecord,
) -> GameState:
    """Compute previous state by inverting a move.

    For walks: player moves in opposite direction.
    For pushes: player and box both move in opposite direction.

    Args:
        static_map: The static map for neighbor lookups.
        state: Current state (after the move we're inverting).
        record: The move record to invert.

    Returns:
        The state before the move was made.
    """
    opposite = opposite_direction(record.direction)

    # Player's previous position is in the opposite direction
    prev_player_idx = static_map.get_neighbor(state.player_index, opposite)

    if not record.was_push:
        # Simple walk: just move player back
        return GameState(
            player_index=prev_player_idx,
            box_indices=state.box_indices,
            box_bitboard=state.box_bitboard,
        )

    # Push: the box is now one tile ahead of player in the push direction
    # It was at the player's current position before the push
    box_current_idx = static_map.get_neighbor(state.player_index, record.direction)
    box_prev_idx = state.player_index

    # Move box back to its previous position
    return state.with_move(
        new_player_index=prev_player_idx,
        pushed_box_from=box_current_idx,
        pushed_box_to=box_prev_idx,
    )


def replay_move(
    static_map: StaticMap,
    state: GameState,
    record: MoveRecord,
) -> GameState:
    """Replay a move from history (for redo).

    Args:
        static_map: The static map for neighbor lookups.
        state: Current state (before the move).
        record: The move record to replay.

    Returns:
        The state after the move.
    """
    # Get new player position
    new_player_idx = static_map.get_neighbor(state.player_index, record.direction)

    if not record.was_push:
        # Simple walk
        return state.with_move(new_player_idx)

    # Push: box moves from new_player_idx to one tile further
    box_from_idx = new_player_idx
    box_to_idx = static_map.get_neighbor(new_player_idx, record.direction)

    return state.with_move(
        new_player_index=new_player_idx,
        pushed_box_from=box_from_idx,
        pushed_box_to=box_to_idx,
    )
