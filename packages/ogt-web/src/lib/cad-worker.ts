import { setOC } from "replicad";
import opencascadeModule from "replicad-opencascadejs/src/replicad_single.js";
import wasmUrl from "replicad-opencascadejs/src/replicad_single.wasm?url";
import { drawGrid } from "./cad/grid";
import { exportSTEP, exportSTL } from "./cad/export";
import type { GridPlan } from "./types";

export type CadFormat = "step" | "stl";

export type WorkerMessage = {
  type: "generate";
  id: number;
  plan: GridPlan;
  format: CadFormat;
};

export type WorkerResponse =
  | { type: "ready" }
  | { type: "init-error"; error: string }
  | { type: "result"; id: number; data: ArrayBuffer }
  | { type: "error"; id: number; error: string };

async function initOC() {
  // The .d.ts declares init() with no args, but the Emscripten JS accepts { locateFile }
  const init = opencascadeModule as unknown as (opts: {
    locateFile: () => string;
  }) => ReturnType<typeof opencascadeModule>;
  const OC = await init({ locateFile: () => wasmUrl });
  setOC(OC);
}

// Start loading WASM immediately
initOC().then(
  () => {
    self.postMessage({ type: "ready" } satisfies WorkerResponse);
  },
  (err) => {
    self.postMessage({
      type: "init-error",
      error: `WASM init failed: ${err}`,
    } satisfies WorkerResponse);
  },
);

self.onmessage = (e: MessageEvent<WorkerMessage>) => {
  const msg = e.data;
  if (msg.type === "generate") {
    const { id } = msg;
    try {
      const solid = drawGrid(msg.plan);
      const blob = msg.format === "stl" ? exportSTL(solid) : exportSTEP(solid);
      blob.arrayBuffer().then(
        (buf) => {
          self.postMessage(
            { type: "result", id, data: buf } satisfies WorkerResponse,
            { transfer: [buf] },
          );
        },
        (err) => {
          self.postMessage({
            type: "error",
            id,
            error: `Export failed: ${err}`,
          } satisfies WorkerResponse);
        },
      );
    } catch (err) {
      self.postMessage({
        type: "error",
        id,
        error: `Generation failed: ${err}`,
      } satisfies WorkerResponse);
    }
  }
};
