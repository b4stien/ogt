import { drawRectangle, type Solid } from "replicad";
import { TILE_THICKNESS } from "./constants";

const INTERSECTION_DISTANCE = 4.2;
const TILE_CHAMFER = Math.sqrt(INTERSECTION_DISTANCE ** 2 * 2);

let cached: Solid | null = null;

export function makeTileChamferCutout(): Solid {
  if (cached) return cached;
  cached = drawRectangle(TILE_CHAMFER, TILE_CHAMFER)
    .rotate(45)
    .sketchOnPlane("XY")
    .extrude(TILE_THICKNESS) as Solid;
  return cached;
}
