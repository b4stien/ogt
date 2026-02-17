import { useSyncExternalStore } from "react";
import { getWorkerStatus, subscribeWorkerStatus } from "@/lib/cad-client";

export function useWorkerStatus() {
  return useSyncExternalStore(subscribeWorkerStatus, getWorkerStatus);
}
