import type { ScrewSize, SummitFeatures } from "./types";

/** Physical tile size: 28 mm = 2.8 cm */
export const TILE_SIZE_CM = 2.8;

export const DEFAULT_SCREW_SIZE: ScrewSize = {
  diameter: 4.2,
  head_diameter: 8.0,
  head_inset: 1.0,
};

export const LITE_DEFAULT_SCREW_SIZE: ScrewSize = {
  diameter: 4.1,
  head_diameter: 7.2,
  head_inset: 1.0,
};

export function emptySummit(): SummitFeatures {
  return { connector_angle: null, tile_chamfer: false, screw: false };
}

export function createEmptyGrid(rows: number, cols: number) {
  const tiles = Array.from({ length: rows }, () =>
    Array.from({ length: cols }, () => true),
  );
  const summits = Array.from({ length: rows + 1 }, () =>
    Array.from({ length: cols + 1 }, () => emptySummit()),
  );
  return { tiles, summits };
}
