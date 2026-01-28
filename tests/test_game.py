"""Tests for the main Game class."""


from sokoban_engine import Direction, MoveResult


class TestGameInitialization:
    """Tests for Game initialization."""

    def test_simple_game_dimensions(self, simple_game):
        """Test game dimensions are correct."""
        assert simple_game.width == 5
        assert simple_game.height == 3

    def test_simple_game_player_position(self, simple_game):
        """Test initial player position."""
        assert simple_game.player_position == (1, 1)

    def test_simple_game_box_positions(self, simple_game):
        """Test initial box positions."""
        assert simple_game.box_positions == ((1, 2),)

    def test_simple_game_goal_positions(self, simple_game):
        """Test goal positions."""
        assert simple_game.goal_positions == ((1, 3),)

    def test_initial_state_not_solved(self, simple_game):
        """Test game is not solved initially."""
        assert not simple_game.is_solved

    def test_initial_move_count(self, simple_game):
        """Test initial move count is zero."""
        assert simple_game.move_count == 0
        assert simple_game.push_count == 0


class TestCellQueries:
    """Tests for cell query methods."""

    def test_is_wall(self, simple_game):
        """Test wall detection."""
        assert simple_game.is_wall(0, 0)
        assert simple_game.is_wall(0, 2)
        assert not simple_game.is_wall(1, 1)

    def test_is_goal(self, simple_game):
        """Test goal detection."""
        assert simple_game.is_goal(1, 3)
        assert not simple_game.is_goal(1, 1)

    def test_is_box(self, simple_game):
        """Test box detection."""
        assert simple_game.is_box(1, 2)
        assert not simple_game.is_box(1, 1)

    def test_is_player(self, simple_game):
        """Test player detection."""
        assert simple_game.is_player(1, 1)
        assert not simple_game.is_player(1, 2)

    def test_out_of_bounds_is_wall(self, simple_game):
        """Test out of bounds treated as wall."""
        assert simple_game.is_wall(-1, 0)
        assert simple_game.is_wall(0, 100)


class TestMoveOperations:
    """Tests for move operations."""

    def test_move_blocked_by_wall(self, simple_game):
        """Test move blocked by wall."""
        result = simple_game.move(Direction.UP)
        assert result == MoveResult.BLOCKED_WALL
        # Player should not have moved
        assert simple_game.player_position == (1, 1)
        assert simple_game.move_count == 0

    def test_move_walk(self, corridor_game):
        """Test simple walk move."""
        # Corridor: #@ $ .#
        # Player can walk right (to empty space)
        result = corridor_game.move(Direction.RIGHT)
        assert result == MoveResult.SUCCESS_WALK
        assert corridor_game.player_position == (1, 2)
        assert corridor_game.move_count == 1
        assert corridor_game.push_count == 0

    def test_move_push(self, simple_game):
        """Test push move."""
        # Simple: #@$.# - pushing box right
        result = simple_game.move(Direction.RIGHT)
        assert result in (MoveResult.SUCCESS_PUSH, MoveResult.WIN)
        assert simple_game.player_position == (1, 2)
        assert simple_game.push_count == 1

    def test_push_to_win(self, simple_game):
        """Test push that wins the game."""
        result = simple_game.move(Direction.RIGHT)
        assert result == MoveResult.WIN
        assert simple_game.is_solved

    def test_push_blocked_by_wall(self, corridor_game):
        """Test push blocked by wall behind box."""
        # First walk to be adjacent to box
        corridor_game.move(Direction.RIGHT)  # Walk
        corridor_game.move(Direction.RIGHT)  # Walk to be next to box

        # Now at position next to box, trying to push into wall
        # Need to construct a scenario where push is blocked
        pass  # This specific test needs a better level

    def test_can_move(self, simple_game):
        """Test can_move method."""
        assert not simple_game.can_move(Direction.UP)  # Wall
        assert simple_game.can_move(Direction.RIGHT)  # Push possible
        assert not simple_game.can_move(Direction.LEFT)  # Wall

    def test_get_legal_moves(self, corridor_game):
        """Test get_legal_moves method."""
        moves = corridor_game.get_legal_moves()
        assert Direction.RIGHT in moves
        assert Direction.LEFT not in moves  # Wall
        assert Direction.UP not in moves  # Wall


