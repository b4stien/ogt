import { useGridState } from "@/hooks/useGridState"
import { GridSvg } from "@/components/GridSvg"
import { GridFeaturesToolbar } from "@/components/GridToolbar"
import { JsonExport } from "@/components/JsonExport"

export function GridEditor() {
  const state = useGridState(2, 2)

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
        <GridFeaturesToolbar
          onEnableAllConnectors={state.enableAllConnectors}
          onEnableAllChamfers={state.enableAllChamfers}
          onEnableAllScrews={state.enableAllScrews}
          onEnableCornerScrews={state.enableCornerScrews}
          onClearAllConnectors={state.clearAllConnectors}
          onClearAllChamfers={state.clearAllChamfers}
          onClearAllScrews={state.clearAllScrews}
        />
      </div>
      <div className="mt-10">
        <JsonExport rows={state.rows} cols={state.cols} toGridPlan={state.toGridPlan} />
      </div>
    </div>
  )
}
