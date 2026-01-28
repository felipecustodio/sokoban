"""Tests for GameState."""

from sokoban_engine.state.game_state import GameState


class TestGameState:
    """Tests for GameState class."""

    def test_from_positions(self):
        """Test creating state from positions."""
        state = GameState.from_positions(
            player_index=0,
            box_indices=[3, 1, 2],  # Unsorted
        )

        assert state.player_index == 0
        assert state.box_indices == (1, 2, 3)  # Should be sorted

    def test_box_indices_canonical(self):
        """Test that box indices are kept in canonical (sorted) order."""
        state1 = GameState.from_positions(0, [1, 3, 2])
        state2 = GameState.from_positions(0, [3, 2, 1])
        state3 = GameState.from_positions(0, [2, 1, 3])

        assert state1.box_indices == state2.box_indices == state3.box_indices

    def test_hash_equality(self):
        """Test that equal states have equal hashes."""
        state1 = GameState.from_positions(0, [1, 2, 3])
        state2 = GameState.from_positions(0, [3, 1, 2])

        assert hash(state1) == hash(state2)
        assert state1 == state2

    def test_hash_inequality(self):
        """Test that different states have different hashes (usually)."""
        state1 = GameState.from_positions(0, [1, 2, 3])
        state2 = GameState.from_positions(1, [1, 2, 3])
        state3 = GameState.from_positions(0, [1, 2, 4])

        assert state1 != state2
        assert state1 != state3

    def test_has_box_at(self):
        """Test has_box_at method."""
        state = GameState.from_positions(0, [1, 3, 5])

        assert state.has_box_at(1)
        assert not state.has_box_at(2)
        assert state.has_box_at(3)
        assert not state.has_box_at(4)
        assert state.has_box_at(5)

    def test_copy(self):
        """Test state copying."""
        state = GameState.from_positions(0, [1, 2])
        copy = state.copy()

        assert copy.player_index == state.player_index
        assert copy.box_indices == state.box_indices
        assert copy.box_bitboard == state.box_bitboard
        assert copy is not state

    def test_with_move_walk(self):
        """Test with_move for simple walk."""
        state = GameState.from_positions(0, [2, 3])
        new_state = state.with_move(new_player_index=1)

        assert new_state.player_index == 1
        assert new_state.box_indices == state.box_indices
        assert new_state.box_bitboard == state.box_bitboard

    def test_with_move_push(self):
        """Test with_move for push."""
        state = GameState.from_positions(0, [1, 3])
        new_state = state.with_move(
            new_player_index=1,
            pushed_box_from=1,
            pushed_box_to=2,
        )

        assert new_state.player_index == 1
        assert 1 not in new_state.box_indices
        assert 2 in new_state.box_indices
        assert 3 in new_state.box_indices
        assert new_state.box_indices == (2, 3)  # Still sorted

    def test_is_solved(self):
        """Test is_solved method."""
        state = GameState.from_positions(0, [1, 2])

        goal_mask_partial = 0b010  # Only index 1 is goal
        goal_mask_full = 0b110  # Indices 1 and 2 are goals

        assert not state.is_solved(goal_mask_partial)
        assert state.is_solved(goal_mask_full)

    def test_boxes_on_goals(self):
        """Test boxes_on_goals count."""
        state = GameState.from_positions(0, [1, 2, 3])

        goal_mask = 0b1010  # Goals at 1 and 3
        assert state.boxes_on_goals(goal_mask) == 2

    def test_bitboard_sync(self):
        """Test that bitboard stays in sync with indices."""
        state = GameState.from_positions(0, [1, 3, 5])

        # Check bitboard matches indices
        from sokoban_engine.state.bitboard import BitboardOps

        assert BitboardOps.to_indices(state.box_bitboard) == state.box_indices
