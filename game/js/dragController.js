/**
 * Drag-to-walk interaction state machine.
 * Handles mousedown/mousemove/mouseup to plan and execute walking paths.
 */

import {
  findAlternativePathsWithPushes,
  screenToGrid,
} from './pathPlanner.js';
import * as pathRenderer from './pathRenderer.js';
import { executePath } from './pathExecutor.js';

const DEBOUNCE_MS = 50;

let state = 'idle'; // 'idle' | 'dragging' | 'executing'
let gameState = null;
let paths = [];
let selectedPathIndex = 0;
let lastTile = null;
let debounceTimer = null;

// Externally provided references
let camera = null;
let canvas = null;
let apiRef = null;
let onStateUpdate = null;
let renderFn = null;

/**
 * Initialize with references to camera, canvas, api module, state callback, and render function.
 */
export function init({ camera: cam, canvas: cvs, api, onUpdate, render }) {
  camera = cam;
  canvas = cvs;
  apiRef = api;
  onStateUpdate = onUpdate;
  renderFn = render;

  canvas.addEventListener('mousedown', onMouseDown);
  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
}

/**
 * Called whenever game state changes (after moves, undo, redo, level load).
 */
export function updateGameState(newState) {
  gameState = newState;
}

/**
 * Cancel any active drag (e.g. when arrow key pressed, or Escape).
 */
export function cancel() {
  if (state === 'dragging') {
    pathRenderer.clearPaths();
    renderFn?.();
    state = 'idle';
    paths = [];
    selectedPathIndex = 0;
    lastTile = null;
  }
}

/**
 * Cycle to next alternative path (Tab key).
 */
export function cyclePathSelection() {
  if (state !== 'dragging' || paths.length <= 1) return;
  selectedPathIndex = (selectedPathIndex + 1) % paths.length;
  pathRenderer.renderPaths(paths, selectedPathIndex);
  renderFn?.();
}

/**
 * Whether the controller is currently busy (dragging or executing).
 */
export function isBusy() {
  return state !== 'idle';
}

function onMouseDown(e) {
  if (state !== 'idle' || !gameState) return;
  if (gameState.is_solved) return;

  // Only handle left mouse button
  if (e.button !== 0) return;

  const tile = screenToGrid(e.clientX, e.clientY, camera, canvas);

  // Check tile is within bounds and walkable
  if (
    tile.row < 0 || tile.row >= gameState.height ||
    tile.col < 0 || tile.col >= gameState.width
  ) {
    return;
  }

  const playerTile = { row: gameState.player[0], col: gameState.player[1] };

  // Don't path to the player's own tile
  if (tile.row === playerTile.row && tile.col === playerTile.col) return;

  state = 'dragging';
  lastTile = tile;
  paths = findAlternativePathsWithPushes(playerTile, tile, gameState, 3);
  selectedPathIndex = 0;

  if (paths.length > 0) {
    pathRenderer.renderPaths(paths, selectedPathIndex);
  } else {
    pathRenderer.clearPaths();
  }
  renderFn?.();
}

function onMouseMove(e) {
  if (state !== 'dragging') return;

  // Debounce
  if (debounceTimer) return;
  debounceTimer = setTimeout(() => { debounceTimer = null; }, DEBOUNCE_MS);

  const tile = screenToGrid(e.clientX, e.clientY, camera, canvas);

  // Skip if same tile
  if (lastTile && tile.row === lastTile.row && tile.col === lastTile.col) return;
  lastTile = tile;

  // Clamp to grid bounds
  if (
    tile.row < 0 || tile.row >= gameState.height ||
    tile.col < 0 || tile.col >= gameState.width
  ) {
    pathRenderer.clearPaths();
    renderFn?.();
    paths = [];
    return;
  }

  const playerTile = { row: gameState.player[0], col: gameState.player[1] };
  paths = findAlternativePathsWithPushes(playerTile, tile, gameState, 3);
  selectedPathIndex = 0;

  if (paths.length > 0) {
    pathRenderer.renderPaths(paths, selectedPathIndex);
  } else {
    pathRenderer.clearPaths();
  }
  renderFn?.();
}

async function onMouseUp(e) {
  if (state !== 'dragging') return;

  if (paths.length === 0 || !paths[selectedPathIndex]) {
    cancel();
    return;
  }

  // Only execute if path has actual moves
  const selected = paths[selectedPathIndex];
  if (selected.directions.length === 0) {
    cancel();
    return;
  }

  state = 'executing';
  pathRenderer.clearPaths();
  renderFn?.();

  try {
    const newState = await executePath(selected, apiRef);
    onStateUpdate?.(newState);
  } catch (err) {
    console.error('Path execution failed:', err);
  }

  state = 'idle';
  paths = [];
  selectedPathIndex = 0;
  lastTile = null;
}
