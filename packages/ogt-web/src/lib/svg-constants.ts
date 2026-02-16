/**
 * SVG coordinate system
 *
 * Each cell is CELL_SIZE × CELL_SIZE (100×100) and includes the tile content
 * (TILE_CONTENT = 88×88) plus GAP/2 margins on each edge. Summits sit at
 * clean multiples of CELL_SIZE.
 *
 * Dimension indicators are drawn in a DIM_OFFSET (40px) margin on the top
 * and left sides. The viewBox origin is shifted to (-DIM_OFFSET, -DIM_OFFSET)
 * so dimension lines sit in negative coordinate space.
 *
 *                  ┊← DIM_OFFSET →┊
 *                  ┊               ┊
 *            ──────┊──── top dim ──┊──────────────────
 *                  ┊               ┊
 *      left dim    summit(0,0)          summit(0,1)          summit(0,2)
 *         ┊          (0,0)               (100,0)              (200,0)
 *         ┊            ┌──────────────────┬──────────────────┐
 *         ┊            │    ┌────────┐    │    ┌────────┐    │
 *         ┊            │  6 │ tile   │ 94 │106 │ tile   │194 │
 *         ┊            │    │ (0,0)  │    │    │ (0,1)  │    │
 *         ┊            │    └────────┘    │    └────────┘    │
 *         ┊            │         94       │        194       │
 *                    summit(1,0)          summit(1,1)          summit(1,2)
 *                      (0,100)             (100,100)            (200,100)
 *                      ├──────────────────┼──────────────────┤
 *                      │    ┌────────┐    │    ┌────────┐    │
 *                      │    │ tile   │    │    │ tile   │    │
 *                      │    │ (1,0)  │    │    │ (1,1)  │    │
 *                      │    └────────┘    │    └────────┘    │
 *                      └──────────────────┴──────────────────┘
 *                    summit(2,0)          summit(2,1)          summit(2,2)
 *                      (0,200)             (100,200)            (200,200)
 */
export const CELL_SIZE = 100;
export const GAP = 12;
export const TILE_CONTENT = CELL_SIZE - GAP;
export const PADDING = 40;

// Feature size constants (proportional to real 28mm tile)
export const CHAMFER_SIZE = TILE_CONTENT * 0.25;
export const CONNECTOR_RADIUS = TILE_CONTENT * 0.14;
export const SCREW_RADIUS = TILE_CONTENT * 0.14;

/** Top-left corner of tile [r,c] */
export function tileX(c: number): number {
  return c * CELL_SIZE + GAP / 2;
}
export function tileY(r: number): number {
  return r * CELL_SIZE + GAP / 2;
}

/** Position of summit (i,j) — intersection point between tiles */
export function summitX(j: number): number {
  return j * CELL_SIZE;
}
export function summitY(i: number): number {
  return i * CELL_SIZE;
}

/** Total grid extent (tiles only, no add-zones) */
export function gridWidth(cols: number): number {
  return cols * CELL_SIZE;
}
export function gridHeight(rows: number): number {
  return rows * CELL_SIZE;
}

export const COLORS = {
  // Green = will be printed, gray = won't
  tileFill: "#bbf7d0",
  holeFill: "#f5f5f5",
  holeStroke: "#d4d4d4",

  featureActive: "#f5f5f5",
  featureGhost: "#bbf7d0",

  addZoneStroke: "#a3a3a3",
  addZoneFill: "#fafafa",
  addZoneText: "#a3a3a3",
} as const;
