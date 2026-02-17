import {
  TILE_CONTENT,
  GAP,
  COLORS,
  PADDING,
  CONNECTOR_RADIUS,
  CHAMFER_SIZE,
  SCREW_RADIUS,
  tileX,
  tileY,
  summitX,
  summitY,
  gridWidth,
  gridHeight,
} from "@/lib/svg-constants";
import { computeConnectorDirection, isTile } from "@/lib/eligibility";
import type { Eligibility } from "@/lib/eligibility";
import type { SummitFeatures } from "@/lib/types";
import { TILE_SIZE_CM } from "@/lib/defaults";

const BUTTON_TEXT_SIZE = 12;
const DIM_OFFSET = 40; // space reserved for dimension indicators
const DIM_TICK = 6; // tick mark length
const DIM_TEXT_SIZE = 11;
const DIM_COLOR = "#a3a3a3";

// --- Helpers ---

type FeatureType = "chamfer" | "screw" | "connector" | null;

function cornerFeature(
  eligibility: Eligibility,
  si: number,
  sj: number,
): FeatureType {
  if (eligibility.chamfers[si]?.[sj]) return "chamfer";
  if (eligibility.screws[si]?.[sj]) return "screw";
  if (eligibility.connectors[si]?.[sj]) return "connector";
  return null;
}

// --- Tile path builder ---

function buildTilePath(
  r: number,
  c: number,
  tiles: boolean[][],
  eligibility: Eligibility,
): string {
  const x = tileX(c);
  const y = tileY(r);

  // Corner definitions in clockwise order: TL → TR → BR → BL
  // Each has: position, summit indices, entry/exit offset directions from corner
  const corners = [
    { cx: x, cy: y, si: r, sj: c, edx: 0, edy: 1, exdx: 1, exdy: 0 },
    {
      cx: x + TILE_CONTENT,
      cy: y,
      si: r,
      sj: c + 1,
      edx: -1,
      edy: 0,
      exdx: 0,
      exdy: 1,
    },
    {
      cx: x + TILE_CONTENT,
      cy: y + TILE_CONTENT,
      si: r + 1,
      sj: c + 1,
      edx: 0,
      edy: -1,
      exdx: -1,
      exdy: 0,
    },
    {
      cx: x,
      cy: y + TILE_CONTENT,
      si: r + 1,
      sj: c,
      edx: 1,
      edy: 0,
      exdx: 0,
      exdy: -1,
    },
  ];

  const parts: string[] = [];

  for (let i = 0; i < corners.length; i++) {
    const { cx, cy, si, sj, edx, edy, exdx, exdy } = corners[i];
    const feature = cornerFeature(eligibility, si, sj);

    let entryX: number, entryY: number;
    let exitX: number, exitY: number;
    let cornerPath: string;

    if (feature === "chamfer") {
      const d = CHAMFER_SIZE + GAP * Math.SQRT2;
      entryX = cx + edx * d;
      entryY = cy + edy * d;
      exitX = cx + exdx * d;
      exitY = cy + exdy * d;
      cornerPath = `L ${exitX} ${exitY}`;
    } else if (feature === "connector") {
      const R = CONNECTOR_RADIUS + GAP;
      // Center the cutout arc on the connector's semicircle center
      const sx = summitX(sj);
      const sy = summitY(si);
      const dir = computeConnectorDirection(tiles, si, sj);
      const rad = (-dir * Math.PI) / 180;
      const ccx = sx + (GAP / 2) * Math.cos(rad);
      const ccy = sy + (GAP / 2) * Math.sin(rad);
      if (edy === 0) {
        entryX = ccx + edx * Math.sqrt(R * R - (cy - ccy) ** 2);
        entryY = cy;
      } else {
        entryX = cx;
        entryY = ccy + edy * Math.sqrt(R * R - (cx - ccx) ** 2);
      }
      if (exdy === 0) {
        exitX = ccx + exdx * Math.sqrt(R * R - (cy - ccy) ** 2);
        exitY = cy;
      } else {
        exitX = cx;
        exitY = ccy + exdy * Math.sqrt(R * R - (cx - ccx) ** 2);
      }
      cornerPath = `A ${R} ${R} 0 0 0 ${exitX} ${exitY}`;
    } else if (feature === "screw") {
      // Arc centered at summit (GAP/2 outside corner)
      const R = SCREW_RADIUS + GAP;
      const offset = Math.sqrt(R * R - (GAP / 2) * (GAP / 2)) - GAP / 2;
      entryX = cx + edx * offset;
      entryY = cy + edy * offset;
      exitX = cx + exdx * offset;
      exitY = cy + exdy * offset;
      cornerPath = `A ${R} ${R} 0 0 0 ${exitX} ${exitY}`;
    } else {
      entryX = cx;
      entryY = cy;
      exitX = cx;
      exitY = cy;
      cornerPath = "";
    }

    if (i === 0) {
      parts.push(`M ${entryX} ${entryY}`);
    } else {
      parts.push(`L ${entryX} ${entryY}`);
    }

    if (cornerPath) {
      parts.push(cornerPath);
    }
  }

  parts.push("Z");
  return parts.join(" ");
}

