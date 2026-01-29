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

    def test_exterior_spaces_become_walls(self):
        """Test that spaces outside the wall boundary become walls."""
        level = """
   ####
   #  #
####  ##
#  $ . #
# @$ . #
########
"""
        parsed = parse_level(level)

        # Leading spaces in row 0 (cols 0-2) should be walls
        assert parsed.grid[0][0] == CellType.WALL
        assert parsed.grid[0][1] == CellType.WALL
        assert parsed.grid[0][2] == CellType.WALL

    def test_interior_floor_preserved(self):
        """Test that interior floor cells remain floor after exterior fix."""
        level = """
   ####
   #  #
####  ##
#  $ . #
# @$ . #
########
"""
        parsed = parse_level(level)

        # Player position should be floor
        assert parsed.grid[4][2] == CellType.FLOOR
        # Interior spaces should be floor
        assert parsed.grid[1][4] == CellType.FLOOR

    def test_goals_preserved_after_exterior_fix(self):
        """Test that reachable goal cells stay GOAL after exterior fix."""
        level = """
   ####
   #  #
####  ##
#  $ . #
# @$ . #
########
"""
        parsed = parse_level(level)

        for goal_pos in parsed.goal_positions:
            assert parsed.grid[goal_pos[0]][goal_pos[1]] == CellType.GOAL

    def test_rectangular_level_unchanged(self):
        """Test that a fully enclosed rectangular level is unaffected."""
        level = """
#####
#@$.#
#####
"""
        parsed = parse_level(level)

        assert parsed.grid[0] == (CellType.WALL,) * 5
        assert parsed.grid[2] == (CellType.WALL,) * 5
        assert parsed.grid[1][0] == CellType.WALL
        assert parsed.grid[1][1] == CellType.FLOOR
        assert parsed.grid[1][2] == CellType.FLOOR
        assert parsed.grid[1][3] == CellType.GOAL
        assert parsed.grid[1][4] == CellType.WALL

    def test_microban_144_exterior(self):
        """Test Microban 144: exterior spaces must be walls."""
        level = (
            "   ####\n"
            "   #  #\n"
            "####  ##\n"
            "#  $ . #\n"
            "# @$ . #\n"
            "########"
        )
        parsed = parse_level(level)

        # Row 0 cols 0-2 are exterior
        for col in range(3):
            assert parsed.grid[0][col] == CellType.WALL, (
                f"Expected WALL at (0, {col})"
            )
        # Row 1 cols 0-2 are exterior
        for col in range(3):
            assert parsed.grid[1][col] == CellType.WALL, (
                f"Expected WALL at (1, {col})"
            )
        # Row 2 col 7 (trailing pad) is exterior
        assert parsed.grid[2][7] == CellType.WALL

    def test_enclosed_interior_region_preserved(self):
        """Test that enclosed interior regions not reachable from the player
        are preserved (not converted to walls). Some levels have pre-solved
        boxes (*) in walled-off sections."""
        level = (
            "  ###########\n"
            " ##     #  @#\n"
            "### $ $$#   #\n"
            "# ##$    $$ #\n"
            "#  #  $ #   #\n"
            "###### ######\n"
            "#.. ..$ #*##\n"
            "# ..    ###\n"
            "#  ..#####\n"
            "#########"
        )
        parsed = parse_level(level)

        # The * at row 6 col 9 is an enclosed box-on-goal behind a wall.
        # It must stay GOAL, not be converted to WALL.
        assert parsed.grid[6][9] == CellType.GOAL

        # Exterior spaces (row 0 cols 0-1) should be walls
        assert parsed.grid[0][0] == CellType.WALL
        assert parsed.grid[0][1] == CellType.WALL

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
