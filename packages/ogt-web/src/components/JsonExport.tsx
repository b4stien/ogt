import { Button } from "@/components/ui/button"
import type { GridPlan } from "@/lib/types"

interface JsonExportProps {
  rows: number
  cols: number
  toGridPlan: () => GridPlan
}

export function JsonExport({ rows, cols, toGridPlan }: JsonExportProps) {
  const getJson = () => JSON.stringify(toGridPlan(), null, 2)

  const handleCopy = () => {
    navigator.clipboard.writeText(getJson())
  }

  const handleDownload = () => {
    const blob = new Blob([getJson()], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "gridplan.json"
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={handleCopy}>
          Copy JSON
        </Button>
        <Button variant="outline" size="sm" onClick={handleDownload}>
          Download JSON
        </Button>
      </div>
      <span className="text-sm text-muted-foreground">
        {rows} row{rows > 1 ? "s" : ""} x {cols} column{cols > 1 ? "s" : ""} · {(rows * 2.8).toFixed(1)} cm x {(cols * 2.8).toFixed(1)} cm
      </span>
    </div>
  )
}
