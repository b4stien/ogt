import { useCallback, useMemo, useState } from "react";
import {
  createEmptyGrid,
  DEFAULT_SCREW_SIZE,
  LITE_DEFAULT_SCREW_SIZE,
  emptySummit,
} from "@/lib/defaults";
import {
  computeAllEligibility,
  computeConnectorDirection,
  computeCornerScrewPositions,
  type Eligibility,
} from "@/lib/eligibility";
import type { GridPlan, ScrewSize, SummitFeatures } from "@/lib/types";

function cloneSummits(summits: SummitFeatures[][]): SummitFeatures[][] {
  return summits.map((row) => row.map((s) => ({ ...s })));
}

function cloneTiles(tiles: boolean[][]): boolean[][] {
  return tiles.map((row) => [...row]);
}

/** Prune summit features that are no longer eligible after a tile change. */
function pruneSummits(
  summits: SummitFeatures[][],
  eligibility: Eligibility,
): SummitFeatures[][] {
  return summits.map((row, i) =>
    row.map((s, j) => ({
      connector_angle: eligibility.connectors[i]?.[j]
        ? s.connector_angle
        : null,
      tile_chamfer: eligibility.chamfers[i]?.[j] ? s.tile_chamfer : false,
      screw: eligibility.screws[i]?.[j] ? s.screw : false,
    })),
  );
}

