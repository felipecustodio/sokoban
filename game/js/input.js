/**
 * Keyboard handler for Sokoban game.
 * Arrow keys + WASD for movement, z/Ctrl+Z for undo, y/Ctrl+Y for redo, r for reset.
 * Tab to cycle path alternatives, Escape to cancel drag.
 */

// Direction constants matching sokoban_engine.Direction
const UP = 0;
const DOWN = 1;
const LEFT = 2;
const RIGHT = 3;

let onMove = null;
let onUndo = null;
let onRedo = null;
let onReset = null;
let onTab = null;
let onEscape = null;

export function bind({ move, undo, redo, reset, tab, escape }) {
  onMove = move;
  onUndo = undo;
  onRedo = redo;
  onReset = reset;
  onTab = tab || null;
  onEscape = escape || null;

  document.addEventListener('keydown', handleKey);
}

export function unbind() {
  document.removeEventListener('keydown', handleKey);
}

function handleKey(e) {
  // Ignore if typing in an input/select
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

  switch (e.key) {
    case 'ArrowUp':
    case 'w':
    case 'W':
      e.preventDefault();
      onMove?.(UP);
      break;
    case 'ArrowDown':
    case 's':
    case 'S':
      e.preventDefault();
      onMove?.(DOWN);
      break;
    case 'ArrowLeft':
    case 'a':
    case 'A':
      e.preventDefault();
      onMove?.(LEFT);
      break;
    case 'ArrowRight':
    case 'd':
    case 'D':
      e.preventDefault();
      onMove?.(RIGHT);
      break;
    case 'z':
    case 'Z':
      e.preventDefault();
      onUndo?.();
      break;
    case 'y':
    case 'Y':
      e.preventDefault();
      onRedo?.();
      break;
    case 'r':
    case 'R':
      e.preventDefault();
      onReset?.();
      break;
    case 'Tab':
      e.preventDefault();
      onTab?.();
      break;
    case 'Escape':
      e.preventDefault();
      onEscape?.();
      break;
  }
}
