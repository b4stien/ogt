import type { Solid } from "replicad";
import { TILE_SIZE, TILE_THICKNESS } from "./constants";
import { CONNECTOR_CUTOUT_HEIGHT, makeConnectorCutout } from "./connectors";
import { makeScrewCutout } from "./screws";
import { makeTileChamferCutout } from "./chamfers";
import { makeOpengridFullTile } from "./tile-full";
import { LITE_TILE_THICKNESS, makeOpengridLiteTile } from "./tile-lite";
import type { GridPlan } from "../types";

export function drawGrid(plan: GridPlan): Solid {
  let result: Solid | null = null;

  // Place tiles
  for (let rowIdx = 0; rowIdx < plan.tiles.length; rowIdx++) {
    const row = plan.tiles[rowIdx];
    for (let colIdx = 0; colIdx < row.length; colIdx++) {
      if (!row[colIdx]) continue;

      const x = colIdx * TILE_SIZE + TILE_SIZE / 2;
      const y = -(rowIdx * TILE_SIZE + TILE_SIZE / 2);

      const baseTile =
        plan.opengrid_type === "lite"
          ? makeOpengridLiteTile()
          : makeOpengridFullTile();

      const tile = baseTile.clone().translate(x, y, 0) as Solid;

      if (result === null) {
        result = tile;
      } else {
        result = result.fuse(tile) as Solid;
      }
    }
  }

  if (result === null) {
    throw new Error("No tiles in grid plan");
  }

  // Prepare cutout templates (created once, reused)
  let connectorTemplate: Solid | null = null;
  let connectorZ = 0;
  let screwTemplate: Solid | null = null;

  // Apply summit features
  for (let i = 0; i < plan.summits.length; i++) {
    const row = plan.summits[i];
    for (let j = 0; j < row.length; j++) {
      const summit = row[j];
      const sx = j * TILE_SIZE;
      const sy = -i * TILE_SIZE;

      if (summit.connector_angle !== null) {
        if (connectorTemplate === null) {
          connectorTemplate = makeConnectorCutout();
          if (plan.opengrid_type === "lite") {
            // Lite tile: connector is not centered (asymmetric wall
            // profile). Z=1.0 measured from reference STEP.
            connectorZ = 1.0;
          } else {
            connectorZ = TILE_THICKNESS / 2 - CONNECTOR_CUTOUT_HEIGHT / 2;
          }
        }
        const cutout = connectorTemplate
          .clone()
          .rotate(summit.connector_angle, [0, 0, 0], [0, 0, 1])
          .translate(sx, sy, connectorZ) as Solid;
        result = result.cut(cutout) as Solid;
      }

      if (summit.tile_chamfer) {
        const cutout = makeTileChamferCutout()
          .clone()
          .translate(sx, sy, 0) as Solid;
        result = result.cut(cutout) as Solid;
      }

      if (summit.screw) {
        if (screwTemplate === null) {
          const thickness =
            plan.opengrid_type === "lite"
              ? LITE_TILE_THICKNESS
              : TILE_THICKNESS;
          screwTemplate = makeScrewCutout(
            plan.screw_size,
            thickness,
            plan.opengrid_type === "lite",
          );
        }
        const cutout = screwTemplate.clone().translate(sx, sy, 0) as Solid;
        result = result.cut(cutout) as Solid;
      }
    }
  }

  return result;
}
