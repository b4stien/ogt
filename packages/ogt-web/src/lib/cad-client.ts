import type { CadFormat, WorkerMessage, WorkerResponse } from "./cad-worker";
import type { GridPlan } from "./types";

export type WorkerStatus = "loading" | "ready" | "error";

export interface WorkerSnapshot {
  status: WorkerStatus;
  error?: string;
}

// --- Worker instance ---

const worker = new Worker(new URL("./cad-worker.ts", import.meta.url), {
  type: "module",
});

// --- Status tracking (useSyncExternalStore-compatible) ---

let snapshot: WorkerSnapshot = { status: "loading" };
const listeners = new Set<() => void>();

/** Transition from "loading" to "ready" or "error" (one-shot). */
function setStatus(status: WorkerStatus, error?: string) {
  if (snapshot.status !== "loading") return;
  snapshot = { status, error };
  for (const fn of listeners) fn();
}

// If the worker doesn't become ready within 30 s, surface an error.
setTimeout(
  () => setStatus("error", "CAD engine timed out while loading"),
  30_000,
);

export function getWorkerStatus(): WorkerSnapshot {
  return snapshot;
}

export function subscribeWorkerStatus(callback: () => void): () => void {
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
  };
}

// --- ID-correlated request/response ---

let nextId = 1;
const pending = new Map<
  number,
  {
    resolve: (blob: Blob) => void;
    reject: (err: Error) => void;
    mimeType: string;
  }
>();

worker.addEventListener("message", (e: MessageEvent<WorkerResponse>) => {
  const msg = e.data;
  switch (msg.type) {
    case "ready":
      setStatus("ready");
      break;
    case "init-error":
      setStatus("error", msg.error);
      break;
    case "result": {
      const p = pending.get(msg.id);
      if (p) {
        pending.delete(msg.id);
        p.resolve(new Blob([msg.data], { type: p.mimeType }));
      }
      break;
    }
    case "error": {
      const p = pending.get(msg.id);
      if (p) {
        pending.delete(msg.id);
        p.reject(new Error(msg.error));
      }
      break;
    }
  }
});

worker.addEventListener("error", () => {
  setStatus("error", "CAD engine failed to load");
});

// --- Public API ---

function waitForReady(): Promise<void> {
  if (snapshot.status === "ready") return Promise.resolve();
  if (snapshot.status === "error") {
    return Promise.reject(
      new Error(snapshot.error ?? "CAD engine failed to initialize"),
    );
  }
  return new Promise((resolve, reject) => {
    const unsub = subscribeWorkerStatus(() => {
      if (snapshot.status === "ready") {
        unsub();
        resolve();
      } else if (snapshot.status === "error") {
        unsub();
        reject(new Error(snapshot.error ?? "CAD engine failed to initialize"));
      }
    });
  });
}

export async function generateCAD(
  plan: GridPlan,
  format: CadFormat,
): Promise<Blob> {
  await waitForReady();

  const id = nextId++;
  const mimeType = format === "stl" ? "model/stl" : "application/step";

  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject, mimeType });
    worker.postMessage({
      type: "generate",
      id,
      plan,
      format,
    } satisfies WorkerMessage);
  });
}
