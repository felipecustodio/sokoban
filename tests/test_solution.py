"""Tests for solution string parsing and generation."""

from sokoban_engine import Direction, MoveRecord
from sokoban_engine.io.solution import (
    parse_solution,
    solution_to_directions,
    solution_to_string,
    validate_solution_format,
)


class TestParseSolution:
    """Tests for parse_solution function."""

    def test_parse_lowercase(self):
        """Test parsing lowercase solution."""
        records = parse_solution("udlr")
        assert len(records) == 4
        assert records[0].direction == Direction.UP
        assert records[0].was_push is False
        assert records[1].direction == Direction.DOWN
        assert records[2].direction == Direction.LEFT
        assert records[3].direction == Direction.RIGHT

    def test_parse_uppercase_pushes(self):
        """Test parsing uppercase (push) moves."""
        records = parse_solution("UDLR")
        assert all(r.was_push for r in records)

    def test_parse_mixed(self):
        """Test parsing mixed case solution."""
        records = parse_solution("DDrdrruLruLLDllU")
        # First two are pushes (D)
        assert records[0].was_push is True
        assert records[1].was_push is True
        # Third is walk (r)
        assert records[2].was_push is False
        # Check last is push (U)
        assert records[-1].was_push is True
        assert records[-1].direction == Direction.UP

    def test_parse_ignores_whitespace(self):
        """Test that whitespace is ignored."""
        records = parse_solution("u d\nl\tr")
        assert len(records) == 4

    def test_parse_empty(self):
        """Test parsing empty solution."""
        records = parse_solution("")
        assert len(records) == 0


class TestSolutionToString:
    """Tests for solution_to_string function."""

    def test_simple_conversion(self):
        """Test converting records to string."""
        records = [
            MoveRecord(Direction.UP, False),
            MoveRecord(Direction.DOWN, True),
            MoveRecord(Direction.LEFT, False),
            MoveRecord(Direction.RIGHT, True),
        ]
        result = solution_to_string(records)
        assert result == "uDlR"

    def test_without_push_info(self):
        """Test conversion without push information."""
        records = [
            MoveRecord(Direction.UP, True),
            MoveRecord(Direction.DOWN, True),
        ]
        result = solution_to_string(records, include_pushes=False)
        assert result == "ud"

    def test_empty_list(self):
        """Test converting empty list."""
        result = solution_to_string([])
        assert result == ""


class TestSolutionToDirections:
    """Tests for solution_to_directions function."""

    def test_basic_conversion(self):
        """Test converting solution to direction list."""
        directions = solution_to_directions("udlr")
        assert directions == [
            Direction.UP,
            Direction.DOWN,
            Direction.LEFT,
            Direction.RIGHT,
        ]

    def test_ignores_case(self):
        """Test that case doesn't affect direction parsing."""
        directions = solution_to_directions("UdLr")
        assert directions == [
            Direction.UP,
            Direction.DOWN,
            Direction.LEFT,
            Direction.RIGHT,
        ]


class TestValidateSolutionFormat:
    """Tests for validate_solution_format function."""

    def test_valid_solution(self):
        """Test valid solution strings."""
        assert validate_solution_format("udlr")
        assert validate_solution_format("UDLR")
        assert validate_solution_format("DDrdrruLruLLDllU")
        assert validate_solution_format("u d l r")

    def test_invalid_solution(self):
        """Test invalid solution strings."""
        assert not validate_solution_format("udlrx")  # 'x' is invalid
        assert not validate_solution_format("up")  # 'p' is invalid


class TestRoundtrip:
    """Test parsing then generating returns equivalent solution."""

    def test_roundtrip(self):
        """Test parse->generate roundtrip."""
        original = "DDrdrruLruLLDllU"
        records = parse_solution(original)
        result = solution_to_string(records)
        assert result == original
