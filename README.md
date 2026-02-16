# `ogt`: openGrid tools

A CadQuery reimplementation of [openGrid](https://github.com/ddanier), a modular storage and organization grid system for 3D printing created by [David Danier](https://github.com/ddanier). `ogt` can be used as a CLI tool, as a Python library, or through its web interface to generate customizable grid models with support for holes, chamfers, screws, and connectors.

## Features

- **Full tile** — the standard 28 mm openGrid tile, the building block of every grid
- **Holes** — empty cutouts in the grid layout, letting you shape grids to fit around obstacles
- **Chamfers** — corner cutouts applied to tiles that touch grid edges, for a cleaner finish
- **Screws** — countersunk screw holes, placed at corners only or at all eligible positions
- **Connectors** — keyed cutouts at tile boundaries for connecting multiple grids
- **Export** — output to STEP or STL

## Project structure

`ogt` is a monorepo with two packages:

| Package          | Path                | Description                                                            |
| ---------------- | ------------------- | ---------------------------------------------------------------------- |
| **ogt** (Python) | `packages/ogt-py/`  | CLI tool and library — prepare grid plans and generate 3D models       |
| **ogt-web**      | `packages/ogt-web/` | Web-based grid editor — visually design grids and export compact codes |

## CLI usage

Run without installing via `uvx`:

```bash
# One-shot: generate a 4x2 grid with connectors and corner screws → STEP
uvx ogt generate --size 4x2 --connectors --screws corners

# Same thing, from a compact code (see below)
uvx ogt generate 0.f.4.2.KlAK._w.f-A

# Or split into two steps:
# 1. Prepare a plan (JSON)
uvx ogt prepare --size 4x2 --connectors --tile-chamfers --screws all -o my-grid.json

# 2. Draw geometry from the plan
uvx ogt draw my-grid.json --format step -o my-grid.step
```

### Compact codes

A compact code encodes an entire grid configuration — dimensions, tile layout, screw sizes, and per-summit features — into a short, shareable string:

```
0.f.2.2.KlAK.8A._4A
```

This is a 2x2 full grid, all tiles present, default screws, all features active. The web editor can produce these codes, which you can then pass straight to the CLI.

See `packages/ogt-py/src/ogt/compact.py` for the full format specification.

## Understanding & contributing

The codebase follows a **prepare + draw** architecture: `prepare` analyzes a layout and produces a pure-data `GridPlan`, then `draw` turns that plan into CadQuery geometry. See [docs/design.md](docs/design.md) for a full explanation.

Each package has its own README with dev commands — see [packages/ogt-py/](packages/ogt-py/) and [packages/ogt-web/](packages/ogt-web/).

## Credits & inspirations

- **David Danier** — openGrid creator
  — [GitHub](https://github.com/ddanier)
  · [Printables](https://www.printables.com/@DavidD)
  · [MakerWorld](https://makerworld.com/en/@david.d)
- **AndyLevesque** — OpenSCAD implementation: [QuackWorks](https://github.com/AndyLevesque/QuackWorks)
- **Perplexinglabs** — web generator: [opengrid generator](https://gridfinity.perplexinglabs.com/pr/opengrid/0/0)
