# `ogt`: openGrid tools

A CadQuery reimplementation of [openGrid](https://github.com/ddanier), a modular storage and organization grid system for 3D printing created by [David Danier](https://github.com/ddanier). `ogt` can be used as a CLI tool or as a Python library to generate customizable grid models with support for holes, chamfers, screws, and connectors.

## Features

- **Full tile** — the standard 28 mm openGrid tile, the building block of every grid
- **Holes** — empty cutouts in the grid layout, letting you shape grids to fit around obstacles
- **Chamfers** — corner cutouts applied to tiles that touch grid edges, for a cleaner finish
- **Screws** — countersunk screw holes, placed at corners only or at all eligible positions
- **Connectors** — keyed cutouts at tile boundaries for connecting multiple grids
- **Export** — output to STL or STEP

## Usage

Run without installing via `uvx`:

```bash
# One-shot: generate a 4x2 grid with connectors and corner screws → STL
uvx ogt generate 4x2 --connectors --screws corners

# Or split into two steps:
# 1. Prepare a plan (JSON)
uvx ogt prepare 4x2 --connectors --tile-chamfers --screws all -o my-grid.json

# 2. Draw geometry from the plan
uvx ogt draw my-grid.json --format step -o my-grid.step
```

## Understanding & contributing

The codebase follows a **prepare + draw** architecture: `prepare` analyzes a layout and produces a pure-data `GridPlan`, then `draw` turns that plan into CadQuery geometry. See [docs/design.md](docs/design.md) for a full explanation.

Dev commands:

```bash
uv run pytest          # tests
uv run ruff check      # lint
uv run ruff format     # format
uv run ty check        # type-check
```

## Credits & inspirations

- **David Danier** — openGrid creator
  — [GitHub](https://github.com/ddanier)
  · [Printables](https://www.printables.com/@DavidD)
  · [MakerWorld](https://makerworld.com/en/@david.d)
- **AndyLevesque** — OpenSCAD implementation: [QuackWorks](https://github.com/AndyLevesque/QuackWorks)
- **Perplexinglabs** — web generator: [opengrid generator](https://gridfinity.perplexinglabs.com/pr/opengrid/0/0)
