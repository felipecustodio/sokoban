/**
 * Client-side BFS pathfinding for drag-to-walk.
 * Builds a walkability grid from game state and finds paths avoiding walls and boxes.
 * Supports push-aware pathfinding where paths can push boxes.
 */

// Direction constants matching sokoban_engine.Direction
const UP = 0;
const DOWN = 1;
const LEFT = 2;
const RIGHT = 3;

const DELTAS = [
  [-1, 0], // UP
  [1, 0],  // DOWN
  [0, -1], // LEFT
  [0, 1],  // RIGHT
];

const MAX_STATES = 50000;

/**
 * Build a 2D boolean grid where true = walkable (floor, not occupied by box).
 */
export function buildWalkabilityGrid(state) {
  const { width, height, walls, boxes } = state;
  // Start all cells as false (unwalkable)
  const grid = Array.from({ length: height }, () => Array(width).fill(false));

  // Mark floor tiles as walkable
  for (const [r, c] of state.floors) {
    grid[r][c] = true;
  }

  // Block box positions
  for (const [r, c] of boxes) {
    grid[r][c] = false;
  }

  return grid;
}

/**
 * BFS from `from` to `to` on a walkability grid.
 * Returns { tiles, directions, cost } or null if no path.
 */
export function findPath(from, to, grid) {
  const height = grid.length;
  const width = grid[0].length;

  if (
    from.row < 0 || from.row >= height || from.col < 0 || from.col >= width ||
    to.row < 0 || to.row >= height || to.col < 0 || to.col >= width
  ) {
    return null;
  }

  if (!grid[from.row][from.col] || !grid[to.row][to.col]) {
    return null;
  }

  if (from.row === to.row && from.col === to.col) {
    return { tiles: [{ row: from.row, col: from.col }], directions: [], cost: 0 };
  }

  const key = (r, c) => r * width + c;
  const visited = new Set();
  visited.add(key(from.row, from.col));

  // parent maps key -> { row, col, dir } where dir is the direction taken to reach this cell
  const parent = new Map();
  const queue = [{ row: from.row, col: from.col }];

  while (queue.length > 0) {
    const current = queue.shift();

    for (let d = 0; d < 4; d++) {
      const nr = current.row + DELTAS[d][0];
      const nc = current.col + DELTAS[d][1];

      if (nr < 0 || nr >= height || nc < 0 || nc >= width) continue;
      if (!grid[nr][nc]) continue;

      const k = key(nr, nc);
      if (visited.has(k)) continue;

      visited.add(k);
      parent.set(k, { row: current.row, col: current.col, dir: d });

      if (nr === to.row && nc === to.col) {
        return reconstructPath(from, to, parent, width);
      }

      queue.push({ row: nr, col: nc });
    }
  }

  return null;
}

function reconstructPath(from, to, parent, width) {
  const key = (r, c) => r * width + c;
  const tiles = [];
  const directions = [];

  let current = { row: to.row, col: to.col };
  while (current.row !== from.row || current.col !== from.col) {
    tiles.unshift(current);
    const p = parent.get(key(current.row, current.col));
    directions.unshift(p.dir);
    current = { row: p.row, col: p.col };
  }
  tiles.unshift({ row: from.row, col: from.col });

  return { tiles, directions, cost: directions.length };
}

/**
 * Find up to maxPaths alternative paths using simplified Yen's algorithm.
 * Blocks intermediate tiles of the primary path to force detours.
 */
export function findAlternativePaths(from, to, grid, maxPaths = 3) {
  const primary = findPath(from, to, grid);
  if (!primary) return [];

  const paths = [primary];

  // Try blocking each intermediate tile of the primary path
  for (let i = 1; i < primary.tiles.length - 1; i++) {
    if (paths.length >= maxPaths) break;

    const tile = primary.tiles[i];
    const saved = grid[tile.row][tile.col];
    grid[tile.row][tile.col] = false;

    const alt = findPath(from, to, grid);
    grid[tile.row][tile.col] = saved;

    if (alt && !isDuplicate(alt, paths)) {
      paths.push(alt);
    }
  }

  return paths;
}

function isDuplicate(path, existing) {
  const sig = pathSignature(path);
  return existing.some((p) => pathSignature(p) === sig);
}

function pathSignature(path) {
  return path.directions.join(',');
}

/**
 * BFS where state = (playerPos, boxPositions).
 * Can push boxes if the cell beyond the box is free.
 * Returns { tiles, directions, cost, pushes, pushStepIndices } or null.
 */
