import { drawCircle, makeCylinder, type Solid, type Sketch } from "replicad";
import { TILE_THICKNESS } from "./constants";
import type { ScrewSize } from "../types";

const SCREW_HEAD_COUNTERSUNK_DEGREE = 90;

const DEFAULT_SCREW: ScrewSize = {
  diameter: 4.2,
  head_diameter: 8.0,
  head_inset: 1.0,
};

export function makeScrewCutout(screwSize: ScrewSize = DEFAULT_SCREW): Solid {
  const mainR = screwSize.diameter / 2;
  const headR = screwSize.head_diameter / 2;
  const countersinkH =
    Math.tan((SCREW_HEAD_COUNTERSUNK_DEGREE / 2) * (Math.PI / 180)) *
    (headR - mainR);

  // Main cylinder, full height through tile
  const mainCyl = makeCylinder(mainR, TILE_THICKNESS, [0, 0, 0], [0, 0, 1]);

  // Countersink cone via loft
  const countersinkBaseZ = TILE_THICKNESS - screwSize.head_inset - countersinkH;
  const bottomCircle = drawCircle(mainR).sketchOnPlane(
    "XY",
    countersinkBaseZ,
  ) as Sketch;
  const topCircle = drawCircle(headR).sketchOnPlane(
    "XY",
    countersinkBaseZ + countersinkH,
  ) as Sketch;
  const countersink = bottomCircle.loftWith(topCircle) as Solid;

  // Head inset cylinder
  const head = makeCylinder(
    headR,
    screwSize.head_inset,
    [0, 0, TILE_THICKNESS - screwSize.head_inset],
    [0, 0, 1],
  );

  return mainCyl.fuse(countersink).fuse(head) as Solid;
}
