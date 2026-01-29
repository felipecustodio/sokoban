/**
 * Three.js overlay for rendering path previews during drag interaction.
 * Shows primary path (highlighted) and alternative paths (dimmed).
 */

import * as THREE from 'three';

let overlayGroup = null;

const PRIMARY_COLOR = 0x4da6ff;
const ALT_COLOR = 0x888888;
const PRIMARY_OPACITY = 0.8;
const ALT_OPACITY = 0.3;
const PRIMARY_Z = 0.15;
const ALT_Z = 0.12;
const TILE_SIZE = 0.85;

// Push/ghost box constants
const PUSH_TILE_COLOR = 0xf0a030;
const PUSH_TILE_OPACITY = 0.5;
const GHOST_BOX_COLOR = 0xf0a030;
const GHOST_BOX_OPACITY = 0.35;
const GHOST_BOX_Z = 0.18;
const GHOST_BOX_SIZE = 0.78;

// Arrow geometry constants
const ARROW_SIZE = 0.18;

// Direction deltas for arrow rotation: UP=0, DOWN=1, LEFT=2, RIGHT=3
const DIR_ANGLES = [
  Math.PI / 2,   // UP
  -Math.PI / 2,  // DOWN
  Math.PI,       // LEFT
  0,             // RIGHT
];

/**
 * Initialize the overlay group and add it to the scene.
 */
export function init(scene) {
  overlayGroup = new THREE.Group();
  scene.add(overlayGroup);
}

function gridToWorld(row, col) {
  return { x: col, y: -row };
}

function createArrowShape() {
  const s = ARROW_SIZE;
  const shape = new THREE.Shape();
  shape.moveTo(s, 0);
  shape.lineTo(-s * 0.5, s * 0.6);
  shape.lineTo(-s * 0.5, -s * 0.6);
  shape.closePath();
  return shape;
}

/**
 * Render path overlays. paths is an array from findAlternativePaths.
 * selectedIndex indicates which path is the primary (highlighted) one.
 */
export function renderPaths(paths, selectedIndex) {
  clearPaths();

  for (let i = 0; i < paths.length; i++) {
    const path = paths[i];
    const isPrimary = i === selectedIndex;
    const color = isPrimary ? PRIMARY_COLOR : ALT_COLOR;
    const opacity = isPrimary ? PRIMARY_OPACITY : ALT_OPACITY;
    const z = isPrimary ? PRIMARY_Z : ALT_Z;

    // Tile highlights
    const pushSteps = isPrimary && path.pushStepIndices ? path.pushStepIndices : null;
    for (let t = 0; t < path.tiles.length; t++) {
      const tile = path.tiles[t];
      const isPushTile = pushSteps && pushSteps.has(t);
      const tileColor = isPushTile ? PUSH_TILE_COLOR : color;
      const tileOpacity = isPushTile ? PUSH_TILE_OPACITY : opacity;
      const geo = new THREE.PlaneGeometry(TILE_SIZE, TILE_SIZE);
      const mat = new THREE.MeshBasicMaterial({
        color: tileColor,
        transparent: true,
        opacity: tileOpacity,
        depthTest: false,
      });
      const mesh = new THREE.Mesh(geo, mat);
      const pos = gridToWorld(tile.row, tile.col);
      mesh.position.set(pos.x, pos.y, z);
      overlayGroup.add(mesh);
    }

    // Direction arrows on primary path
    if (isPrimary && path.tiles.length > 1) {
      const arrowShape = createArrowShape();
      const arrowGeo = new THREE.ShapeGeometry(arrowShape);

      for (let j = 0; j < path.tiles.length - 1; j++) {
        const from = path.tiles[j];
        const to = path.tiles[j + 1];
        const fromPos = gridToWorld(from.row, from.col);
        const toPos = gridToWorld(to.row, to.col);

        const midX = (fromPos.x + toPos.x) / 2;
        const midY = (fromPos.y + toPos.y) / 2;

        const dir = path.directions[j];
        const mat = new THREE.MeshBasicMaterial({
          color: 0xffffff,
          transparent: true,
          opacity: 0.9,
          depthTest: false,
        });
        const mesh = new THREE.Mesh(arrowGeo, mat);
        mesh.position.set(midX, midY, z + 0.01);
        mesh.rotation.z = DIR_ANGLES[dir];
        overlayGroup.add(mesh);
      }
    }

    // Ghost box previews for push paths
    if (isPrimary && path.pushes && path.pushes.length > 0) {
      renderGhostBoxes(path.pushes, z);
    }
  }
}

/**
 * Collapse multi-push chains into final resting positions per distinct box.
 * Returns a Map of "fromRow,fromCol" (original position) -> { row, col, direction }.
 */
function computeBoxFinalPositions(pushes) {
  // Track box movements: key by current position
  const positionMap = new Map(); // "r,c" -> { origKey, row, col, direction }

  for (const push of pushes) {
    const fromKey = push.fromRow + ',' + push.fromCol;
    const toKey = push.toRow + ',' + push.toCol;

    // Check if this "from" matches a previous push's "to" (same box moved again)
    let origKey = fromKey;
    if (positionMap.has(fromKey)) {
      const prev = positionMap.get(fromKey);
      origKey = prev.origKey;
      positionMap.delete(fromKey);
    }

    positionMap.set(toKey, {
      origKey,
      row: push.toRow,
      col: push.toCol,
      direction: push.direction,
    });
  }

  return positionMap;
}

/**
 * Render semi-transparent ghost boxes at push destinations.
 */
function renderGhostBoxes(pushes, z) {
  const finals = computeBoxFinalPositions(pushes);

  const arrowShape = createArrowShape();
  const arrowGeo = new THREE.ShapeGeometry(arrowShape);

  for (const [, box] of finals) {
    const pos = gridToWorld(box.row, box.col);

    // Ghost box plane
    const geo = new THREE.PlaneGeometry(GHOST_BOX_SIZE, GHOST_BOX_SIZE);
    const mat = new THREE.MeshBasicMaterial({
      color: GHOST_BOX_COLOR,
      transparent: true,
      opacity: GHOST_BOX_OPACITY,
      depthTest: false,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(pos.x, pos.y, GHOST_BOX_Z);
    overlayGroup.add(mesh);

    // Outline
    const edges = new THREE.EdgesGeometry(geo);
    const lineMat = new THREE.LineBasicMaterial({
      color: GHOST_BOX_COLOR,
      transparent: true,
      opacity: 0.6,
    });
    const outline = new THREE.LineSegments(edges, lineMat);
    outline.position.set(pos.x, pos.y, GHOST_BOX_Z + 0.005);
    overlayGroup.add(outline);

    // Direction arrow on ghost box
    const arrowMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.7,
      depthTest: false,
    });
    const arrowMesh = new THREE.Mesh(arrowGeo, arrowMat);
    arrowMesh.position.set(pos.x, pos.y, GHOST_BOX_Z + 0.01);
    arrowMesh.rotation.z = DIR_ANGLES[box.direction];
    overlayGroup.add(arrowMesh);
  }
}

/**
 * Remove all path overlay meshes and dispose their resources.
 */
export function clearPaths() {
  if (!overlayGroup) return;
  while (overlayGroup.children.length > 0) {
    const child = overlayGroup.children[0];
    overlayGroup.remove(child);
    if (child.geometry) child.geometry.dispose();
    if (child.material) child.material.dispose();
  }
}
