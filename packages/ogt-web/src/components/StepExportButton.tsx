import { Button } from "@/components/ui/button";
import { useCadExport, type ExportStatus } from "@/hooks/useStepExport";
import type { CadFormat } from "@/lib/cad-worker";
import type { GridPlan } from "@/lib/types";

function buttonClass(status: ExportStatus) {
  if (status === "done")
    return "bg-green-600 text-white hover:bg-green-600 hover:text-white border-green-600";
  if (status === "error")
    return "bg-red-600 text-white hover:bg-red-600 hover:text-white border-red-600";
  return "";
}

function buttonLabel(format: CadFormat, status: ExportStatus) {
  const label = format.toUpperCase();
  if (status === "loading") return "Generating\u2026";
  if (status === "done") return "Downloaded";
  if (status === "error") return "Error";
  return `Download ${label}`;
}

interface CadExportButtonProps {
  format: CadFormat;
  toGridPlan: () => GridPlan;
  filename: string;
  disabled?: boolean;
}

export function CadExportButton({
  format,
  toGridPlan,
  filename,
  disabled,
}: CadExportButtonProps) {
  const { status, trigger } = useCadExport(format);

  return (
    <Button
      variant="outline"
      size="sm"
      disabled={disabled || status === "loading"}
      className={buttonClass(status)}
      onClick={() => trigger(toGridPlan(), filename)}
    >
      {buttonLabel(format, status)}
    </Button>
  );
}
