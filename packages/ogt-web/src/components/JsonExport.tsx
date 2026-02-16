import { useCallback, useMemo, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { encode } from "@/lib/compact"
import { TILE_SIZE_CM } from "@/lib/defaults"
import type { GridPlan } from "@/lib/types"

type CopyStatus = "idle" | "copied" | "error"

function useCopyStatus(): [CopyStatus, (text: string) => void] {
  const [status, setStatus] = useState<CopyStatus>("idle")
  const timerRef = useRef<ReturnType<typeof setTimeout>>(null)

  const copy = useCallback((text: string) => {
    if (timerRef.current) clearTimeout(timerRef.current)
    setStatus("copied")
    navigator.clipboard.writeText(text).then(null, () => setStatus("error"))
    timerRef.current = setTimeout(() => setStatus("idle"), 3000)
  }, [])

  return [status, copy]
}

function copyButtonClass(status: CopyStatus) {
  if (status === "copied") return "bg-green-600 text-white hover:bg-green-600 hover:text-white border-green-600"
  if (status === "error") return "bg-red-600 text-white hover:bg-red-600 hover:text-white border-red-600"
  return ""
}

function copyLabel(defaultLabel: string, status: CopyStatus) {
  if (status === "copied") return "Copied"
  if (status === "error") return "Error"
  return defaultLabel
}

interface JsonExportProps {
  rows: number
  cols: number
  toGridPlan: () => GridPlan
}

export function JsonExport({ rows, cols, toGridPlan }: JsonExportProps) {
  const plan = useMemo(() => toGridPlan(), [toGridPlan])
  const compactCode = useMemo(() => encode(plan), [plan])
  const command = `uvx ogt generate ${compactCode}`

  const getJson = () => JSON.stringify(plan, null, 2)

  const [cmdStatus, copyCmd] = useCopyStatus()
  const [jsonStatus, copyJson] = useCopyStatus()

  const handleCopyCommand = () => copyCmd(command)
  const handleCopy = () => copyJson(getJson())

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
      <div className="flex items-center rounded border border-input bg-muted">
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopyCommand}
          className={`rounded-r-none border-0 border-r border-input shadow-none ${copyButtonClass(cmdStatus)}`}
        >
          {copyLabel("Copy command", cmdStatus)}
        </Button>
        <code className="flex-1 px-2 py-1.5 text-xs break-all select-all">
          {command}
        </code>
      </div>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={handleCopy} className={copyButtonClass(jsonStatus)}>
          {copyLabel("Copy JSON", jsonStatus)}
        </Button>
        <Button variant="outline" size="sm" onClick={handleDownload}>
          Download JSON
        </Button>
      </div>
      <span className="text-sm text-muted-foreground">
        {rows} row{rows > 1 ? "s" : ""} x {cols} column{cols > 1 ? "s" : ""} · {(rows * TILE_SIZE_CM).toFixed(1)} cm x {(cols * TILE_SIZE_CM).toFixed(1)} cm
      </span>
    </div>
  )
}
