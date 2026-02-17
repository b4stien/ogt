import { useGridState } from "@/hooks/useGridState";
import { GridSvg } from "@/components/GridSvg";
import { GridFeaturesToolbar } from "@/components/GridToolbar";
import { JsonExport } from "@/components/JsonExport";
import type { ScrewSize } from "@/lib/types";

function ScrewField({
  label,
  field,
  screwSize,
  onChange,
}: {
  label: string;
  field: keyof ScrewSize;
  screwSize: ScrewSize;
  onChange: (s: ScrewSize) => void;
}) {
  return (
    <div className="flex items-center rounded-md border bg-background shadow-xs">
      <span className="flex-none px-3 h-8 flex items-center text-sm font-medium border-r bg-muted text-foreground/60 rounded-l-md">
        {label}
      </span>
      <input
        type="number"
        step="0.1"
        value={screwSize[field]}
        onChange={(e) =>
          onChange({ ...screwSize, [field]: parseFloat(e.target.value) || 0 })
        }
        className="w-16 h-8 px-2 text-sm bg-transparent outline-none"
      />
    </div>
  );
}

export function GridEditor() {
  const state = useGridState(2, 2);

  return (
    <div>
      <div className="flex flex-col gap-6">
        <GridSvg
          tiles={state.tiles}
          summits={state.summits}
          eligibility={state.eligibility}
          onToggleTile={state.toggleTile}
          onToggleConnector={state.toggleConnector}
          onToggleChamfer={state.toggleChamfer}
          onToggleScrew={state.toggleScrew}
          onAddRow={state.addRow}
          onRemoveRow={state.removeRow}
          onAddColumn={state.addColumn}
          onRemoveColumn={state.removeColumn}
        />
        <div className="flex flex-col gap-2 max-w-3xl">
          <div className="inline-flex w-fit h-8 rounded-md border shadow-xs overflow-hidden select-none">
            <button
              type="button"
              onClick={() => state.setOpengridType("full")}
              className={`px-3 flex items-center text-sm font-medium cursor-pointer ${
                state.opengridType === "full"
                  ? "bg-primary text-primary-foreground"
                  : "text-foreground hover:bg-muted"
              }`}
            >
              Full
            </button>
            <button
              type="button"
              onClick={() => state.setOpengridType("lite")}
              className={`px-3 flex items-center text-sm font-medium border-l cursor-pointer ${
                state.opengridType === "lite"
                  ? "bg-primary text-primary-foreground"
                  : "text-foreground hover:bg-muted"
              }`}
            >
              Lite
            </button>
          </div>
          <GridFeaturesToolbar
            onEnableAllConnectors={state.enableAllConnectors}
            onEnableAllChamfers={state.enableAllChamfers}
            onEnableAllScrews={state.enableAllScrews}
            onEnableCornerScrews={state.enableCornerScrews}
            onClearAllConnectors={state.clearAllConnectors}
            onClearAllChamfers={state.clearAllChamfers}
            onClearAllScrews={state.clearAllScrews}
          />
          <div className="flex gap-2">
            <ScrewField
              label="Screw diameter (mm)"
              field="diameter"
              screwSize={state.screwSize}
              onChange={state.setScrewSize}
            />
            <ScrewField
              label="Screw head diameter (mm)"
              field="head_diameter"
              screwSize={state.screwSize}
              onChange={state.setScrewSize}
            />
            <ScrewField
              label="Screw head inset (mm)"
              field="head_inset"
              screwSize={state.screwSize}
              onChange={state.setScrewSize}
            />
          </div>
        </div>
      </div>
      <div className="max-w-3xl">
        <div className="mt-10">
          <JsonExport
            rows={state.rows}
            cols={state.cols}
            opengridType={state.opengridType}
            toGridPlan={state.toGridPlan}
          />
        </div>
        <div className="mt-10 rounded border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-700 flex flex-col gap-2">
          <p>
            <strong>Beta:</strong> This generator is still in beta. Please
            verify its output, inspect the generated STEP/STL file, and do a
            small test print before committing to larger projects.
          </p>
          <p>
            <strong>Grid preview:</strong> Green areas represent material that
            will be printed. When a feature (connector, chamfer, screw hole) is
            enabled, its spot turns light grey to indicate material will be
            removed there. Click on a tile to toggle it on or off, and click on
            a feature spot (connector, chamfer, screw hole) to toggle it
            individually.
          </p>
        </div>
      </div>
    </div>
  );
}
