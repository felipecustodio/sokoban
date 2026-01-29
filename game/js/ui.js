/**
 * HUD overlay: level selector, stats, win screen.
 */

import * as api from './api.js';

let collectionSelect, levelSelect, resetBtn;
let movesEl, pushesEl, boxesEl;
let winOverlay, nextLevelBtn;
let titleEl;

let onLevelLoad = null;

export function init(loadCallback) {
  onLevelLoad = loadCallback;

  collectionSelect = document.getElementById('collection-select');
  levelSelect = document.getElementById('level-select');
  resetBtn = document.getElementById('reset-btn');
  movesEl = document.getElementById('moves');
  pushesEl = document.getElementById('pushes');
  boxesEl = document.getElementById('boxes-on-goals');
  winOverlay = document.getElementById('win-overlay');
  nextLevelBtn = document.getElementById('next-level-btn');
  titleEl = document.getElementById('level-title');

  collectionSelect.addEventListener('change', onCollectionChange);
  levelSelect.addEventListener('change', onLevelChange);
  resetBtn.addEventListener('click', () => onLevelLoad?.('reset'));
  nextLevelBtn.addEventListener('click', onNextLevel);

  loadCollections();
}

async function loadCollections() {
  const data = await api.getCollections();
  collectionSelect.innerHTML = '';
  for (const name of data.collections) {
    const opt = document.createElement('option');
    opt.value = name;
    opt.textContent = name.replace('.txt', '');
    collectionSelect.appendChild(opt);
  }

  // Default to Microban if available
  const microban = data.collections.find(n => n === 'Microban.txt');
  if (microban) {
    collectionSelect.value = microban;
  }

  await onCollectionChange();
}

async function onCollectionChange() {
  const filename = collectionSelect.value;
  if (!filename) return;

  const data = await api.getLevels(filename);
  levelSelect.innerHTML = '';
  for (const level of data.levels) {
    const opt = document.createElement('option');
    opt.value = level.index;
    opt.textContent = `${level.index + 1}. ${level.title}`;
    levelSelect.appendChild(opt);
  }

  // Load first level
  if (data.levels.length > 0) {
    levelSelect.value = data.levels[0].index;
    await loadSelectedLevel();
  }
}

async function onLevelChange() {
  await loadSelectedLevel();
}

async function loadSelectedLevel() {
  const filename = collectionSelect.value;
  const index = parseInt(levelSelect.value, 10);
  if (!filename || isNaN(index)) return;

  const state = await api.loadLevel(filename, index);
  winOverlay.classList.add('hidden');
  onLevelLoad?.(state);
}

async function onNextLevel() {
  const currentIndex = parseInt(levelSelect.value, 10);
  const nextOption = levelSelect.querySelector(`option[value="${currentIndex + 1}"]`);
  if (nextOption) {
    levelSelect.value = currentIndex + 1;
    await loadSelectedLevel();
  }
}

export function updateStats(state) {
  titleEl.textContent = state.title || 'Sokoban';
  movesEl.textContent = state.move_count;
  pushesEl.textContent = state.push_count;

  const totalGoals = state.goals.length;
  boxesEl.textContent = `${state.boxes_on_goals}/${totalGoals}`;

  if (state.is_solved) {
    winOverlay.classList.remove('hidden');
  } else {
    winOverlay.classList.add('hidden');
  }
}
