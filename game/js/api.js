/**
 * API client for the Sokoban game server.
 */

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== null) {
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export function getCollections() {
  return request('GET', '/api/collections');
}

export function getLevels(filename) {
  return request('GET', `/api/collections/${encodeURIComponent(filename)}/levels`);
}

export function loadLevel(filename, index) {
  return request('POST', '/api/load', { filename, index });
}

export function move(direction) {
  return request('POST', '/api/move', { direction });
}

export function undo() {
  return request('POST', '/api/undo');
}

export function redo() {
  return request('POST', '/api/redo');
}

export function reset() {
  return request('POST', '/api/reset');
}

export function movePath(directions) {
  return request('POST', '/api/move-path', { directions });
}
