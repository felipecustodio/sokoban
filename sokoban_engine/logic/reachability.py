"""Reachability computation using bitwise flood-fill.

This module computes which tiles the player can reach without pushing boxes,
and determines which pushes are legal based on player reachability.
"""

from sokoban_engine.board.static_map import StaticMap
from sokoban_engine.core.direction import Direction, opposite_direction
from sokoban_engine.core.types import Bitboard, TileIndex


def compute_reachability(
    static_map: StaticMap,
    player_index: TileIndex,
    box_bitboard: Bitboard,
) -> Bitboard:
    """Compute all tiles reachable by player using bitwise flood-fill.

    Uses iterative expansion in all directions until fixed point is reached.
    Very efficient for finding all tiles the player can walk to.

    Args:
        static_map: The static map with floor information.
        player_index: Current player tile index.
        box_bitboard: Bitboard of current box positions.

    Returns:
        Bitboard with 1s for all reachable tiles.
    """
    # Start with player position
    reachable: Bitboard = 1 << player_index

    # Passable mask: floor tiles that don't have boxes
    passable_mask = static_map.floor_mask & ~box_bitboard

    # Iteratively expand until no change
    while True:
        expanded = reachable

        # For each reachable tile, add its passable neighbors
        # We iterate through set bits and add neighbors
        expanded = _expand_reachable(reachable, static_map, passable_mask)

        # Fixed point reached
        if expanded == reachable:
            break
        reachable = expanded

    return reachable


def _expand_reachable(
    reachable: Bitboard,
    static_map: StaticMap,
    passable_mask: Bitboard,
) -> Bitboard:
    """Expand reachable set by one step in all directions.

    For each currently reachable tile, adds all passable neighbors.
    """
    expanded = reachable

    # Iterate through each reachable tile
    remaining = reachable
    while remaining:
        # Get index of lowest set bit
        tile_idx = (remaining & -remaining).bit_length() - 1
        remaining &= remaining - 1  # Clear lowest bit

        # Add all passable neighbors
        for direction in Direction:
            neighbor_idx = static_map.neighbors[tile_idx][direction]
            if neighbor_idx != -1 and (passable_mask & (1 << neighbor_idx)):
                expanded |= 1 << neighbor_idx

    return expanded


def get_legal_pushes(
    static_map: StaticMap,
    player_index: TileIndex,
    box_bitboard: Bitboard,
) -> list[tuple[TileIndex, Direction]]:
    """Find all legal push moves from current position.

    A push is legal if:
    1. The player can reach the tile opposite the push direction (behind the box)
    2. The tile in the push direction (where box will go) is empty (no wall, no box)

    Args:
        static_map: The static map.
        player_index: Current player tile index.
        box_bitboard: Bitboard of box positions.

    Returns:
        List of (box_tile_index, push_direction) pairs.
    """
    # First compute all reachable tiles
    reachable = compute_reachability(static_map, player_index, box_bitboard)

    pushes: list[tuple[TileIndex, Direction]] = []

    # Iterate through each box
    remaining = box_bitboard
    while remaining:
        # Get lowest set bit (first box)
        box_idx = (remaining & -remaining).bit_length() - 1
        remaining &= remaining - 1  # Clear lowest bit

        # Check each direction
        for direction in Direction:
            # Position player needs to be at (opposite side of box)
            opposite_dir = opposite_direction(direction)
            push_from_idx = static_map.neighbors[box_idx][opposite_dir]

            # Can't push from wall
            if push_from_idx == -1:
                continue

            # Can player reach push position?
            if not (reachable & (1 << push_from_idx)):
                continue

            # Is destination for box valid?
            push_to_idx = static_map.neighbors[box_idx][direction]

            # Wall at destination
            if push_to_idx == -1:
                continue

            # Box at destination
            if box_bitboard & (1 << push_to_idx):
                continue

            pushes.append((box_idx, direction))

    return pushes


def compute_reachability_fast(
    static_map: StaticMap,
    player_index: TileIndex,
    box_bitboard: Bitboard,
) -> Bitboard:
    """Alternative flood-fill using neighbor pre-computation.

    This version may be faster for sparse boards where most tiles
    have few reachable neighbors.
    """
    # Use BFS-style expansion with a work set
    reachable: Bitboard = 1 << player_index
    frontier: Bitboard = reachable
    passable_mask = static_map.floor_mask & ~box_bitboard

    while frontier:
        new_frontier: Bitboard = 0

        # Process all tiles in current frontier
        remaining = frontier
        while remaining:
            tile_idx = (remaining & -remaining).bit_length() - 1
            remaining &= remaining - 1

            # Check all neighbors
            for direction in Direction:
                neighbor_idx = static_map.neighbors[tile_idx][direction]
                if neighbor_idx == -1:
                    continue

                neighbor_bit = 1 << neighbor_idx

                # If passable and not already reachable, add to new frontier
                if (passable_mask & neighbor_bit) and not (reachable & neighbor_bit):
                    new_frontier |= neighbor_bit
                    reachable |= neighbor_bit

        frontier = new_frontier

    return reachable