// --- Components ---

interface GridSvgProps {
  tiles: boolean[][];
  summits: SummitFeatures[][];
  eligibility: Eligibility;
  onToggleTile: (r: number, c: number) => void;
  onToggleConnector: (i: number, j: number) => void;
  onToggleChamfer: (i: number, j: number) => void;
  onToggleScrew: (i: number, j: number) => void;
  onAddRow: () => void;
  onRemoveRow: () => void;
  onAddColumn: () => void;
  onRemoveColumn: () => void;
}

function Tile({
  r,
  c,
  present,
  tiles,
  eligibility,
  onClick,
}: {
  r: number;
  c: number;
  present: boolean;
  tiles: boolean[][];
  eligibility: Eligibility;
  onClick: () => void;
}) {
  if (!present) {
    const x = tileX(c);
    const y = tileY(r);
    return (
      <rect
        x={x}
        y={y}
        width={TILE_CONTENT}
        height={TILE_CONTENT}
        fill={COLORS.holeFill}
        stroke={COLORS.holeStroke}
        strokeWidth={1}
        strokeDasharray="4 4"
        rx={3}
        onClick={onClick}
        className="cursor-pointer"
      />
    );
  }

  return (
    <path
      d={buildTilePath(r, c, tiles, eligibility)}
      fill={COLORS.tileFill}
      onClick={onClick}
      className="cursor-pointer"
    />
  );
}

function ChamferFeature({
  i,
  j,
  active,
  eligible,
  tiles,
  onClick,
}: {
  i: number;
  j: number;
  active: boolean;
  eligible: boolean;
  tiles: boolean[][];
  onClick: () => void;
}) {
  if (!eligible) return null;
  const sx = summitX(j);
  const sy = summitY(i);
  const color = active ? COLORS.featureActive : COLORS.featureGhost;
  const S = CHAMFER_SIZE;

  const br = isTile(tiles, i, j);
  const bl = isTile(tiles, i, j - 1);
  const tr = isTile(tiles, i - 1, j);

  let dx1: number, dy1: number, dx2: number, dy2: number;
  if (br) {
    dx1 = S;
    dy1 = 0;
    dx2 = 0;
    dy2 = S;
  } else if (bl) {
    dx1 = -S;
    dy1 = 0;
    dx2 = 0;
    dy2 = S;
  } else if (tr) {
    dx1 = S;
    dy1 = 0;
    dx2 = 0;
    dy2 = -S;
  } else {
    dx1 = -S;
    dy1 = 0;
    dx2 = 0;
    dy2 = -S;
  }

  // Right angle at the tile corner (GAP/2 toward the tile from summit)
  const ox = sx + (Math.sign(dx1) * GAP) / 2;
  const oy = sy + (Math.sign(dy2) * GAP) / 2;

  return (
    <polygon
      points={`${ox},${oy} ${ox + dx1},${oy + dy1} ${ox + dx2},${oy + dy2}`}
      fill={color}
      onClick={onClick}
      className="cursor-pointer"
    />
  );
}

