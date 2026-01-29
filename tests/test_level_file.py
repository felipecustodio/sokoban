"""Tests for level file loading, collections, and alternative characters."""

import pytest

from sokoban_engine import (
    Game,
    LevelInfo,
    load_collection_with_info,
    load_level,
    load_level_by_index,
    load_level_by_title,
    load_level_collection,
    load_levels_from_string,
)
from sokoban_engine.board.parser import ParseError, parse_level


# ---------------------------------------------------------------------------
# Alternative character support (B, &, X)
# ---------------------------------------------------------------------------


class TestAlternativeCharacters:
    """Tests for B (box), & (player), X (box-on-goal) parsing."""

    def test_ampersand_as_player(self):
        level = "#####\n#&$.#\n#####"
        parsed = parse_level(level)
        assert parsed.player_position == (1, 1)

    def test_b_as_box(self):
        level = "#####\n#@B.#\n#####"
        parsed = parse_level(level)
        assert (1, 2) in parsed.box_positions

    def test_x_as_box_on_goal(self):
        level = "#####\n#@X #\n#####"
        parsed = parse_level(level)
        assert (1, 2) in parsed.box_positions
        assert (1, 2) in parsed.goal_positions

    def test_ampersand_and_b_together(self):
        level = "######\n#&B. #\n######"
        game = Game(level)
        assert game.player_position == (1, 1)
        assert len(game.box_positions) == 1

    def test_mixed_standard_and_alternative(self):
        level = "#######\n#&B$..#\n#######"
        parsed = parse_level(level)
        assert parsed.player_position == (1, 1)
        assert len(parsed.box_positions) == 2
        assert len(parsed.goal_positions) == 2

    def test_game_from_alternative_chars(self):
        level = "######\n#& B.#\n######"
        game = load_level(level)
        assert not game.is_solved


# ---------------------------------------------------------------------------
# Level collection loading
# ---------------------------------------------------------------------------


class TestLoadLevelCollection:
    """Tests for loading level collections from strings."""

    COLLECTION = (
        "Level: First\n"
        "\n"
        "#####\n"
        "#@$.#\n"
        "#####\n"
        "\n"
        "Level: Second\n"
        "\n"
        "######\n"
        "# @$.#\n"
        "######\n"
    )

    def test_load_levels_from_string(self):
        games = load_levels_from_string(self.COLLECTION)
        assert len(games) == 2

    def test_collection_games_are_valid(self):
        games = load_levels_from_string(self.COLLECTION)
        for game in games:
            assert isinstance(game, Game)
            assert not game.is_solved

    def test_load_collection_with_titles(self, tmp_path):
        path = tmp_path / "test.txt"
        path.write_text(self.COLLECTION)
        infos = load_collection_with_info(path)
        assert len(infos) == 2
        assert infos[0].title == "First"
        assert infos[1].title == "Second"

    def test_title_set_on_game(self, tmp_path):
        path = tmp_path / "test.txt"
        path.write_text(self.COLLECTION)
        infos = load_collection_with_info(path)
        assert infos[0].game.title == "First"
        assert infos[1].game.title == "Second"

    def test_indices_are_sequential(self, tmp_path):
        path = tmp_path / "test.txt"
        path.write_text(self.COLLECTION)
        infos = load_collection_with_info(path)
        assert infos[0].index == 0
        assert infos[1].index == 1


# ---------------------------------------------------------------------------
# Title fallback from filename
# ---------------------------------------------------------------------------


class TestTitleFallback:
    """Tests for title generation when Level: headers are absent."""

    UNTITLED_COLLECTION = (
        "#####\n"
        "#@$.#\n"
        "#####\n"
        "\n"
        "######\n"
        "# @$.#\n"
        "######\n"
    )

    def test_fallback_uses_filename(self, tmp_path):
        path = tmp_path / "Microban.txt"
        path.write_text(self.UNTITLED_COLLECTION)
        infos = load_collection_with_info(path)
        assert infos[0].title == "Microban 1"
        assert infos[1].title == "Microban 2"

    def test_fallback_without_filename(self):
        """load_levels_from_string has no filename, uses generic fallback."""
        games = load_levels_from_string(self.UNTITLED_COLLECTION)
        assert len(games) == 2
        # Games loaded via load_levels_from_string get generic titles
        # (no filename available)


# ---------------------------------------------------------------------------
# Level selection by index and title
# ---------------------------------------------------------------------------


