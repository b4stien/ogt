/**
 * Node.js script to generate STEP/STL files from a compact GridPlan code.
 *
 * Usage:
 *   npx tsx scripts/generate.ts <compact-code> [--format step|stl] [-o output.step]
 */
import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { setOC } from "replicad";
import { decode } from "../src/lib/compact";
import { drawGrid } from "../src/lib/cad/grid";
import { exportSTEP, exportSTL } from "../src/lib/cad/export";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function initOC() {
  // Load the OpenCascade WASM module for Node.js
  const wasmPath = join(
    __dirname,
    "../node_modules/replicad-opencascadejs/src/replicad_single.wasm",
  );

  // Use createRequire for the .js file (Emscripten module)
  const require = createRequire(import.meta.url);
  const mod = require("replicad-opencascadejs/src/replicad_single.js");
  const initOpenCascade = mod.default || mod;

  const OC = await initOpenCascade({
    locateFile: () => wasmPath,
  });

  setOC(OC);
}

function parseArgs(args: string[]) {
  let code: string | null = null;
  let format = "step";
  let output: string | null = null;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--format" && i + 1 < args.length) {
      format = args[++i].toLowerCase();
    } else if (args[i] === "-o" && i + 1 < args.length) {
      output = args[++i];
    } else if (!args[i].startsWith("-")) {
      code = args[i];
    }
  }

  if (!code) {
    console.error(
      "Usage: npx tsx scripts/generate.ts <compact-code> [--format step|stl] [-o output]",
    );
    process.exit(1);
  }

  if (format !== "step" && format !== "stl") {
    console.error(`Invalid format: ${format}. Must be 'step' or 'stl'.`);
    process.exit(1);
  }

  if (!output) {
    output = `opengrid.${format}`;
  }

  return { code, format, output };
}

async function main() {
  const { code, format, output } = parseArgs(process.argv.slice(2));

  console.error("Loading OpenCascade WASM...");
  await initOC();

  console.error(`Decoding compact code: ${code}`);
  const plan = decode(code);

  console.error("Generating geometry...");
  const solid = drawGrid(plan);

  console.error(`Exporting ${format.toUpperCase()}...`);
  const blob = format === "step" ? exportSTEP(solid) : exportSTL(solid);

  const buffer = Buffer.from(await blob.arrayBuffer());
  const outputPath = resolve(output);
  writeFileSync(outputPath, buffer);
  console.error(`Written to ${outputPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
