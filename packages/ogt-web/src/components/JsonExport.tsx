import { useCallback, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { CadExportButton } from "@/components/StepExportButton";
import { encode } from "@/lib/compact";
import { TILE_THICKNESS } from "@/lib/cad/constants";
import { LITE_TILE_THICKNESS } from "@/lib/cad/tile-light";
import { TILE_SIZE_CM } from "@/lib/defaults";
import type { GridPlan } from "@/lib/types";
import { useWorkerStatus } from "@/hooks/useWorkerStatus";

type CopyStatus = "idle" | "copied" | "error";

function useCopyStatus(): [CopyStatus, (text: string) => void] {
  const [status, setStatus] = useState<CopyStatus>("idle");
  const timerRef = useRef<ReturnType<typeof setTimeout>>(null);

  const copy = useCallback((text: string) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setStatus("copied");
    navigator.clipboard.writeText(text).then(null, () => setStatus("error"));
    timerRef.current = setTimeout(() => setStatus("idle"), 3000);
  }, []);

  return [status, copy];
}

function copyButtonClass(status: CopyStatus) {
  if (status === "copied")
    return "bg-green-600 text-white hover:bg-green-600 hover:text-white border-green-600";
  if (status === "error")
    return "bg-red-600 text-white hover:bg-red-600 hover:text-white border-red-600";
  return "";
}

function copyLabel(defaultLabel: string, status: CopyStatus) {
  if (status === "copied") return "Copied";
  if (status === "error") return "Error";
  return defaultLabel;
}

interface CommandRowProps {
  label: string;
  command: string;
  status: CopyStatus;
  onCopy: () => void;
}

function CommandRow({ label, command, status, onCopy }: CommandRowProps) {
  return (
    <div className="flex items-center rounded border border-input bg-muted">
      <Button
        variant="outline"
        size="sm"
        onClick={onCopy}
        className={`rounded-r-none border-0 border-r border-input shadow-none ${copyButtonClass(status)}`}
      >
        {copyLabel(label, status)}
      </Button>
      <code className="flex-1 px-2 py-1.5 text-xs break-all select-all">
        {command}
      </code>
    </div>
  );
}

interface JsonExportProps {
  rows: number;
  cols: number;
  opengridType: "full" | "lite";
  toGridPlan: () => GridPlan;
}

export function JsonExport({
  rows,
  cols,
  opengridType,
  toGridPlan,
}: JsonExportProps) {
  const workerState = useWorkerStatus();
  const plan = useMemo(() => toGridPlan(), [toGridPlan]);
  const compactCode = useMemo(() => encode(plan), [plan]);
  const uvxCommand = `uvx ogt generate ${compactCode}`;
  const pipxCommand = `pipx run ogt generate ${compactCode}`;

  const [uvxStatus, copyUvx] = useCopyStatus();
  const [pipxStatus, copyPipx] = useCopyStatus();

  const filenameBase = `opengrid-${opengridType === "lite" ? "lite-" : ""}${cols}x${rows}`;

  return (
    <div className="flex flex-col gap-2">
      <span className="text-sm text-muted-foreground">
        {rows} row{rows > 1 ? "s" : ""} x {cols} column{cols > 1 ? "s" : ""} ·{" "}
        {(rows * TILE_SIZE_CM).toFixed(1)} cm x{" "}
        {(cols * TILE_SIZE_CM).toFixed(1)} cm x{" "}
        {opengridType === "lite" ? LITE_TILE_THICKNESS : TILE_THICKNESS} mm
      </span>
      <div className="flex gap-2 items-center">
        <CadExportButton
          format="step"
          toGridPlan={toGridPlan}
          filename={`${filenameBase}.step`}
          disabled={workerState.status !== "ready"}
        />
        <CadExportButton
          format="stl"
          toGridPlan={toGridPlan}
          filename={`${filenameBase}.stl`}
          disabled={workerState.status !== "ready"}
        />
        {workerState.status === "loading" && (
          <span className="text-sm text-muted-foreground">
            Loading CAD engine…
          </span>
        )}
        {workerState.status === "error" && (
          <span className="text-sm text-red-600">{workerState.error}</span>
        )}
      </div>
      <CommandRow
        label="Copy uvx command"
        command={uvxCommand}
        status={uvxStatus}
        onCopy={() => copyUvx(uvxCommand)}
      />
      <CommandRow
        label="Copy pipx command"
        command={pipxCommand}
        status={pipxStatus}
        onCopy={() => copyPipx(pipxCommand)}
      />
    </div>
  );
}