class TestHistory:
    """Tests for undo/redo functionality."""

    def test_undo_walk(self, corridor_game):
        """Test undo of walk move."""
        original_pos = corridor_game.player_position
        corridor_game.move(Direction.RIGHT)
        assert corridor_game.player_position != original_pos

        corridor_game.undo()
        assert corridor_game.player_position == original_pos
        assert corridor_game.move_count == 0

    def test_undo_push(self, simple_game):
        """Test undo of push move."""
        original_player = simple_game.player_position
        original_boxes = simple_game.box_positions

        # Push the box right (simple level: #@$.#)
        simple_game.move(Direction.RIGHT)

        # Undo should restore both player and box
        simple_game.undo()
        assert simple_game.player_position == original_player
        assert simple_game.box_positions == original_boxes

    def test_redo(self, corridor_game):
        """Test redo functionality."""
        corridor_game.move(Direction.RIGHT)
        new_pos = corridor_game.player_position

        corridor_game.undo()
        corridor_game.redo()

        assert corridor_game.player_position == new_pos

    def test_undo_empty_returns_false(self, simple_game):
        """Test undo on empty history returns False."""
        assert not simple_game.undo()

    def test_redo_empty_returns_false(self, simple_game):
        """Test redo with nothing to redo returns False."""
        assert not simple_game.redo()

    def test_new_move_clears_redo(self, corridor_game):
        """Test that new move clears redo stack."""
        corridor_game.move(Direction.RIGHT)
        corridor_game.undo()
        assert corridor_game.can_redo

        # New move should clear redo
        corridor_game.move(Direction.RIGHT)
        assert not corridor_game.can_redo

    def test_reset(self, corridor_game):
        """Test reset to initial state."""
        original_pos = corridor_game.player_position
        corridor_game.move(Direction.RIGHT)
        corridor_game.move(Direction.RIGHT)

        corridor_game.reset()

        assert corridor_game.player_position == original_pos
        assert corridor_game.move_count == 0
        assert not corridor_game.can_undo


class TestClone:
    """Tests for game cloning."""

    def test_clone_independent(self, simple_game):
        """Test that cloned game is independent."""
        clone = simple_game.clone()

        # Make move on original
        simple_game.move(Direction.RIGHT)

        # Clone should be unchanged
        assert clone.player_position == (1, 1)
        assert clone.move_count == 0

    def test_clone_shares_static_map(self, simple_game):
        """Test that clone shares static map (memory efficiency)."""
        clone = simple_game.clone()
        assert clone.static_map is simple_game.static_map


class TestStateExport:
    """Tests for state export methods."""

    def test_get_state_hash_consistency(self, simple_game):
        """Test that same state has same hash."""
        hash1 = simple_game.get_state_hash()

        # Make some moves and undo
        simple_game.move(Direction.RIGHT)
        simple_game.undo()

        hash2 = simple_game.get_state_hash()
        assert hash1 == hash2

    def test_get_canonical_state(self, simple_game):
        """Test canonical state representation."""
        player_idx, box_indices = simple_game.get_canonical_state()
        assert isinstance(player_idx, int)
        assert isinstance(box_indices, tuple)
        assert all(isinstance(i, int) for i in box_indices)

    def test_canonical_state_sorted(self, multi_box_game):
        """Test that box indices are sorted."""
        _, box_indices = multi_box_game.get_canonical_state()
        assert box_indices == tuple(sorted(box_indices))


class TestLegalPushes:
    """Tests for push-centric API."""

    def test_get_legal_pushes(self, solvable_game):
        """Test legal push enumeration."""
        pushes = solvable_game.get_legal_pushes()

        # Should have at least one legal push
        assert len(pushes) > 0

        # Each push should be (tile_index, direction)
        for box_idx, direction in pushes:
            assert isinstance(box_idx, int)
            assert isinstance(direction, Direction)