function ConnectorFeature({
  i,
  j,
  active,
  eligible,
  angle,
  tiles,
  onClick,
}: {
  i: number;
  j: number;
  active: boolean;
  eligible: boolean;
  angle: number | null;
  tiles: boolean[][];
  onClick: () => void;
}) {
  if (!eligible) return null;
  const sx = summitX(j);
  const sy = summitY(i);
  // Negate: computeConnectorDirection uses math-convention angles (y-up)
  // but SVG rotate() is y-down. Negating fixes horizontal edges (-90↔90)
  // while leaving vertical edges (0, 180) unchanged.
  const direction =
    active && angle !== null ? angle : computeConnectorDirection(tiles, i, j);
  const rotation = -direction;
  const color = active ? COLORS.featureActive : COLORS.featureGhost;
  // Flat side at GAP/2 from origin (aligns with tile edge after rotation)
  const R = CONNECTOR_RADIUS;
  const g = GAP / 2;
  const d = `M ${g} ${-R} A ${R} ${R} 0 0 1 ${g} ${R} Z`;
  return (
    <path
      d={d}
      transform={`translate(${sx},${sy}) rotate(${rotation})`}
      fill={color}
      onClick={onClick}
      className="cursor-pointer"
    />
  );
}

function ScrewFeature({
  i,
  j,
  active,
  eligible,
  onClick,
}: {
  i: number;
  j: number;
  active: boolean;
  eligible: boolean;
  onClick: () => void;
}) {
  if (!eligible) return null;
  const x = summitX(j);
  const y = summitY(i);
  const color = active ? COLORS.featureActive : COLORS.featureGhost;
  return (
    <circle
      cx={x}
      cy={y}
      r={SCREW_RADIUS}
      fill={color}
      onClick={onClick}
      className="cursor-pointer"
    />
  );
}