class TestLevelSelection:
    """Tests for load_level_by_index and load_level_by_title."""

    COLLECTION = (
        "Level: Alpha\n\n"
        "#####\n#@$.#\n#####\n\n"
        "Level: Beta\n\n"
        "######\n# @$.#\n######\n\n"
        "Level: Gamma\n\n"
        "#######\n#  @$.#\n#######\n"
    )

    @pytest.fixture
    def collection_path(self, tmp_path):
        path = tmp_path / "test_collection.txt"
        path.write_text(self.COLLECTION)
        return path

    def test_load_by_index_first(self, collection_path):
        info = load_level_by_index(collection_path, 0)
        assert info.title == "Alpha"
        assert info.index == 0

    def test_load_by_index_last(self, collection_path):
        info = load_level_by_index(collection_path, 2)
        assert info.title == "Gamma"
        assert info.index == 2

    def test_load_by_index_out_of_range(self, collection_path):
        with pytest.raises(IndexError):
            load_level_by_index(collection_path, 99)

    def test_load_by_index_negative(self, collection_path):
        with pytest.raises(IndexError):
            load_level_by_index(collection_path, -1)

    def test_load_by_title(self, collection_path):
        info = load_level_by_title(collection_path, "Beta")
        assert info.title == "Beta"
        assert info.index == 1

    def test_load_by_title_case_insensitive(self, collection_path):
        info = load_level_by_title(collection_path, "beta")
        assert info.title == "Beta"

    def test_load_by_title_not_found(self, collection_path):
        with pytest.raises(KeyError):
            load_level_by_title(collection_path, "Nonexistent")


# ---------------------------------------------------------------------------
# Title with solution suffix (Base-Levels format)
# ---------------------------------------------------------------------------


class TestTitleWithSolution:
    """Test that 'Level: name | solution' strips the solution part."""

    COLLECTION = (
        "Level: caleb-01 | RlUUdLLrdD\n"
        "\n"
        "   ###\n"
        "   #.#\n"
        "#### #\n"
        "#. BB###\n"
        "### &B.#\n"
        "  #B####\n"
        "  #.#\n"
        "  ###\n"
    )

    def test_title_strips_solution(self, tmp_path):
        path = tmp_path / "base.txt"
        path.write_text(self.COLLECTION)
        infos = load_collection_with_info(path)
        assert len(infos) == 1
        assert infos[0].title == "caleb-01"

    def test_game_is_playable(self, tmp_path):
        path = tmp_path / "base.txt"
        path.write_text(self.COLLECTION)
        infos = load_collection_with_info(path)
        game = infos[0].game
        assert not game.is_solved
        assert len(game.box_positions) > 0


# ---------------------------------------------------------------------------
# Real level database files
# ---------------------------------------------------------------------------


class TestRealLevelFiles:
    """Integration tests against actual level database files."""

    @pytest.mark.parametrize(
        "filename,expected_min",
        [
            ("Microban.txt", 155),
            ("Original & Extra.txt", 90),
            ("Pico Cosmos.txt", 20),
            ("Base-Levels.txt", 28),
            ("Tricky.txt", 9),
            ("Boxxle 1.txt", 100),
            ("Sasquatch.txt", 50),
        ],
    )
    def test_collection_loads_expected_count(self, filename, expected_min):
        games = load_level_collection(f"levels/{filename}")
        assert len(games) >= expected_min, (
            f"{filename}: expected >= {expected_min} levels, got {len(games)}"
        )

    def test_all_microban_levels_valid(self):
        infos = load_collection_with_info("levels/Microban.txt")
        for info in infos:
            assert info.game.width > 0
            assert info.game.height > 0
            assert len(info.game.box_positions) > 0
            assert info.game.title

    def test_base_levels_alternative_chars(self):
        infos = load_collection_with_info("levels/Base-Levels.txt")
        assert len(infos) >= 28
        for info in infos:
            assert len(info.game.box_positions) > 0

    def test_all_collections_load(self):
        """Every .txt file in levels/ should load at least 1 level."""
        import os

        levels_dir = "levels"
        for filename in os.listdir(levels_dir):
            if not filename.endswith(".txt"):
                continue
            path = os.path.join(levels_dir, filename)
            games = load_level_collection(path)
            assert len(games) > 0, f"{filename}: loaded 0 levels"