export function useGridState(initialRows: number, initialCols: number) {
  const [opengridType, setOpengridTypeRaw] = useState<"full" | "lite">("full");
  const [screwSize, setScrewSize] = useState<ScrewSize>({
    ...DEFAULT_SCREW_SIZE,
  });

  const setOpengridType = useCallback((type: "full" | "lite") => {
    setOpengridTypeRaw(type);
    setScrewSize(
      type === "lite" ? LITE_DEFAULT_SCREW_SIZE : DEFAULT_SCREW_SIZE,
    );
  }, []);
  const [tiles, setTiles] = useState<boolean[][]>(
    () => createEmptyGrid(initialRows, initialCols).tiles,
  );
  const [summits, setSummits] = useState<SummitFeatures[][]>(
    () => createEmptyGrid(initialRows, initialCols).summits,
  );

  const rows = tiles.length;
  const cols = tiles[0]?.length ?? 0;

  const eligibility = useMemo(() => computeAllEligibility(tiles), [tiles]);

  const toggleTile = useCallback(
    (r: number, c: number) => {
      const newTiles = cloneTiles(tiles);
      newTiles[r][c] = !newTiles[r][c];
      const newElig = computeAllEligibility(newTiles);
      setTiles(newTiles);
      setSummits((prevS) => pruneSummits(cloneSummits(prevS), newElig));
    },
    [tiles],
  );

  const toggleConnector = useCallback(
    (i: number, j: number) => {
      if (!eligibility.connectors[i]?.[j]) return;
      setSummits((prev) => {
        const next = cloneSummits(prev);
        if (next[i][j].connector_angle !== null) {
          next[i][j].connector_angle = null;
        } else {
          // Use current tiles to compute direction
          next[i][j].connector_angle = computeConnectorDirection(tiles, i, j);
        }
        return next;
      });
    },
    [eligibility, tiles],
  );

  const toggleChamfer = useCallback(
    (i: number, j: number) => {
      if (!eligibility.chamfers[i]?.[j]) return;
      setSummits((prev) => {
        const next = cloneSummits(prev);
        next[i][j].tile_chamfer = !next[i][j].tile_chamfer;
        return next;
      });
    },
    [eligibility],
  );

  const toggleScrew = useCallback(
    (i: number, j: number) => {
      if (!eligibility.screws[i]?.[j]) return;
      setSummits((prev) => {
        const next = cloneSummits(prev);
        next[i][j].screw = !next[i][j].screw;
        return next;
      });
    },
    [eligibility],
  );

  const addRow = useCallback(() => {
    setTiles((prev) => [...prev, Array.from({ length: cols }, () => true)]);
    setSummits((prev) => [
      ...prev,
      Array.from({ length: cols + 1 }, () => emptySummit()),
    ]);
  }, [cols]);

  const removeRow = useCallback(() => {
    if (rows <= 1) return;
    const newTiles = tiles.slice(0, -1);
    const newElig = computeAllEligibility(newTiles);
    setTiles(newTiles);
    setSummits((prevS) => {
      const trimmed = prevS.slice(0, -1);
      return pruneSummits(trimmed, newElig);
    });
  }, [rows, tiles]);

  const addColumn = useCallback(() => {
    setTiles((prev) => prev.map((row) => [...row, true]));
    setSummits((prev) => prev.map((row) => [...row, emptySummit()]));
  }, []);

  const removeColumn = useCallback(() => {
    if (cols <= 1) return;
    const newTiles = tiles.map((row) => row.slice(0, -1));
    const newElig = computeAllEligibility(newTiles);
    setTiles(newTiles);
    setSummits((prevS) => {
      const trimmed = prevS.map((row) => row.slice(0, -1));
      return pruneSummits(trimmed, newElig);
    });
  }, [cols, tiles]);

  const enableAllConnectors = useCallback(() => {
    setSummits((prev) => {
      const next = cloneSummits(prev);
      for (let i = 0; i <= rows; i++) {
        for (let j = 0; j <= cols; j++) {
          if (
            eligibility.connectors[i]?.[j] &&
            next[i][j].connector_angle === null
          ) {
            next[i][j].connector_angle = computeConnectorDirection(tiles, i, j);
          }
        }
      }
      return next;
    });
  }, [rows, cols, eligibility, tiles]);

  const enableAllChamfers = useCallback(() => {
    setSummits((prev) => {
      const next = cloneSummits(prev);
      for (let i = 0; i <= rows; i++) {
        for (let j = 0; j <= cols; j++) {
          if (eligibility.chamfers[i]?.[j]) {
            next[i][j].tile_chamfer = true;
          }
        }
      }
      return next;
    });
  }, [rows, cols, eligibility]);

  const enableAllScrews = useCallback(() => {
    setSummits((prev) => {
      const next = cloneSummits(prev);
      for (let i = 0; i <= rows; i++) {
        for (let j = 0; j <= cols; j++) {
          if (eligibility.screws[i]?.[j]) {
            next[i][j].screw = true;
          }
        }
      }
      return next;
    });
  }, [rows, cols, eligibility]);

  const enableCornerScrews = useCallback(() => {
    const corners = computeCornerScrewPositions(eligibility.screws);
    setSummits((prev) => {
      const next = cloneSummits(prev);
      for (let i = 0; i <= rows; i++) {
        for (let j = 0; j <= cols; j++) {
          if (eligibility.screws[i]?.[j]) {
            next[i][j].screw = !!corners[i]?.[j];
          }
        }
      }
      return next;
    });
  }, [rows, cols, eligibility]);

  const clearAllConnectors = useCallback(() => {
    setSummits((prev) =>
      prev.map((row) => row.map((s) => ({ ...s, connector_angle: null }))),
    );
  }, []);

  const clearAllChamfers = useCallback(() => {
    setSummits((prev) =>
      prev.map((row) => row.map((s) => ({ ...s, tile_chamfer: false }))),
    );
  }, []);

  const clearAllScrews = useCallback(() => {
    setSummits((prev) =>
      prev.map((row) => row.map((s) => ({ ...s, screw: false }))),
    );
  }, []);

  const toGridPlan = useCallback((): GridPlan => {
    return {
      tiles,
      summits,
      opengrid_type: opengridType,
      screw_size: screwSize,
    };
  }, [tiles, summits, opengridType, screwSize]);

  return {
    tiles,
    summits,
    rows,
    cols,
    eligibility,
    opengridType,
    setOpengridType,
    screwSize,
    setScrewSize,
    toggleTile,
    toggleConnector,
    toggleChamfer,
    toggleScrew,
    addRow,
    removeRow,
    addColumn,
    removeColumn,
    enableAllConnectors,
    enableAllChamfers,
    enableAllScrews,
    enableCornerScrews,
    clearAllConnectors,
    clearAllChamfers,
    clearAllScrews,
    toGridPlan,
  };
}
