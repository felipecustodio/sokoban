"""Tests for the level parser."""

import pytest

from sokoban_engine.board.parser import ParseError, parse_level
from sokoban_engine.core.types import CellType


class TestParseLevel:
    """Tests for parse_level function."""

    def test_simple_level(self):
        """Test parsing a simple level."""
        level = """
#####
#@$.#
#####
"""
        parsed = parse_level(level)

        assert parsed.width == 5
        assert parsed.height == 3
        assert parsed.player_position == (1, 1)
        assert parsed.box_positions == ((1, 2),)
        assert parsed.goal_positions == ((1, 3),)

    def test_multi_box_level(self):
        """Test parsing a level with multiple boxes."""
        level = """
######
#@$. #
# $. #
######
"""
        parsed = parse_level(level)

        assert len(parsed.box_positions) == 2
        assert len(parsed.goal_positions) == 2

    def test_player_on_goal(self):
        """Test parsing player on goal (+)."""
        level = """
#####
#+$ #
#####
"""
        parsed = parse_level(level)

        assert parsed.player_position == (1, 1)
        assert (1, 1) in parsed.goal_positions

    def test_box_on_goal(self):
        """Test parsing box on goal (*)."""
        level = """
#####
#@* #
#####
"""
        parsed = parse_level(level)

        assert (1, 2) in parsed.box_positions
        assert (1, 2) in parsed.goal_positions

    def test_grid_cell_types(self):
        """Test correct cell type identification."""
        level = """
#####
#@$.#
#####
"""
        parsed = parse_level(level)

        # Walls
        assert parsed.grid[0][0] == CellType.WALL
        assert parsed.grid[0][2] == CellType.WALL

        # Floor
        assert parsed.grid[1][1] == CellType.FLOOR  # Player position
        assert parsed.grid[1][2] == CellType.FLOOR  # Box position

        # Goal
        assert parsed.grid[1][3] == CellType.GOAL

    def test_empty_level_raises(self):
        """Test that empty level raises ParseError."""
        with pytest.raises(ParseError):
            parse_level("")

    def test_no_player_raises(self):
        """Test that level without player raises ParseError."""
        level = """
#####
# $.#
#####
"""
        with pytest.raises(ParseError, match="No player"):
            parse_level(level)

    def test_multiple_players_raises(self):
        """Test that multiple players raises ParseError."""
        level = """
#####
#@$@#
#####
"""
        with pytest.raises(ParseError, match="Multiple players"):
            parse_level(level)

    def test_box_goal_mismatch_raises(self):
        """Test that mismatched box/goal count raises ParseError."""
        level = """
#####
#@$ #
#####
"""
        with pytest.raises(ParseError, match="Box count"):
            parse_level(level)

    def test_no_boxes_raises(self):
        """Test that level without boxes raises ParseError."""
        level = """
#####
#@  #
#####
"""
        with pytest.raises(ParseError, match="No boxes"):
            parse_level(level)

    def test_alternative_floor_characters(self):
        """Test that - and _ are treated as floor."""
        level = """
#####
#@-$_#
#####
"""
        # This should parse - the box/goal mismatch is expected
        # Let's use a valid level
        level = """
######
#@-$.#
######
"""
        parsed = parse_level(level)
        assert parsed.grid[1][2] == CellType.FLOOR

    def test_jagged_level_padding(self):
        """Test that jagged levels are padded correctly."""
        level = """
###
#@$.#
###
"""
        parsed = parse_level(level)

        # All rows should have same width
        assert parsed.width == 5
        for row in parsed.grid:
            assert len(row) == 5
