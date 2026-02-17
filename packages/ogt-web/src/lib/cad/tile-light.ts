import { draw, drawRectangle, type Solid } from "replicad";
import { TILE_SIZE } from "./constants";

export const LITE_TILE_THICKNESS = 4.0;
const SQRT2 = Math.sqrt(2);

function makeTileWall(): Solid {
  const halfSize = TILE_SIZE / 2; // 14

  // Profile on YZ plane, extruded along X
  const profile = draw([0.0, LITE_TILE_THICKNESS])
    .lineTo([0.0, 0.0])
    .lineTo([0.8, 0.0])
    .lineTo([0.8, 1.6])
    .lineTo([1.5, 2.6])
    .lineTo([1.5, 3.6])
    .lineTo([1.1, LITE_TILE_THICKNESS])
    .close()
    .sketchOnPlane("YZ")
    .extrude(TILE_SIZE) as Solid;

  // Center on X, outer face at Y = -14
  return profile.translate(-halfSize, -halfSize, 0) as Solid;
}

function makeCornerWall(): Solid {
  const halfSize = TILE_SIZE / 2; // 14
  const extrudeLen = TILE_SIZE * SQRT2;

  const profile = draw([0.0, LITE_TILE_THICKNESS])
    .lineTo([4.17, LITE_TILE_THICKNESS])
    .lineTo([5.57, 2.6])
    .lineTo([5.57, 0.0])
    .lineTo([0.0, 0.0])
    .close()
    .sketchOnPlane("YZ")
    .extrude(extrudeLen) as Solid;

  // Center on X, outer face at Y = -14*sqrt(2)
  return profile.translate(-extrudeLen / 2, -halfSize * SQRT2, 0) as Solid;
}

let cachedTile: Solid | null = null;

export function makeOpengridLightTile(): Solid {
  if (cachedTile) return cachedTile;

  // Axis-aligned frame: 4 walls at 0, 90, 180, 270
  const wall = makeTileWall();
  let axisFrame: Solid = wall;
  for (const angle of [90, 180, 270]) {
    axisFrame = axisFrame.fuse(
      wall.clone().rotate(angle, [0, 0, 0], [0, 0, 1]) as Solid,
    ) as Solid;
  }

  // 45-degree frame: 4 corner walls, then rotate entire frame 45
  const corner = makeCornerWall();
  let diagFrame: Solid = corner;
  for (const angle of [90, 180, 270]) {
    diagFrame = diagFrame.fuse(
      corner.clone().rotate(angle, [0, 0, 0], [0, 0, 1]) as Solid,
    ) as Solid;
  }
  diagFrame = diagFrame.rotate(45, [0, 0, 0], [0, 0, 1]) as Solid;

  // Union both frames
  let tile = axisFrame.fuse(diagFrame) as Solid;

  // Intersect with bounding box to clip to tile footprint
  const bbox = drawRectangle(TILE_SIZE, TILE_SIZE)
    .sketchOnPlane("XY")
    .extrude(LITE_TILE_THICKNESS) as Solid;

  tile = tile.intersect(bbox) as Solid;

  cachedTile = tile;
  return tile;
}
