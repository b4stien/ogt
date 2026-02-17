import { draw, type Solid } from "replicad";

export const CONNECTOR_CUTOUT_HEIGHT = 2.4;

function mod(x: number, m: number): number {
  return ((x % m) + m) % m;
}

function arcMid(
  cx: number,
  cy: number,
  r: number,
  ax: number,
  ay: number,
  bx: number,
  by: number,
): [number, number] {
  const aAng = Math.atan2(ay - cy, ax - cx);
  const bAng = Math.atan2(by - cy, bx - cx);
  // CW sweep (negative direction)
  const cw = mod(aAng - bAng, 2 * Math.PI);
  // CCW sweep (positive direction)
  const ccw = mod(bAng - aAng, 2 * Math.PI);

  let mid: number;
  if (cw < ccw) {
    // Shorter arc is CW
    mid = aAng - cw / 2;
  } else if (ccw < cw) {
    // Shorter arc is CCW
    mid = aAng + ccw / 2;
  } else {
    // Semicircle: pick the side with larger x (outward from tile wall)
    const midCcw = aAng + ccw / 2;
    const midCw = aAng - cw / 2;
    const xCcw = cx + r * Math.cos(midCcw);
    const xCw = cx + r * Math.cos(midCw);
    mid = xCcw > xCw ? midCcw : midCw;
  }
  return [cx + r * Math.cos(mid), cy + r * Math.sin(mid)];
}

type Edge = [
  kind: "LINE" | "ARC",
  start: [number, number],
  end: [number, number],
  center: [number, number] | null,
  radius: number | null,
];

const edges: Edge[] = [
  // 1: outer fillet bottom-left
  ["ARC", [0.0, -2.567], [0.275, -2.318], [0.25, -2.567], 0.25],
  // 2: connecting arc (left dimple)
  ["ARC", [0.275, -2.318], [1.156, -2.555], [0.0, -5.1], 2.795],
  // 3: inner fillet bottom
  ["ARC", [1.156, -2.555], [1.363, -2.6], [1.363, -2.1], 0.5],
  // 4: bottom flat
  ["LINE", [1.363, -2.6], [2.5, -2.6], null, null],
  // 5: bottom arc (big semicircle)
  ["ARC", [2.5, -2.6], [2.5, 2.6], [2.5, 0.0], 2.6],
  // 6: top flat
  ["LINE", [2.5, 2.6], [1.363, 2.6], null, null],
  // 7: inner fillet top
  ["ARC", [1.363, 2.6], [1.156, 2.555], [1.363, 2.1], 0.5],
  // 8: connecting arc (right dimple)
  ["ARC", [1.156, 2.555], [0.275, 2.318], [0.0, 5.1], 2.795],
  // 9: outer fillet top-left
  ["ARC", [0.275, 2.318], [0.0, 2.567], [0.25, 2.567], 0.25],
  // 10: closing line
  ["LINE", [0.0, 2.567], [0.0, -2.567], null, null],
];

let cachedCutout: Solid | null = null;

export function makeConnectorCutout(): Solid {
  if (cachedCutout) return cachedCutout;

  let sketcher = draw([0.0, -2.567]);

  for (const [kind, start, end, center, radius] of edges) {
    if (kind === "LINE") {
      sketcher = sketcher.lineTo(end);
    } else {
      const mid = arcMid(
        center![0],
        center![1],
        radius!,
        start[0],
        start[1],
        end[0],
        end[1],
      );
      sketcher = sketcher.threePointsArcTo(end, mid);
    }
  }

  const cutout = sketcher
    .close()
    .sketchOnPlane("XY")
    .extrude(CONNECTOR_CUTOUT_HEIGHT) as Solid;

  cachedCutout = cutout;
  return cutout;
}
