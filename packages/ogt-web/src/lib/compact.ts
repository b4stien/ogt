/**
 * Compact encoding/decoding for GridPlan.
 *
 * The canonical format specification lives in the Python module docstring:
 * `src/ogt/compact.py`. This file is a TypeScript port.
 */

import { emptySummit } from "./defaults";
import {
  computeConnectorDirection,
  computeEligibleChamferPositions,
  computeEligibleConnectorPositions,
  computeEligibleScrewPositions,
} from "./eligibility";
import type { GridPlan, ScrewSize, SummitFeatures } from "./types";

// -- Base64url helpers --------------------------------------------------------

const B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

function b64urlEncode(data: Uint8Array): string {
  let out = "";
  for (let i = 0; i < data.length; i += 3) {
    const b0 = data[i];
    const b1 = i + 1 < data.length ? data[i + 1] : 0;
    const b2 = i + 2 < data.length ? data[i + 2] : 0;
    out += B64[(b0 >> 2) & 0x3f];
    out += B64[((b0 << 4) | (b1 >> 4)) & 0x3f];
    if (i + 1 < data.length) out += B64[((b1 << 2) | (b2 >> 6)) & 0x3f];
    if (i + 2 < data.length) out += B64[b2 & 0x3f];
  }
  return out;
}

function b64urlDecode(s: string): Uint8Array {
  const lookup = new Uint8Array(128);
  for (let i = 0; i < B64.length; i++) lookup[B64.charCodeAt(i)] = i;

  // Pad to multiple of 4
  while (s.length % 4 !== 0) s += "=";

  const out: number[] = [];
  for (let i = 0; i < s.length; i += 4) {
    const c0 = s[i] === "=" ? 0 : lookup[s.charCodeAt(i)];
    const c1 = s[i + 1] === "=" ? 0 : lookup[s.charCodeAt(i + 1)];
    const c2 = s[i + 2] === "=" ? 0 : lookup[s.charCodeAt(i + 2)];
    const c3 = s[i + 3] === "=" ? 0 : lookup[s.charCodeAt(i + 3)];
    out.push((c0 << 2) | (c1 >> 4));
    if (s[i + 2] !== "=") out.push(((c1 << 4) | (c2 >> 2)) & 0xff);
    if (s[i + 3] !== "=") out.push(((c2 << 6) | c3) & 0xff);
  }
  return new Uint8Array(out);
}

// -- Bit packing --------------------------------------------------------------

function bitsToBytes(bits: boolean[]): Uint8Array {
  const nBytes = Math.ceil(bits.length / 8);
  const result = new Uint8Array(nBytes);
  for (let i = 0; i < bits.length; i++) {
    if (bits[i]) result[i >> 3] |= 1 << (7 - (i & 7));
  }
  return result;
}

function bytesToBits(data: Uint8Array, nBits: number): boolean[] {
  const bits: boolean[] = [];
  for (let i = 0; i < nBits; i++) {
    const byteIdx = i >> 3;
    const bitIdx = 7 - (i & 7);
    bits.push((data[byteIdx] & (1 << bitIdx)) !== 0);
  }
  return bits;
}

// -- Public API ---------------------------------------------------------------

export function encode(plan: GridPlan): string {
  const rows = plan.tiles.length;
  const cols = plan.tiles[0]?.length ?? 0;

  const typeChar = plan.opengrid_type === "full" ? "f" : "l";

  // Screw → 3 bytes (0.1 mm units)
  const screwBytes = new Uint8Array([
    Math.round(plan.screw_size.diameter * 10),
    Math.round(plan.screw_size.head_diameter * 10),
    Math.round(plan.screw_size.head_inset * 10),
  ]);
  const screwStr = b64urlEncode(screwBytes);

  // Tiles → R×C bits row-major
  const tileBits: boolean[] = [];
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++) tileBits.push(plan.tiles[r][c]);
  const tilesStr = b64urlEncode(bitsToBytes(tileBits));

  // Features → (R+1)×(C+1) bits row-major
  const featureBits: boolean[] = [];
  for (let i = 0; i <= rows; i++) {
    for (let j = 0; j <= cols; j++) {
      const s = plan.summits[i][j];
      featureBits.push(s.connector_angle !== null || s.tile_chamfer || s.screw);
    }
  }
  const featuresStr = b64urlEncode(bitsToBytes(featureBits));

  return `0.${typeChar}.${rows}.${cols}.${screwStr}.${tilesStr}.${featuresStr}`;
}

export function decode(code: string): GridPlan {
  const parts = code.split(".");
  if (parts.length !== 7)
    throw new Error(`Expected 7 dot-separated parts, got ${parts.length}`);

  const [version, typeChar, rStr, cStr, screwStr, tilesStr, featuresStr] =
    parts;

  if (version !== "0") throw new Error(`Unsupported version: '${version}'`);
  if (typeChar !== "f" && typeChar !== "l")
    throw new Error(`Invalid type: '${typeChar}'`);

  const opengridType = typeChar === "f" ? "full" : "lite";
  const rows = parseInt(rStr, 10);
  const cols = parseInt(cStr, 10);
  if (isNaN(rows) || isNaN(cols))
    throw new Error(`Invalid dimensions: '${rStr}' x '${cStr}'`);
  if (rows < 1 || cols < 1)
    throw new Error(`Dimensions must be >= 1, got ${rows}x${cols}`);

  // Screw
  const screwData = b64urlDecode(screwStr);
  if (screwData.length !== 3)
    throw new Error(`Screw data must be 3 bytes, got ${screwData.length}`);
  const screwSize: ScrewSize = {
    diameter: screwData[0] / 10,
    head_diameter: screwData[1] / 10,
    head_inset: screwData[2] / 10,
  };

  // Tiles
  const tilesData = b64urlDecode(tilesStr);
  const nTileBits = rows * cols;
  if (tilesData.length < Math.ceil(nTileBits / 8))
    throw new Error("Insufficient tile data");
  const tileBits = bytesToBits(tilesData, nTileBits);
  const tiles: boolean[][] = [];
  for (let r = 0; r < rows; r++) {
    const row: boolean[] = [];
    for (let c = 0; c < cols; c++) row.push(tileBits[r * cols + c]);
    tiles.push(row);
  }

  // Compute eligibility
  const connEligible = computeEligibleConnectorPositions(tiles);
  const chamferEligible = computeEligibleChamferPositions(tiles);
  const screwEligible = computeEligibleScrewPositions(tiles);

  // Features
  const featuresData = b64urlDecode(featuresStr);
  const nFeatureBits = (rows + 1) * (cols + 1);
  if (featuresData.length < Math.ceil(nFeatureBits / 8))
    throw new Error("Insufficient feature data");
  const featureBits = bytesToBits(featuresData, nFeatureBits);

  // Build summits
  const summits: SummitFeatures[][] = [];
  for (let i = 0; i <= rows; i++) {
    const row: SummitFeatures[] = [];
    for (let j = 0; j <= cols; j++) {
      const bit = featureBits[i * (cols + 1) + j];
      const sf = emptySummit();
      if (bit) {
        if (connEligible[i][j]) {
          sf.connector_angle = computeConnectorDirection(tiles, i, j);
        } else if (chamferEligible[i][j]) {
          sf.tile_chamfer = true;
        } else if (screwEligible[i][j]) {
          sf.screw = true;
        }
      }
      row.push(sf);
    }
    summits.push(row);
  }

  return {
    tiles,
    summits,
    opengrid_type: opengridType as "full" | "lite",
    screw_size: screwSize,
  };
}
