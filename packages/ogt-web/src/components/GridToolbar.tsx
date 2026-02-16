import { Button } from "@/components/ui/button"

interface GridFeaturesToolbarProps {
  onEnableAllConnectors: () => void
  onEnableAllChamfers: () => void
  onEnableAllScrews: () => void
  onEnableCornerScrews: () => void
  onClearAllConnectors: () => void
  onClearAllChamfers: () => void
  onClearAllScrews: () => void
}

export function GridFeaturesToolbar({
  onEnableAllConnectors,
  onEnableAllChamfers,
  onEnableAllScrews,
  onEnableCornerScrews,
  onClearAllConnectors,
  onClearAllChamfers,
  onClearAllScrews,
}: GridFeaturesToolbarProps) {
  return (
    <div className="flex flex-wrap gap-4 items-start">
      <div className="flex gap-1">
        <Button variant="outline" size="sm" onClick={onEnableAllConnectors}>
          All connectors
        </Button>
        <Button variant="ghost" size="sm" onClick={onClearAllConnectors}>
          Clear
        </Button>
      </div>

      <div className="flex gap-1">
        <Button variant="outline" size="sm" onClick={onEnableAllChamfers}>
          All chamfers
        </Button>
        <Button variant="ghost" size="sm" onClick={onClearAllChamfers}>
          Clear
        </Button>
      </div>

      <div className="flex gap-1">
        <Button variant="outline" size="sm" onClick={onEnableAllScrews}>
          All screws
        </Button>
        <Button variant="outline" size="sm" onClick={onEnableCornerScrews}>
          Corner screws
        </Button>
        <Button variant="ghost" size="sm" onClick={onClearAllScrews}>
          Clear
        </Button>
      </div>
    </div>
  )
}
