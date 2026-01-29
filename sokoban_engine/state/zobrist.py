"""Zobrist hashing for efficient state deduplication.

Provides O(1) incremental hash updates on moves/undos,
enabling fast visited-state lookup in solvers.
"""

import random

from sokoban_engine.core.types import TileIndex


class ZobristHasher:
    """Zobrist hash computation for Sokoban game states.

    Initialized per-level from the number of floor tiles.
    Uses XOR-based hashing for O(1) incremental updates.

    The hash for a state is:
        player_keys[player_index] XOR box_keys[b1] XOR box_keys[b2] XOR ...
    """

    __slots__ = ("_player_keys", "_box_keys")

    def __init__(self, num_floor_tiles: int, seed: int = 0) -> None:
        """Initialize Zobrist keys for a level.

        Args:
            num_floor_tiles: Number of passable floor tiles in the level.
            seed: RNG seed for deterministic, reproducible key generation.
        """
        rng = random.Random(seed)
        max_val = (1 << 64) - 1
        self._player_keys: tuple[int, ...] = tuple(
            rng.randint(0, max_val) for _ in range(num_floor_tiles)
        )
        self._box_keys: tuple[int, ...] = tuple(
            rng.randint(0, max_val) for _ in range(num_floor_tiles)
        )

    def hash_state(
        self,
        player_index: TileIndex,
        box_indices: tuple[TileIndex, ...],
    ) -> int:
        """Compute full Zobrist hash for a state.

        Args:
            player_index: Tile index of the player.
            box_indices: Sorted tuple of tile indices for boxes.

        Returns:
            64-bit Zobrist hash.
        """
        h = self._player_keys[player_index]
        for b in box_indices:
            h ^= self._box_keys[b]
        return h

    def update_walk(
        self,
        current_hash: int,
        old_player: TileIndex,
        new_player: TileIndex,
    ) -> int:
        """Incrementally update hash after a walk (no box pushed).

        Args:
            current_hash: Hash before the move.
            old_player: Player's previous tile index.
            new_player: Player's new tile index.

        Returns:
            Updated hash.
        """
        return current_hash ^ self._player_keys[old_player] ^ self._player_keys[new_player]

    def update_push(
        self,
        current_hash: int,
        old_player: TileIndex,
        new_player: TileIndex,
        box_from: TileIndex,
        box_to: TileIndex,
    ) -> int:
        """Incrementally update hash after a push.

        Args:
            current_hash: Hash before the move.
            old_player: Player's previous tile index.
            new_player: Player's new tile index (box's old position).
            box_from: Box's previous tile index.
            box_to: Box's new tile index.

        Returns:
            Updated hash.
        """
        return (
            current_hash
            ^ self._player_keys[old_player]
            ^ self._player_keys[new_player]
            ^ self._box_keys[box_from]
            ^ self._box_keys[box_to]
        )
