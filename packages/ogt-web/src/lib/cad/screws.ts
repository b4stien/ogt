import { drawCircle, makeCylinder, type Solid, type Sketch } from "replicad";
import { TILE_THICKNESS } from "./constants";
import type { ScrewSize } from "../types";

const SCREW_HEAD_COUNTERSUNK_DEGREE = 90;

const DEFAULT_SCREW: ScrewSize = {
  diameter: 4.2,
  head_diameter: 8.0,
  head_inset: 1.0,
};

export function makeScrewCutout(
  screwSize: ScrewSize = DEFAULT_SCREW,
  tileThickness: number = TILE_THICKNESS,
  headAtBottom: boolean = false,
): Solid {
  const mainR = screwSize.diameter / 2;
  const headR = screwSize.head_diameter / 2;
  const countersinkH =
    Math.tan((SCREW_HEAD_COUNTERSUNK_DEGREE / 2) * (Math.PI / 180)) *
    (headR - mainR);

  // Main cylinder, full height through tile
  const mainCyl = makeCylinder(mainR, tileThickness, [0, 0, 0], [0, 0, 1]);

  let countersink: Solid;
  let head: Solid;

  if (headAtBottom) {
    // Head (counterbore) at Z=0
    head = makeCylinder(headR, screwSize.head_inset, [0, 0, 0], [0, 0, 1]);

    // Countersink cone above the counterbore (head_r -> main_r going up)
    const bottomCircle = drawCircle(headR).sketchOnPlane(
      "XY",
      screwSize.head_inset,
    ) as Sketch;
    const topCircle = drawCircle(mainR).sketchOnPlane(
      "XY",
      screwSize.head_inset + countersinkH,
    ) as Sketch;
    countersink = bottomCircle.loftWith(topCircle) as Solid;
  } else {
    // Countersink cone near the top (main_r -> head_r going up)
    const countersinkBaseZ =
      tileThickness - screwSize.head_inset - countersinkH;
    const bottomCircle = drawCircle(mainR).sketchOnPlane(
      "XY",
      countersinkBaseZ,
    ) as Sketch;
    const topCircle = drawCircle(headR).sketchOnPlane(
      "XY",
      countersinkBaseZ + countersinkH,
    ) as Sketch;
    countersink = bottomCircle.loftWith(topCircle) as Solid;

    // Head inset cylinder at the top
    head = makeCylinder(
      headR,
      screwSize.head_inset,
      [0, 0, tileThickness - screwSize.head_inset],
      [0, 0, 1],
    );
  }

  return mainCyl.fuse(countersink).fuse(head) as Solid;
}
