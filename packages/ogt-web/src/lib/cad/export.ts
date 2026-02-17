import type { Solid } from "replicad";

export function exportSTEP(shape: Solid): Blob {
  return shape.blobSTEP();
}

export function exportSTL(shape: Solid): Blob {
  return shape.blobSTL();
}
