"""Main Game class - the public facade for the Sokoban engine.

This class combines all engine components and provides a clean API
for game control, suitable for building rendering engines or solvers on top.
"""

from typing import Self

from sokoban_engine.board.parser import ParsedLevel, parse_level
from sokoban_engine.board.static_map import StaticMap
from sokoban_engine.core.direction import Direction
from sokoban_engine.core.types import MoveResult, Position, TileIndex
from sokoban_engine.history.move_record import MoveRecord
from sokoban_engine.history.undo_stack import UndoStack, invert_move, replay_move
from sokoban_engine.logic.move import apply_move, can_move, get_legal_move_directions
from sokoban_engine.logic.reachability import get_legal_pushes
from sokoban_engine.state.game_state import GameState


class Game:
    """Main facade for the Sokoban engine.

    Provides high-level API for game control while internally
    managing static map, state, and history.

    Example:
        >>> level = '''
        ... #####
        ... #@$.#
        ... #####
        ... '''
        >>> game = Game(level)
        >>> result = game.move(Direction.RIGHT)
        >>> print(result)  # MoveResult.SUCCESS_PUSH or MoveResult.WIN
    """

    def __init__(self, level_string: str) -> None:
        """Initialize game from XSB-format level string.

        Args:
            level_string: Multi-line string in standard Sokoban format
                # = wall, @ = player, $ = box, . = goal
                + = player on goal, * = box on goal, space = floor

        Raises:
            ParseError: If level format is invalid.
        """
        self._parsed: ParsedLevel = parse_level(level_string)
        self._static_map: StaticMap = StaticMap.from_parsed_level(self._parsed)
        self._initial_state: GameState = GameState.from_parsed_level(
            self._parsed, self._static_map
        )
        self._state: GameState = self._initial_state.copy()
        self._history: UndoStack = UndoStack()

    # === State Queries ===

    @property
    def width(self) -> int:
        """Board width in cells."""
        return self._static_map.width

    @property
    def height(self) -> int:
        """Board height in cells."""
        return self._static_map.height

    @property
    def player_position(self) -> Position:
        """Current player position as (row, col)."""
        return self._state.get_player_position(self._static_map)

    @property
    def box_positions(self) -> tuple[Position, ...]:
        """Current box positions as tuple of (row, col)."""
        return self._state.get_box_positions(self._static_map)

    @property
    def goal_positions(self) -> tuple[Position, ...]:
        """Static goal positions."""
        return self._static_map.goal_positions

    @property
    def num_boxes(self) -> int:
        """Number of boxes in the level."""
        return len(self._state.box_indices)

    @property
    def is_solved(self) -> bool:
        """True if all boxes are on goals."""
        return self._state.is_solved(self._static_map.goal_mask)

    @property
    def boxes_on_goals(self) -> int:
        """Number of boxes currently on goal tiles."""
        return self._state.boxes_on_goals(self._static_map.goal_mask)

    @property
    def move_count(self) -> int:
        """Total moves made (including walks and pushes)."""
        return self._history.move_count

    @property
    def push_count(self) -> int:
        """Total box pushes made."""
        return self._history.push_count

    # === Cell Queries ===

    def is_wall(self, row: int, col: int) -> bool:
        """Check if cell is a wall."""
        return self._static_map.is_wall(row, col)

    def is_goal(self, row: int, col: int) -> bool:
        """Check if cell is a goal."""
        return self._static_map.is_goal(row, col)

    def is_box(self, row: int, col: int) -> bool:
        """Check if cell contains a box."""
        tile_idx = self._static_map.get_tile_index(row, col)
        if tile_idx == -1:
            return False
        return self._state.has_box_at(tile_idx)

    def is_player(self, row: int, col: int) -> bool:
        """Check if player is at this cell."""
        tile_idx = self._static_map.get_tile_index(row, col)
        return tile_idx == self._state.player_index

    def is_floor(self, row: int, col: int) -> bool:
        """Check if cell is a passable floor (not wall)."""
        return not self._static_map.is_wall(row, col)

    # === Move Operations ===

    def move(self, direction: Direction) -> MoveResult:
        """Attempt to move player in direction.

        Args:
            direction: Direction to move.

        Returns:
            MoveResult indicating success/failure and type.
        """
        new_state, result = apply_move(self._static_map, self._state, direction)

        if new_state is not None:
            # Move succeeded - update state and record history
            was_push = result in (MoveResult.SUCCESS_PUSH, MoveResult.WIN)
            self._history.push(MoveRecord(direction, was_push))
            self._state = new_state

        return result

    def can_move(self, direction: Direction) -> bool:
        """Check if move in direction is valid without executing."""
        return can_move(self._static_map, self._state, direction)

    def get_legal_moves(self) -> list[Direction]:
        """Get all currently legal move directions."""
        return get_legal_move_directions(self._static_map, self._state)

    # === Push-Centric API (for solvers) ===

    def get_legal_pushes(self) -> list[tuple[TileIndex, Direction]]:
        """Get all legal push moves: (box_index, direction).

        Considers player reachability to push positions.
        This is useful for solvers that want to enumerate possible pushes.

        Returns:
            List of (box_tile_index, push_direction) pairs.
        """
        return get_legal_pushes(
            self._static_map,
            self._state.player_index,
            self._state.box_bitboard,
        )

    # === History Operations ===

    def undo(self) -> bool:
        """Undo last move. Returns False if no history."""
        record = self._history.pop()
        if record is None:
            return False

        self._state = invert_move(self._static_map, self._state, record)
        return True

    def redo(self) -> bool:
        """Redo previously undone move. Returns False if nothing to redo."""
        record = self._history.redo_pop()
        if record is None:
            return False

        self._state = replay_move(self._static_map, self._state, record)
        return True

    @property
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self._history.can_undo

    @property
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self._history.can_redo

    def reset(self) -> None:
        """Reset to initial state, clearing history."""
        self._state = self._initial_state.copy()
        self._history.clear()

    def get_move_history(self) -> list[MoveRecord]:
        """Get list of all moves made."""
        return self._history.get_history()

    # === State Export (for solvers/serialization) ===

    def get_state_hash(self) -> int:
        """Get hash of current state for memoization."""
        return hash(self._state)

    def get_canonical_state(self) -> tuple[TileIndex, tuple[TileIndex, ...]]:
        """Get canonical (player_index, sorted_box_indices) representation."""
        return (self._state.player_index, self._state.box_indices)

    def clone(self) -> Self:
        """Create independent copy of game (for search branches).

        The clone shares the static map but has independent state and history.
        """
        cloned = self.__class__.__new__(self.__class__)
        cloned._parsed = self._parsed
        cloned._static_map = self._static_map  # Shared (immutable)
        cloned._initial_state = self._initial_state
        cloned._state = self._state.copy()
        cloned._history = UndoStack()  # Fresh history for clone
        return cloned

    # === Internal Access (for advanced use) ===

    @property
    def static_map(self) -> StaticMap:
        """Access the static map (for advanced operations)."""
        return self._static_map

    @property
    def state(self) -> GameState:
        """Access the current game state (for advanced operations)."""
        return self._state
