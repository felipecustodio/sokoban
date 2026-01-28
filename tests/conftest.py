"""Pytest fixtures for sokoban-engine tests."""

import pytest

from sokoban_engine import Game
from sokoban_engine.board.parser import parse_level
from sokoban_engine.board.static_map import StaticMap
from sokoban_engine.state.game_state import GameState

# Standard test levels

SIMPLE_LEVEL = """
#####
#@$.#
#####
"""

MULTI_BOX_LEVEL = """
########
#  $.  #
#$$@.. #
#  $.  #
########
"""

SOLVABLE_LEVEL = """
######
#    #
# $@.#
#    #
######
"""

CORRIDOR_LEVEL = """
#######
#@ $ .#
#######
"""


@pytest.fixture
def simple_level_string() -> str:
    """Simple level with one box."""
    return SIMPLE_LEVEL


@pytest.fixture
def multi_box_level_string() -> str:
    """Level with multiple boxes."""
    return MULTI_BOX_LEVEL


@pytest.fixture
def simple_game() -> Game:
    """Game instance with simple level."""
    return Game(SIMPLE_LEVEL)


@pytest.fixture
def multi_box_game() -> Game:
    """Game instance with multi-box level."""
    return Game(MULTI_BOX_LEVEL)


@pytest.fixture
def solvable_game() -> Game:
    """Game instance with a solvable level."""
    return Game(SOLVABLE_LEVEL)


@pytest.fixture
def corridor_game() -> Game:
    """Game instance with corridor level."""
    return Game(CORRIDOR_LEVEL)


@pytest.fixture
def simple_parsed():
    """Parsed simple level."""
    return parse_level(SIMPLE_LEVEL)


@pytest.fixture
def simple_static_map(simple_parsed) -> StaticMap:
    """Static map for simple level."""
    return StaticMap.from_parsed_level(simple_parsed)


@pytest.fixture
def simple_initial_state(simple_parsed, simple_static_map) -> GameState:
    """Initial game state for simple level."""
    return GameState.from_parsed_level(simple_parsed, simple_static_map)
