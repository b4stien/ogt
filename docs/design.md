# Code Design

## Grid

### Slots

A grid is defined by a 2D layout of **slots**. Each slot is either:

- `Tile` — a physical tile is placed there
- `Hole` — empty space (cutout in the grid)

```python
layout = [
    [Tile(), Tile(), Hole()],
    [Tile(), Tile(), Tile()],
]
```

Row 0 is at Y=0, rows go downward (-Y). Col 0 is at X=0, cols go rightward (+X).

### Summits

**Summits** are the intersection points between slots. For an NxM grid of slots, there are (N+1)x(M+1) summits. Each summit touches up to 4 neighboring slots.

Summit features (connectors, chamfers, screws) are decided based on the tile/hole pattern of these 4 neighbors.

#### Summit feature eligibility rules at a glance

| Feature      | Condition on (tl, tr, bl, br)                                    |
| ------------ | ---------------------------------------------------------------- |
| Connector    | Two tiles sharing an edge (horizontal or vertical split pattern) |
| Tile chamfer | Exactly 1 of the 4 neighbors is a Tile                           |
| Screw        | All 4 neighbors are Tiles                                        |

### Coordinate system

A 3x2 grid has 4x3 summits:

Summit `(i, j)` sits at the top-left corner of slot `(i, j)`.
Summit `(i, j)` world position: `x = j * TILE_SIZE`, `y = -i * TILE_SIZE`.

3x2 grid with coordinates :

```
  (0,0)───(0,1)───(0,2)───(0,3)    ← summit coords (row, col)
    │       │       │       │
    │ [0,0] │ [0,1] │ [0,2] │      ← slot coords [row, col]
    │       │       │       │
  (1,0)───(1,1)───(1,2)───(1,3)
    │       │       │       │
    │ [1,0] │ [1,1] │ [1,2] │
    │       │       │       │
  (2,0)───(2,1)───(2,2)───(2,3)
```

## Prepare + Draw

Grid construction is split into two phases:

1. **Prepare** (`prepare/`) — Analyzes the user-provided layout (a 2D array of `Slot` objects) and produces a `GridPlan`: a pure-data description of _what_ to build. No geometry is created. This is where eligibility rules live (which summits get connectors, screws, chamfers).

2. **Draw** (`draw/`) — Takes the `GridPlan` and produces CadQuery geometry. Places tiles, then applies cutouts at summits. No decision logic — it just follows the plan.

```
layout (Slot[][]) ──→ prepare_grid() ──→ GridPlan ──→ draw_grid() ──→ cq.Workplane
```

This separation keeps the geometric code simple and the decision logic testable without running CAD operations.

## Neighbor ordering: top-left, clockwise

When code inspects the 4 slots around a summit `(i, j)`, it always uses this order — starting top-left, then clockwise:

```
  tl │ tr         (i-1, j-1) │ (i-1, j)
  ───┼───    =    ───────────┼──────────
  bl │ br         (i,   j-1) │ (i,   j)
```

```python
tl = is_tile(i - 1, j - 1)   # top-left
tr = is_tile(i - 1, j)       # top-right
bl = is_tile(i, j - 1)       # bottom-left
br = is_tile(i, j)           # bottom-right
```

This convention is consistent across `connectors.py`, `screws.py`, and `tile_chamfers.py`.
