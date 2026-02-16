/**
 * Pure functions computing feature eligibility at summit positions.
 * Direct port of the Python eligibility logic.
 */

export function isTile(tiles: boolean[][], r: number, c: number): boolean {
  const rows = tiles.length
  const cols = tiles[0]?.length ?? 0
  if (r >= 0 && r < rows && c >= 0 && c < cols) return tiles[r][c]
  return false
}

/**
 * Summit (i,j) is eligible for a connector iff its 4 neighbors form
 * a pair of tiles sharing an edge (horizontal or vertical split).
 */
export function computeEligibleConnectorPositions(
  tiles: boolean[][],
): boolean[][] {
  const rows = tiles.length
  const cols = tiles[0]?.length ?? 0
  const result: boolean[][] = []
  for (let i = 0; i <= rows; i++) {
    const row: boolean[] = []
    for (let j = 0; j <= cols; j++) {
      const tl = isTile(tiles, i - 1, j - 1)
      const tr = isTile(tiles, i - 1, j)
      const bl = isTile(tiles, i, j - 1)
      const br = isTile(tiles, i, j)
      const eligible =
        (tl === tr && bl === br && tl !== bl) ||
        (tl === bl && tr === br && tl !== tr)
      row.push(eligible)
    }
    result.push(row)
  }
  return result
}

/**
 * Returns Z-rotation in degrees for the connector cutout at summit (i,j).
 */
export function computeConnectorDirection(
  tiles: boolean[][],
  i: number,
  j: number,
): number {
  const tl = isTile(tiles, i - 1, j - 1)
  const tr = isTile(tiles, i - 1, j)
  const bl = isTile(tiles, i, j - 1)
  const br = isTile(tiles, i, j)

  // Horizontal edge
  if (tl === tr && bl === br && tl !== bl) {
    return bl ? -90 : 90
  }
  // Vertical edge
  if (tl === bl && tr === br && tl !== tr) {
    return tr ? 0 : 180
  }
  return 0
}

/**
 * Summit (i,j) is eligible for a tile chamfer iff exactly 1 of its
 * 4 neighboring cells is a tile.
 */
export function computeEligibleChamferPositions(
  tiles: boolean[][],
): boolean[][] {
  const rows = tiles.length
  const cols = tiles[0]?.length ?? 0
  const result: boolean[][] = []
  for (let i = 0; i <= rows; i++) {
    const row: boolean[] = []
    for (let j = 0; j <= cols; j++) {
      const count = [
        isTile(tiles, i - 1, j - 1),
        isTile(tiles, i - 1, j),
        isTile(tiles, i, j - 1),
        isTile(tiles, i, j),
      ].filter(Boolean).length
      row.push(count === 1)
    }
    result.push(row)
  }
  return result
}

/**
 * Summit (i,j) is eligible for a screw iff all 4 neighboring cells are tiles.
 */
export function computeEligibleScrewPositions(
  tiles: boolean[][],
): boolean[][] {
  const rows = tiles.length
  const cols = tiles[0]?.length ?? 0
  const result: boolean[][] = []
  for (let i = 0; i <= rows; i++) {
    const row: boolean[] = []
    for (let j = 0; j <= cols; j++) {
      const tl = isTile(tiles, i - 1, j - 1)
      const tr = isTile(tiles, i - 1, j)
      const bl = isTile(tiles, i, j - 1)
      const br = isTile(tiles, i, j)
      row.push(tl && tr && bl && br)
    }
    result.push(row)
  }
  return result
}

/**
 * Filter eligible screw positions to only corner screws.
 * A summit is a corner if it is eligible and has no pass-through on
 * any axis (not both left+right, and not both up+down neighbors eligible).
 */
export function computeCornerScrewPositions(
  eligible: boolean[][],
): boolean[][] {
  const nRows = eligible.length
  const nCols = eligible[0]?.length ?? 0

  function isEligible(r: number, c: number): boolean {
    if (r >= 0 && r < nRows && c >= 0 && c < nCols) return eligible[r][c]
    return false
  }

  const result: boolean[][] = []
  for (let i = 0; i < nRows; i++) {
    const row: boolean[] = []
    for (let j = 0; j < nCols; j++) {
      if (!eligible[i][j]) {
        row.push(false)
        continue
      }
      const hThrough = isEligible(i, j - 1) && isEligible(i, j + 1)
      const vThrough = isEligible(i - 1, j) && isEligible(i + 1, j)
      row.push(!hThrough && !vThrough)
    }
    result.push(row)
  }
  return result
}

export interface Eligibility {
  connectors: boolean[][]
  chamfers: boolean[][]
  screws: boolean[][]
}

export function computeAllEligibility(tiles: boolean[][]): Eligibility {
  return {
    connectors: computeEligibleConnectorPositions(tiles),
    chamfers: computeEligibleChamferPositions(tiles),
    screws: computeEligibleScrewPositions(tiles),
  }
}
