/**
 * Executes a planned path by sending directions to the server.
 */

/**
 * Execute a path in batch mode (instant teleport).
 * @param {Object} path - Path object with { directions: number[] }
 * @param {Object} api - API module with movePath function
 * @returns {Promise<Object>} Final game state
 */
export async function executePath(path, api) {
  return api.movePath(path.directions);
}
