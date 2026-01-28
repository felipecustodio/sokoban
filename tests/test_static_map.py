"""Tests for StaticMap."""

from sokoban_engine.core.direction import Direction


class TestStaticMap:
    """Tests for StaticMap class."""

    def test_dimensions(self, simple_static_map):
        """Test map dimensions."""
        assert simple_static_map.width == 5
        assert simple_static_map.height == 3

    def test_num_floor_tiles(self, simple_static_map):
        """Test floor tile count."""
        # Simple level: #####
        #              #@$.#
        #              #####
        # Floor tiles: positions (1,1), (1,2), (1,3) = 3 tiles
        assert simple_static_map.num_floor_tiles == 3

    def test_get_tile_index(self, simple_static_map):
        """Test tile index lookup."""
        # Floor tiles should have indices 0, 1, 2
        idx1 = simple_static_map.get_tile_index(1, 1)
        idx2 = simple_static_map.get_tile_index(1, 2)
        idx3 = simple_static_map.get_tile_index(1, 3)

        assert idx1 >= 0
        assert idx2 >= 0
        assert idx3 >= 0
        assert len({idx1, idx2, idx3}) == 3  # All different

    def test_get_tile_index_wall(self, simple_static_map):
        """Test tile index for wall returns -1."""
        assert simple_static_map.get_tile_index(0, 0) == -1
        assert simple_static_map.get_tile_index(0, 2) == -1

    def test_get_position(self, simple_static_map):
        """Test position lookup from index."""
        # Get index for (1, 1)
        idx = simple_static_map.get_tile_index(1, 1)
        pos = simple_static_map.get_position(idx)
        assert pos == (1, 1)

    def test_neighbors(self, simple_static_map):
        """Test neighbor relationships."""
        # Tile at (1, 1) - left is wall, right is floor
        idx = simple_static_map.get_tile_index(1, 1)

        left_neighbor = simple_static_map.get_neighbor(idx, Direction.LEFT)
        right_neighbor = simple_static_map.get_neighbor(idx, Direction.RIGHT)
        up_neighbor = simple_static_map.get_neighbor(idx, Direction.UP)
        down_neighbor = simple_static_map.get_neighbor(idx, Direction.DOWN)

        assert left_neighbor == -1  # Wall
        assert right_neighbor >= 0  # Floor
        assert up_neighbor == -1  # Wall
        assert down_neighbor == -1  # Wall

    def test_is_wall(self, simple_static_map):
        """Test is_wall method."""
        assert simple_static_map.is_wall(0, 0)
        assert simple_static_map.is_wall(2, 2)
        assert not simple_static_map.is_wall(1, 1)

    def test_is_goal(self, simple_static_map):
        """Test is_goal method."""
        assert simple_static_map.is_goal(1, 3)
        assert not simple_static_map.is_goal(1, 1)
        assert not simple_static_map.is_goal(0, 0)  # Wall

    def test_is_goal_index(self, simple_static_map):
        """Test is_goal_index method."""
        goal_idx = simple_static_map.get_tile_index(1, 3)
        player_idx = simple_static_map.get_tile_index(1, 1)

        assert simple_static_map.is_goal_index(goal_idx)
        assert not simple_static_map.is_goal_index(player_idx)

    def test_goal_mask(self, simple_static_map):
        """Test goal mask has correct bits set."""
        goal_idx = simple_static_map.get_tile_index(1, 3)
        assert simple_static_map.goal_mask & (1 << goal_idx)

    def test_floor_mask(self, simple_static_map):
        """Test floor mask has all floor tiles."""
        assert (
            simple_static_map.floor_mask == (1 << simple_static_map.num_floor_tiles) - 1
        )

    def test_immutability(self, simple_static_map):
        """Test that StaticMap is frozen/immutable."""
        import pytest

        with pytest.raises(AttributeError):
            simple_static_map.width = 10