export function findPathWithPushes(from, to, state) {
  const { width, height } = state;
  const floorSet = new Set();
  for (const [r, c] of state.floors) {
    floorSet.add(r * width + c);
  }

  const isFloor = (r, c) =>
    r >= 0 && r < height && c >= 0 && c < width && floorSet.has(r * width + c);

  // Initial box positions as sorted flat indices
  const initialBoxes = state.boxes.map(([r, c]) => r * width + c).sort((a, b) => a - b);

  if (!isFloor(from.row, from.col) || !isFloor(to.row, to.col)) return null;

  const startPlayerIdx = from.row * width + from.col;
  const targetIdx = to.row * width + to.col;

  if (startPlayerIdx === targetIdx) {
    return { tiles: [{ row: from.row, col: from.col }], directions: [], cost: 0, pushes: [], pushStepIndices: new Set() };
  }

  const stateKey = (playerIdx, boxes) => playerIdx + '|' + boxes.join(',');

  const visited = new Set();
  const startKey = stateKey(startPlayerIdx, initialBoxes);
  visited.add(startKey);

  // Queue entries: { playerIdx, boxes, path: [{ playerIdx, dir, push }] }
  const queue = [{ playerIdx: startPlayerIdx, boxes: initialBoxes, path: [] }];
  let statesExplored = 0;

  while (queue.length > 0) {
    if (statesExplored++ >= MAX_STATES) return null;

    const current = queue.shift();

    const pr = Math.floor(current.playerIdx / width);
    const pc = current.playerIdx % width;
    const boxSet = new Set(current.boxes);

    for (let d = 0; d < 4; d++) {
      const nr = pr + DELTAS[d][0];
      const nc = pc + DELTAS[d][1];

      if (!isFloor(nr, nc)) continue;

      const neighborIdx = nr * width + nc;
      let newBoxes = current.boxes;
      let push = null;

      if (boxSet.has(neighborIdx)) {
        // Box at neighbor — try to push
        const beyondR = nr + DELTAS[d][0];
        const beyondC = nc + DELTAS[d][1];
        if (!isFloor(beyondR, beyondC)) continue;

        const beyondIdx = beyondR * width + beyondC;
        if (boxSet.has(beyondIdx)) continue; // another box blocks

        // Create new box array with this box moved
        newBoxes = current.boxes.map((b) => (b === neighborIdx ? beyondIdx : b)).sort((a, b) => a - b);
        push = {
          fromRow: nr, fromCol: nc,
          toRow: beyondR, toCol: beyondC,
          direction: d,
        };
      }

      const sk = stateKey(neighborIdx, newBoxes);
      if (visited.has(sk)) continue;
      visited.add(sk);

      const newPath = [...current.path, { playerIdx: neighborIdx, dir: d, push }];

      if (neighborIdx === targetIdx) {
        return reconstructPushPath(from, newPath, width);
      }

      queue.push({ playerIdx: neighborIdx, boxes: newBoxes, path: newPath });
    }
  }

  return null;
}

function reconstructPushPath(from, pathSteps, width) {
  const tiles = [{ row: from.row, col: from.col }];
  const directions = [];
  const pushes = [];
  const pushStepIndices = new Set();

  for (let i = 0; i < pathSteps.length; i++) {
    const step = pathSteps[i];
    const r = Math.floor(step.playerIdx / width);
    const c = step.playerIdx % width;
    tiles.push({ row: r, col: c });
    directions.push(step.dir);
    if (step.push) {
      pushes.push({ ...step.push, stepIndex: i + 1 }); // +1 because tiles[0] is start
      pushStepIndices.add(i + 1);
    }
  }

  return { tiles, directions, cost: directions.length, pushes, pushStepIndices };
}

/**
 * Find up to maxPaths alternative paths, supporting box pushes.
 */
export function findAlternativePathsWithPushes(from, to, state, maxPaths = 3) {
  const primary = findPathWithPushes(from, to, state);
  if (!primary) return [];

  const paths = [primary];

  if (primary.pushes.length === 0) {
    // No pushes — use the faster walkability-grid approach for alternatives
    const grid = buildWalkabilityGrid(state);
    for (let i = 1; i < primary.tiles.length - 1; i++) {
      if (paths.length >= maxPaths) break;
      const tile = primary.tiles[i];
      const saved = grid[tile.row][tile.col];
      grid[tile.row][tile.col] = false;
      const alt = findPath(from, to, grid);
      grid[tile.row][tile.col] = saved;
      if (alt) {
        // Augment with empty push fields
        alt.pushes = [];
        alt.pushStepIndices = new Set();
        if (!isDuplicate(alt, paths)) paths.push(alt);
      }
    }
  } else {
    // Has pushes — generate alternatives by adding virtual walls and re-running push BFS
    for (let i = 1; i < primary.tiles.length - 1; i++) {
      if (paths.length >= maxPaths) break;
      const tile = primary.tiles[i];
      // Create modified state with this tile removed from floors
      const modifiedState = {
        ...state,
        floors: state.floors.filter(([r, c]) => !(r === tile.row && c === tile.col)),
      };
      const alt = findPathWithPushes(from, to, modifiedState);
      if (alt && !isDuplicate(alt, paths)) {
        paths.push(alt);
      }
    }
  }

  return paths;
}

/**
 * Convert screen coordinates to grid (row, col).
 */
export function screenToGrid(screenX, screenY, camera, canvas) {
  const rect = canvas.getBoundingClientRect();
  const ndcX = ((screenX - rect.left) / rect.width) * 2 - 1;
  const ndcY = -((screenY - rect.top) / rect.height) * 2 + 1;

  const worldX = camera.left + (ndcX + 1) * 0.5 * (camera.right - camera.left);
  const worldY = camera.bottom + (ndcY + 1) * 0.5 * (camera.top - camera.bottom);

  // Inverse of gridToWorld: x = col, y = -row
  const col = Math.round(worldX);
  const row = Math.round(-worldY);

  return { row, col };
}
