"""Transposition table for O(1) visited-state lookup.

A thin wrapper around a dict mapping Zobrist hashes to solver-defined data.
"""

from typing import Generic, TypeVar

T = TypeVar("T")


class TranspositionTable(Generic[T]):
    """Hash table mapping Zobrist hashes to arbitrary solver data.

    Generic over T so solvers can store whatever they need
    (depth, bound, move sequence, etc.).

    Uses Python dict for simplicity. Solvers can substitute
    fixed-size tables if memory is a concern.
    """

    __slots__ = ("_table",)

    def __init__(self) -> None:
        """Initialize an empty transposition table."""
        self._table: dict[int, T] = {}

    def __contains__(self, zobrist_hash: int) -> bool:
        """Check if a hash is in the table."""
        return zobrist_hash in self._table

    def __len__(self) -> int:
        """Number of entries in the table."""
        return len(self._table)

    def store(self, zobrist_hash: int, data: T) -> None:
        """Store data for a Zobrist hash.

        Args:
            zobrist_hash: The Zobrist hash key.
            data: Solver-defined data to store.
        """
        self._table[zobrist_hash] = data

    def lookup(self, zobrist_hash: int) -> T | None:
        """Look up data by Zobrist hash.

        Args:
            zobrist_hash: The Zobrist hash key.

        Returns:
            Stored data, or None if not found.
        """
        return self._table.get(zobrist_hash)

    def clear(self) -> None:
        """Remove all entries."""
        self._table.clear()
