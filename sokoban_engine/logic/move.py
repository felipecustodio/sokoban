"""Move application logic.

Handles both simple walks (player moves to empty cell) and pushes (player pushes a box).
"""

from sokoban_engine.board.static_map import StaticMap
from sokoban_engine.core.direction import Direction
from sokoban_engine.core.types import MoveResult, TileIndex
from sokoban_engine.state.bitboard import BitboardOps
from sokoban_engine.state.game_state import GameState


def apply_move(
    static_map: StaticMap,
    state: GameState,
    direction: Direction,
) -> tuple[GameState | None, MoveResult]:
    """Apply a move to the game state.

    Args:
        static_map: The static map with wall/goal information.
        state: Current game state.
        direction: Direction to move.

    Returns:
        (new_state, result) where new_state is None if move is invalid.
    """
    player_idx = state.player_index

    # Get adjacent tile in direction
    adjacent_idx = static_map.get_neighbor(player_idx, direction)

    # Check if blocked by wall
    if adjacent_idx == -1:
        return None, MoveResult.BLOCKED_WALL

    # Check if box is present at adjacent cell
    if BitboardOps.has_box(state.box_bitboard, adjacent_idx):
        return _apply_push(static_map, state, direction, adjacent_idx)

    # Empty floor: simple walk
    new_state = state.with_move(adjacent_idx)
    return new_state, MoveResult.SUCCESS_WALK


def _apply_push(
    static_map: StaticMap,
    state: GameState,
    direction: Direction,
    box_idx: TileIndex,
) -> tuple[GameState | None, MoveResult]:
    """Attempt to push a box.

    Args:
        static_map: The static map.
        state: Current state.
        direction: Direction of push.
        box_idx: The tile index of the box being pushed.

    Returns:
        (new_state, result)
    """
    # Check tile beyond the box
    beyond_idx = static_map.get_neighbor(box_idx, direction)

    # Wall beyond box
    if beyond_idx == -1:
        return None, MoveResult.BLOCKED_BOX

    # Another box beyond
    if BitboardOps.has_box(state.box_bitboard, beyond_idx):
        return None, MoveResult.BLOCKED_BOX

    # Push is valid: move box and player
    new_state = state.with_move(
        new_player_index=box_idx,  # Player moves to box's old position
        pushed_box_from=box_idx,
        pushed_box_to=beyond_idx,
    )

    # Check win condition
    if new_state.is_solved(static_map.goal_mask):
        return new_state, MoveResult.WIN

    return new_state, MoveResult.SUCCESS_PUSH


def can_move(
    static_map: StaticMap,
    state: GameState,
    direction: Direction,
) -> bool:
    """Check if a move in the given direction is valid.

    Args:
        static_map: The static map.
        state: Current state.
        direction: Direction to check.

    Returns:
        True if the move is valid.
    """
    player_idx = state.player_index
    adjacent_idx = static_map.get_neighbor(player_idx, direction)

    # Wall blocks
    if adjacent_idx == -1:
        return False

    # No box - can walk
    if not BitboardOps.has_box(state.box_bitboard, adjacent_idx):
        return True

    # Box present - check if can push
    beyond_idx = static_map.get_neighbor(adjacent_idx, direction)

    # Wall behind box
    if beyond_idx == -1:
        return False

    # Another box behind blocks push
    return not BitboardOps.has_box(state.box_bitboard, beyond_idx)


def get_legal_move_directions(
    static_map: StaticMap,
    state: GameState,
) -> list[Direction]:
    """Get all directions the player can move.

    Args:
        static_map: The static map.
        state: Current state.

    Returns:
        List of valid move directions.
    """
    return [d for d in Direction if can_move(static_map, state, d)]
