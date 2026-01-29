"""Tests for Zobrist hashing and transposition table."""

from sokoban_engine import Direction, Game
from sokoban_engine.state.transposition import TranspositionTable
from sokoban_engine.state.zobrist import ZobristHasher

# Simple level for testing:
#   #####
#   #@ .#
#   # $ #
#   #   #
#   #####
# Player at (1,1), box at (2,2), goal at (1,3)
SIMPLE_LEVEL = """\
#####
#@ .#
# $ #
#   #
#####
"""

# Level where a push is possible:
#   #####
#   #@$.#
#   #####
PUSH_LEVEL = """\
#####
#@$.#
#####
"""


class TestZobristHasher:
    """Tests for ZobristHasher."""

    def test_hash_deterministic(self):
        """Same state always produces the same hash."""
        hasher = ZobristHasher(10, seed=42)
        h1 = hasher.hash_state(0, (1, 2, 3))
        h2 = hasher.hash_state(0, (1, 2, 3))
        assert h1 == h2

    def test_different_states_different_hashes(self):
        """Player at different tiles produces different hashes."""
        hasher = ZobristHasher(10, seed=42)
        h1 = hasher.hash_state(0, (5,))
        h2 = hasher.hash_state(1, (5,))
        assert h1 != h2

    def test_incremental_walk(self):
        """update_walk matches full hash_state recomputation."""
        hasher = ZobristHasher(10, seed=42)
        boxes = (3, 5, 7)
        h_before = hasher.hash_state(0, boxes)
        h_incremental = hasher.update_walk(h_before, old_player=0, new_player=1)
        h_recomputed = hasher.hash_state(1, boxes)
        assert h_incremental == h_recomputed

    def test_incremental_push(self):
        """update_push matches full hash_state recomputation."""
        hasher = ZobristHasher(10, seed=42)
        boxes_before = (3, 5, 7)
        boxes_after = (4, 5, 7)  # box at 3 pushed to 4
        h_before = hasher.hash_state(2, boxes_before)
        h_incremental = hasher.update_push(
            h_before, old_player=2, new_player=3, box_from=3, box_to=4
        )
        h_recomputed = hasher.hash_state(3, boxes_after)
        assert h_incremental == h_recomputed

    def test_hash_reversible(self):
        """Walk then undo returns to original hash."""
        hasher = ZobristHasher(10, seed=42)
        boxes = (3, 5)
        h_original = hasher.hash_state(0, boxes)
        h_walked = hasher.update_walk(h_original, old_player=0, new_player=1)
        h_undone = hasher.update_walk(h_walked, old_player=1, new_player=0)
        assert h_undone == h_original

    def test_push_reversible(self):
        """Push then undo returns to original hash."""
        hasher = ZobristHasher(10, seed=42)
        boxes = (3, 5)
        h_original = hasher.hash_state(2, boxes)
        h_pushed = hasher.update_push(
            h_original, old_player=2, new_player=3, box_from=3, box_to=4
        )
        # Undo: player goes back from 3 to 2, box goes back from 4 to 3
        h_undone = hasher.update_push(
            h_pushed, old_player=3, new_player=2, box_from=4, box_to=3
        )
        assert h_undone == h_original

    def test_seed_reproducibility(self):
        """Same seed produces identical keys and hashes."""
        h1 = ZobristHasher(10, seed=123)
        h2 = ZobristHasher(10, seed=123)
        state_hash_1 = h1.hash_state(0, (1, 2))
        state_hash_2 = h2.hash_state(0, (1, 2))
        assert state_hash_1 == state_hash_2

    def test_different_seeds_different_hashes(self):
        """Different seeds produce different hashes."""
        h1 = ZobristHasher(10, seed=0)
        h2 = ZobristHasher(10, seed=1)
        hash1 = h1.hash_state(0, (1, 2))
        hash2 = h2.hash_state(0, (1, 2))
        assert hash1 != hash2


class TestTranspositionTable:
    """Tests for TranspositionTable."""

    def test_store_lookup(self):
        """Basic store/lookup/contains."""
        tt: TranspositionTable[int] = TranspositionTable()
        tt.store(12345, 42)
        assert 12345 in tt
        assert tt.lookup(12345) == 42
        assert len(tt) == 1

    def test_missing_key(self):
        """Lookup returns None for unknown hash."""
        tt: TranspositionTable[str] = TranspositionTable()
        assert tt.lookup(99999) is None
        assert 99999 not in tt

    def test_clear(self):
        """Clear removes all entries."""
        tt: TranspositionTable[int] = TranspositionTable()
        tt.store(1, 10)
        tt.store(2, 20)
        assert len(tt) == 2
        tt.clear()
        assert len(tt) == 0
        assert tt.lookup(1) is None

    def test_overwrite(self):
        """Storing same key overwrites previous data."""
        tt: TranspositionTable[int] = TranspositionTable()
        tt.store(1, 10)
        tt.store(1, 20)
        assert tt.lookup(1) == 20
        assert len(tt) == 1


class TestGameZobristIntegration:
    """Tests for Zobrist hashing integrated into Game."""

    def test_game_state_hash_incremental(self):
        """game.move() then check get_state_hash() matches manual Zobrist."""
        game = Game(PUSH_LEVEL)
        initial_hash = game.get_state_hash()

        # Make a push: player right pushes box right
        result = game.move(Direction.RIGHT)
        assert result.name.startswith("SUCCESS") or result.name == "WIN"

        # Manually compute what the hash should be
        zobrist = game._zobrist
        expected = zobrist.hash_state(
            game.state.player_index, game.state.box_indices
        )
        assert game.get_state_hash() == expected
        assert game.get_state_hash() != initial_hash

    def test_game_undo_restores_hash(self):
        """move + undo returns hash to original."""
        game = Game(SIMPLE_LEVEL)
        original_hash = game.get_state_hash()

        # Walk down
        game.move(Direction.DOWN)
        assert game.get_state_hash() != original_hash

        # Undo
        game.undo()
        assert game.get_state_hash() == original_hash

    def test_game_undo_push_restores_hash(self):
        """Push + undo returns hash to original."""
        game = Game(PUSH_LEVEL)
        original_hash = game.get_state_hash()

        game.move(Direction.RIGHT)
        assert game.get_state_hash() != original_hash

        game.undo()
        assert game.get_state_hash() == original_hash

    def test_game_redo_restores_hash(self):
        """move + undo + redo returns to moved hash."""
        game = Game(SIMPLE_LEVEL)

        game.move(Direction.DOWN)
        moved_hash = game.get_state_hash()

        game.undo()
        game.redo()
        assert game.get_state_hash() == moved_hash

    def test_game_reset_restores_hash(self):
        """reset() returns hash to initial."""
        game = Game(SIMPLE_LEVEL)
        original_hash = game.get_state_hash()

        game.move(Direction.DOWN)
        game.move(Direction.DOWN)
        assert game.get_state_hash() != original_hash

        game.reset()
        assert game.get_state_hash() == original_hash

    def test_game_clone_shares_zobrist(self):
        """Cloned game produces same hash for same state."""
        game = Game(SIMPLE_LEVEL)
        clone = game.clone()

        assert clone.get_state_hash() == game.get_state_hash()
        assert clone._zobrist is game._zobrist

        # Both should update consistently
        game.move(Direction.DOWN)
        clone.move(Direction.DOWN)
        assert clone.get_state_hash() == game.get_state_hash()
