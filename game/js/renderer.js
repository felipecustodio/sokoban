/**
 * Three.js scene setup and tile rendering with colored shapes.
 */

import * as THREE from 'three';

let scene, camera, renderer;
let staticGroup, dynamicGroup;

const TILE_WORLD_SIZE = 1;

export function init(canvas) {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0d0d14);

  camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 100);
  camera.position.set(0, 0, 10);

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);

  staticGroup = new THREE.Group();
  dynamicGroup = new THREE.Group();
  scene.add(staticGroup);
  scene.add(dynamicGroup);

  window.addEventListener('resize', onResize);
  onResize();
}

export function getScene() {
  return scene;
}

export function getCamera() {
  return camera;
}

function onResize() {
  const w = window.innerWidth;
  const h = window.innerHeight;
  renderer.setSize(w, h);
}

function fitCamera(width, height) {
  const padding = 0.5;
  const gameW = width + padding * 2;
  const gameH = height + padding * 2;
  const aspect = window.innerWidth / window.innerHeight;

  let viewW, viewH;
  if (gameW / gameH > aspect) {
    viewW = gameW;
    viewH = gameW / aspect;
  } else {
    viewH = gameH;
    viewW = gameH * aspect;
  }

  const cx = width / 2 - 0.5;
  const cy = -(height / 2 - 0.5);

  camera.left = cx - viewW / 2;
  camera.right = cx + viewW / 2;
  camera.top = cy + viewH / 2;
  camera.bottom = cy - viewH / 2;
  camera.updateProjectionMatrix();
}

function gridToWorld(row, col) {
  return { x: col, y: -row };
}

function createFloorMesh(row, col) {
  const geo = new THREE.PlaneGeometry(0.92, 0.92);
  const mat = new THREE.MeshBasicMaterial({ color: 0x1e1e2e });
  const mesh = new THREE.Mesh(geo, mat);
  const pos = gridToWorld(row, col);
  mesh.position.set(pos.x, pos.y, 0);
  return mesh;
}

function createWallMesh(row, col) {
  const geo = new THREE.PlaneGeometry(0.96, 0.96);
  const mat = new THREE.MeshBasicMaterial({ color: 0x3d3d50 });
  const mesh = new THREE.Mesh(geo, mat);
  const pos = gridToWorld(row, col);
  mesh.position.set(pos.x, pos.y, 0);
  return mesh;
}

function createGoalMesh(row, col) {
  const geo = new THREE.CircleGeometry(0.15, 20);
  const mat = new THREE.MeshBasicMaterial({ color: 0xff6b6b });
  const mesh = new THREE.Mesh(geo, mat);
  const pos = gridToWorld(row, col);
  mesh.position.set(pos.x, pos.y, 0.1);
  return mesh;
}

function createBoxMesh(row, col, onGoal) {
  const geo = new THREE.PlaneGeometry(0.78, 0.78);
  const color = onGoal ? 0x4ecdc4 : 0xf0a030;
  const mat = new THREE.MeshBasicMaterial({ color });
  const mesh = new THREE.Mesh(geo, mat);
  const pos = gridToWorld(row, col);
  mesh.position.set(pos.x, pos.y, 0.2);
  return mesh;
}

function createPlayerMesh(row, col) {
  const geo = new THREE.CircleGeometry(0.35, 24);
  const mat = new THREE.MeshBasicMaterial({ color: 0x4da6ff });
  const mesh = new THREE.Mesh(geo, mat);
  const pos = gridToWorld(row, col);
  mesh.position.set(pos.x, pos.y, 0.3);
  return mesh;
}

export function renderState(state) {
  // Clear previous
  staticGroup.clear();
  dynamicGroup.clear();

  const { width, height, walls, floors, player, boxes, goals } = state;

  const goalSet = new Set(goals.map(([r, c]) => `${r},${c}`));

  // Render floors
  for (const [r, c] of floors) {
    staticGroup.add(createFloorMesh(r, c));
  }

  // Render walls
  for (const [r, c] of walls) {
    staticGroup.add(createWallMesh(r, c));
  }

  // Render goals
  for (const [r, c] of goals) {
    staticGroup.add(createGoalMesh(r, c));
  }

  // Render boxes
  for (const [r, c] of boxes) {
    const isOnGoal = goalSet.has(`${r},${c}`);
    dynamicGroup.add(createBoxMesh(r, c, isOnGoal));
  }

  // Render player
  dynamicGroup.add(createPlayerMesh(player[0], player[1]));

  fitCamera(width, height);
  render();
}

export function render() {
  renderer.render(scene, camera);
}
