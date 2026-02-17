import { useCallback, useRef, useState } from "react";
import { generateCAD } from "@/lib/cad-client";
import type { CadFormat } from "@/lib/cad-worker";
import type { GridPlan } from "@/lib/types";

export type ExportStatus = "idle" | "loading" | "done" | "error";

export function useCadExport(format: CadFormat) {
  const [status, setStatus] = useState<ExportStatus>("idle");
  const timerRef = useRef<ReturnType<typeof setTimeout>>(null);

  const trigger = useCallback(
    (plan: GridPlan, filename: string) => {
      if (timerRef.current) clearTimeout(timerRef.current);
      setStatus("loading");

      generateCAD(plan, format).then(
        (blob) => {
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = filename;
          a.click();
          URL.revokeObjectURL(url);

          setStatus("done");
          timerRef.current = setTimeout(() => setStatus("idle"), 3000);
        },
        () => {
          setStatus("error");
          timerRef.current = setTimeout(() => setStatus("idle"), 3000);
        },
      );
    },
    [format],
  );

  return { status, trigger };
}
