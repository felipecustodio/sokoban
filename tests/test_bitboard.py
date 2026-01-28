"""Tests for bitboard operations."""

from sokoban_engine.state.bitboard import BitboardOps


class TestBitboardOps:
    """Tests for BitboardOps class."""

    def test_has_box_empty(self):
        """Test has_box on empty bitboard."""
        assert not BitboardOps.has_box(0, 0)
        assert not BitboardOps.has_box(0, 5)

    def test_has_box_present(self):
        """Test has_box when box is present."""
        bitboard = 0b1010  # Boxes at indices 1 and 3
        assert not BitboardOps.has_box(bitboard, 0)
        assert BitboardOps.has_box(bitboard, 1)
        assert not BitboardOps.has_box(bitboard, 2)
        assert BitboardOps.has_box(bitboard, 3)

    def test_set_box(self):
        """Test setting a box."""
        bitboard = 0
        bitboard = BitboardOps.set_box(bitboard, 5)
        assert BitboardOps.has_box(bitboard, 5)
        assert bitboard == 0b100000

    def test_clear_box(self):
        """Test clearing a box."""
        bitboard = 0b111  # Boxes at 0, 1, 2
        bitboard = BitboardOps.clear_box(bitboard, 1)
        assert not BitboardOps.has_box(bitboard, 1)
        assert BitboardOps.has_box(bitboard, 0)
        assert BitboardOps.has_box(bitboard, 2)

    def test_move_box(self):
        """Test moving a box."""
        bitboard = 0b001  # Box at index 0
        bitboard = BitboardOps.move_box(bitboard, 0, 3)
        assert not BitboardOps.has_box(bitboard, 0)
        assert BitboardOps.has_box(bitboard, 3)

    def test_count_boxes(self):
        """Test counting boxes."""
        assert BitboardOps.count_boxes(0) == 0
        assert BitboardOps.count_boxes(0b1) == 1
        assert BitboardOps.count_boxes(0b1010) == 2
        assert BitboardOps.count_boxes(0b11111) == 5

    def test_boxes_on_goals(self):
        """Test counting boxes on goals."""
        boxes = 0b1010  # Boxes at 1, 3
        goals = 0b1100  # Goals at 2, 3
        # Only box at 3 is on goal
        assert BitboardOps.boxes_on_goals(boxes, goals) == 1

    def test_all_boxes_on_goals_true(self):
        """Test all boxes on goals (win condition)."""
        boxes = 0b1010  # Boxes at 1, 3
        goals = 0b1110  # Goals at 1, 2, 3 (includes all box positions)
        assert BitboardOps.all_boxes_on_goals(boxes, goals)

    def test_all_boxes_on_goals_false(self):
        """Test not all boxes on goals."""
        boxes = 0b1010  # Boxes at 1, 3
        goals = 0b1000  # Goals only at 3
        assert not BitboardOps.all_boxes_on_goals(boxes, goals)

    def test_from_indices(self):
        """Test creating bitboard from indices."""
        indices = (1, 3, 5)
        bitboard = BitboardOps.from_indices(indices)
        assert BitboardOps.has_box(bitboard, 1)
        assert BitboardOps.has_box(bitboard, 3)
        assert BitboardOps.has_box(bitboard, 5)
        assert not BitboardOps.has_box(bitboard, 0)
        assert not BitboardOps.has_box(bitboard, 2)

    def test_to_indices(self):
        """Test converting bitboard to indices."""
        bitboard = 0b101010  # Bits at 1, 3, 5
        indices = BitboardOps.to_indices(bitboard)
        assert indices == (1, 3, 5)

    def test_roundtrip(self):
        """Test indices -> bitboard -> indices roundtrip."""
        original = (2, 5, 8, 10)
        bitboard = BitboardOps.from_indices(original)
        result = BitboardOps.to_indices(bitboard)
        assert result == original

    def test_large_indices(self):
        """Test with large tile indices (>64)."""
        bitboard = BitboardOps.set_box(0, 100)
        assert BitboardOps.has_box(bitboard, 100)
        assert BitboardOps.count_boxes(bitboard) == 1