export function GridSvg({
  tiles,
  summits,
  eligibility,
  onToggleTile,
  onToggleConnector,
  onToggleChamfer,
  onToggleScrew,
  onAddRow,
  onRemoveRow,
  onAddColumn,
  onRemoveColumn,
}: GridSvgProps) {
  const rows = tiles.length;
  const cols = tiles[0]?.length ?? 0;
  const gw = gridWidth(cols);
  const gh = gridHeight(rows);
  const addZoneSize = 36;
  const stackRows = cols === 1 && rows > 1;
  const stackCols = rows === 1 && cols > 1;
  const totalW = gw + GAP + addZoneSize + (stackCols ? GAP + addZoneSize : 0);
  const totalH = gh + GAP + addZoneSize + (stackRows ? GAP + addZoneSize : 0);
  const svgW = DIM_OFFSET + totalW + PADDING;
  const svgH = DIM_OFFSET + totalH;
  const viewBox = `${-DIM_OFFSET} ${-DIM_OFFSET} ${svgW} ${svgH}`;

  return (
    <svg
      viewBox={viewBox}
      width={svgW}
      height={svgH}
      style={{ marginLeft: -46 }}
    >
      {/* Layer 1: Tile cells */}
      {tiles.map((row, r) =>
        row.map((present, c) => (
          <Tile
            key={`tile-${r}-${c}`}
            r={r}
            c={c}
            present={present}
            tiles={tiles}
            eligibility={eligibility}
            onClick={() => onToggleTile(r, c)}
          />
        )),
      )}

      {/* Layer 2: Summit features */}
      {summits.map((row, i) =>
        row.map((s, j) => (
          <g key={`summit-${i}-${j}`}>
            <ChamferFeature
              i={i}
              j={j}
              active={s.tile_chamfer}
              eligible={eligibility.chamfers[i]?.[j] ?? false}
              tiles={tiles}
              onClick={() => onToggleChamfer(i, j)}
            />
            <ConnectorFeature
              i={i}
              j={j}
              active={s.connector_angle !== null}
              eligible={eligibility.connectors[i]?.[j] ?? false}
              angle={s.connector_angle}
              tiles={tiles}
              onClick={() => onToggleConnector(i, j)}
            />
            <ScrewFeature
              i={i}
              j={j}
              active={s.screw}
              eligible={eligibility.screws[i]?.[j] ?? false}
              onClick={() => onToggleScrew(i, j)}
            />
          </g>
        )),
      )}

      {/* Row zones (bottom): Remove left, Add right (stacked if 1 col) */}
      {(() => {
        const zy = gh + GAP;
        const zx = GAP / 2;
        const fullW = gw - GAP;
        const halfW = (fullW - GAP) / 2;
        if (stackRows) {
          return (
            <>
              <g onClick={onAddRow} className="cursor-pointer">
                <rect
                  x={zx}
                  y={zy}
                  width={fullW}
                  height={addZoneSize}
                  rx={4}
                  fill={COLORS.addZoneFill}
                  stroke={COLORS.addZoneStroke}
                  strokeWidth={1}
                  strokeDasharray="6 4"
                />
                <text
                  x={zx + fullW / 2}
                  y={zy + addZoneSize / 2}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={BUTTON_TEXT_SIZE}
                  fill={COLORS.addZoneText}
                >
                  Add row
                </text>
              </g>
              <g onClick={onRemoveRow} className="cursor-pointer">
                <rect
                  x={zx}
                  y={zy + addZoneSize + GAP}
                  width={fullW}
                  height={addZoneSize}
                  rx={4}
                  fill={COLORS.addZoneFill}
                  stroke={COLORS.addZoneStroke}
                  strokeWidth={1}
                  strokeDasharray="6 4"
                />
                <text
                  x={zx + fullW / 2}
                  y={zy + addZoneSize + GAP + addZoneSize / 2}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={BUTTON_TEXT_SIZE}
                  fill={COLORS.addZoneText}
                >
                  Remove row
                </text>
              </g>
            </>
          );
        }
        return (
          <>
            {rows > 1 && (
              <g onClick={onRemoveRow} className="cursor-pointer">
                <rect
                  x={zx}
                  y={zy}
                  width={halfW}
                  height={addZoneSize}
                  rx={4}
                  fill={COLORS.addZoneFill}
                  stroke={COLORS.addZoneStroke}
                  strokeWidth={1}
                  strokeDasharray="6 4"
                />
                <text
                  x={zx + halfW / 2}
                  y={zy + addZoneSize / 2}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={BUTTON_TEXT_SIZE}
                  fill={COLORS.addZoneText}
                >
                  Remove row
                </text>
              </g>
            )}
            <g onClick={onAddRow} className="cursor-pointer">
              <rect
                x={rows > 1 ? zx + halfW + GAP : zx}
                y={zy}
                width={rows > 1 ? halfW : fullW}
                height={addZoneSize}
                rx={4}
                fill={COLORS.addZoneFill}
                stroke={COLORS.addZoneStroke}
                strokeWidth={1}
                strokeDasharray="6 4"
              />
              <text
                x={rows > 1 ? zx + halfW + GAP + halfW / 2 : zx + fullW / 2}
                y={zy + addZoneSize / 2}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={BUTTON_TEXT_SIZE}
                fill={COLORS.addZoneText}
              >
                Add row
              </text>
            </g>
          </>
        );
      })()}

      {/* Column zones (right): Add top, Remove bottom (stacked if 1 row) */}
      {(() => {
        const colLabel = rows < 3 ? "col" : "column";
        const zx = gw + GAP;
        const zy = GAP / 2;
        const fullH = gh - GAP;
        const halfH = (fullH - GAP) / 2;
        if (stackCols) {
          const cx1 = zx + addZoneSize / 2;
          const cx2 = zx + addZoneSize + GAP + addZoneSize / 2;
          const cy = zy + fullH / 2;
          return (
            <>
              <g onClick={onAddColumn} className="cursor-pointer">
                <rect
                  x={zx}
                  y={zy}
                  width={addZoneSize}
                  height={fullH}
                  rx={4}
                  fill={COLORS.addZoneFill}
                  stroke={COLORS.addZoneStroke}
                  strokeWidth={1}
                  strokeDasharray="6 4"
                />
                <text
                  x={cx1}
                  y={cy}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={BUTTON_TEXT_SIZE}
                  fill={COLORS.addZoneText}
                  transform={`rotate(-90, ${cx1}, ${cy})`}
                >
                  {`Add ${colLabel}`}
                </text>
              </g>
              <g onClick={onRemoveColumn} className="cursor-pointer">
                <rect
                  x={zx + addZoneSize + GAP}
                  y={zy}
                  width={addZoneSize}
                  height={fullH}
                  rx={4}
                  fill={COLORS.addZoneFill}
                  stroke={COLORS.addZoneStroke}
                  strokeWidth={1}
                  strokeDasharray="6 4"
                />
                <text
                  x={cx2}
                  y={cy}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={BUTTON_TEXT_SIZE}
                  fill={COLORS.addZoneText}
                  transform={`rotate(-90, ${cx2}, ${cy})`}
                >
                  {`Remove ${colLabel}`}
                </text>
              </g>
            </>
          );
        }
        const cx = zx + addZoneSize / 2;
        return (
          <>
            <g onClick={onAddColumn} className="cursor-pointer">
              <rect
                x={zx}
                y={zy}
                width={addZoneSize}
                height={cols > 1 ? halfH : fullH}
                rx={4}
                fill={COLORS.addZoneFill}
                stroke={COLORS.addZoneStroke}
                strokeWidth={1}
                strokeDasharray="6 4"
              />
              <text
                x={cx}
                y={cols > 1 ? zy + halfH / 2 : zy + fullH / 2}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={BUTTON_TEXT_SIZE}
                fill={COLORS.addZoneText}
                transform={`rotate(-90, ${cx}, ${cols > 1 ? zy + halfH / 2 : zy + fullH / 2})`}
              >
                {`Add ${colLabel}`}
              </text>
            </g>
            {cols > 1 && (
              <g onClick={onRemoveColumn} className="cursor-pointer">
                <rect
                  x={zx}
                  y={zy + halfH + GAP}
                  width={addZoneSize}
                  height={halfH}
                  rx={4}
                  fill={COLORS.addZoneFill}
                  stroke={COLORS.addZoneStroke}
                  strokeWidth={1}
                  strokeDasharray="6 4"
                />
                <text
                  x={cx}
                  y={zy + halfH + GAP + halfH / 2}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={BUTTON_TEXT_SIZE}
                  fill={COLORS.addZoneText}
                  transform={`rotate(-90, ${cx}, ${zy + halfH + GAP + halfH / 2})`}
                >
                  {`Remove ${colLabel}`}
                </text>
              </g>
            )}
          </>
        );
      })()}

      {/* Top dimension indicator */}
      {(() => {
        const y = -DIM_OFFSET / 2;
        const x1 = GAP / 2;
        const x2 = gw - GAP / 2;
        const label = `${cols} column${cols > 1 ? "s" : ""} · ${(cols * TILE_SIZE_CM).toFixed(1)} cm`;
        return (
          <g>
            <line
              x1={x1}
              y1={y}
              x2={x2}
              y2={y}
              stroke={DIM_COLOR}
              strokeWidth={0.5}
            />
            <line
              x1={x1}
              y1={y - DIM_TICK / 2}
              x2={x1}
              y2={y + DIM_TICK / 2}
              stroke={DIM_COLOR}
              strokeWidth={0.5}
            />
            <line
              x1={x2}
              y1={y - DIM_TICK / 2}
              x2={x2}
              y2={y + DIM_TICK / 2}
              stroke={DIM_COLOR}
              strokeWidth={0.5}
            />
            <text
              x={(x1 + x2) / 2}
              y={y - DIM_TICK}
              textAnchor="middle"
              fontSize={DIM_TEXT_SIZE}
              fill={DIM_COLOR}
            >
              {label}
            </text>
          </g>
        );
      })()}

      {/* Left dimension indicator */}
      {(() => {
        const x = -DIM_OFFSET / 2;
        const y1 = GAP / 2;
        const y2 = gh - GAP / 2;
        const label = `${rows} row${rows > 1 ? "s" : ""} · ${(rows * TILE_SIZE_CM).toFixed(1)} cm`;
        const cx = x;
        const cy = (y1 + y2) / 2;
        return (
          <g>
            <line
              x1={x}
              y1={y1}
              x2={x}
              y2={y2}
              stroke={DIM_COLOR}
              strokeWidth={0.5}
            />
            <line
              x1={x - DIM_TICK / 2}
              y1={y1}
              x2={x + DIM_TICK / 2}
              y2={y1}
              stroke={DIM_COLOR}
              strokeWidth={0.5}
            />
            <line
              x1={x - DIM_TICK / 2}
              y1={y2}
              x2={x + DIM_TICK / 2}
              y2={y2}
              stroke={DIM_COLOR}
              strokeWidth={0.5}
            />
            <text
              x={cx}
              y={cy}
              textAnchor="middle"
              fontSize={DIM_TEXT_SIZE}
              fill={DIM_COLOR}
              transform={`rotate(-90, ${cx}, ${cy})`}
              dy={-DIM_TICK}
            >
              {label}
            </text>
          </g>
        );
      })()}
    </svg>
  );
}
