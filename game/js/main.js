/**
 * Entry point: init Three.js, bind inputs, connect to API.
 */

import * as renderer from './renderer.js';
import * as input from './input.js';
import * as ui from './ui.js';
import * as api from './api.js';
import * as pathRenderer from './pathRenderer.js';
import * as dragController from './dragController.js';

let currentState = null;
let requestInFlight = false;

function updateView(state) {
  currentState = state;
  renderer.renderState(state);
  ui.updateStats(state);
  dragController.updateGameState(state);
}

async function handleMove(direction) {
  // Cancel any active drag when arrow key is pressed
  dragController.cancel();

  if (!currentState || requestInFlight || currentState.is_solved) return;
  if (dragController.isBusy()) return;
  requestInFlight = true;
  try {
    const state = await api.move(direction);
    updateView(state);
  } catch (e) {
    console.error('Move failed:', e);
  } finally {
    requestInFlight = false;
  }
}

async function handleUndo() {
  if (!currentState || requestInFlight || !currentState.can_undo) return;
  if (dragController.isBusy()) return;
  requestInFlight = true;
  try {
    const state = await api.undo();
    updateView(state);
  } catch (e) {
    console.error('Undo failed:', e);
  } finally {
    requestInFlight = false;
  }
}

async function handleRedo() {
  if (!currentState || requestInFlight || !currentState.can_redo) return;
  if (dragController.isBusy()) return;
  requestInFlight = true;
  try {
    const state = await api.redo();
    updateView(state);
  } catch (e) {
    console.error('Redo failed:', e);
  } finally {
    requestInFlight = false;
  }
}

async function handleReset() {
  if (!currentState || requestInFlight) return;
  if (dragController.isBusy()) return;
  requestInFlight = true;
  try {
    const state = await api.reset();
    updateView(state);
  } catch (e) {
    console.error('Reset failed:', e);
  } finally {
    requestInFlight = false;
  }
}

function onLevelLoad(stateOrCommand) {
  if (stateOrCommand === 'reset') {
    handleReset();
    return;
  }
  updateView(stateOrCommand);
}

function start() {
  const canvas = document.getElementById('game-canvas');
  renderer.init(canvas);

  // Initialize path overlay renderer
  pathRenderer.init(renderer.getScene());

  // Initialize drag controller
  dragController.init({
    camera: renderer.getCamera(),
    canvas,
    api,
    onUpdate: updateView,
    render: renderer.render,
  });

  input.bind({
    move: handleMove,
    undo: handleUndo,
    redo: handleRedo,
    reset: handleReset,
    tab: () => dragController.cyclePathSelection(),
    escape: () => dragController.cancel(),
  });

  ui.init(onLevelLoad);
}

start();
