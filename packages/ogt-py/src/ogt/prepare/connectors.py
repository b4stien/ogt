"""Connector eligibility and direction computation."""

from ogt.slot import Slot, Tile


def _connector_direction(layout: list[list[Slot]], i: int, j: int) -> float:
    """Return Z-rotation (degrees) for the cutout at summit (i, j).

    The cutout's canonical orientation extends in +X. The rotation maps
    it to point into tile material.

    """
    n_rows = len(layout)
    n_cols = len(layout[0])

    def is_tile(r: int, c: int) -> bool:
        if 0 <= r < n_rows and 0 <= c < n_cols:
            return isinstance(layout[r][c], Tile)
        return False

    tl = is_tile(i - 1, j - 1)
    tr = is_tile(i - 1, j)
    bl = is_tile(i, j - 1)
    br = is_tile(i, j)

    # Horizontal edge (top row == each other, bottom row == each other, differ)
    if tl == tr and bl == br and tl != bl:
        if bl:  # tiles below in grid = -Y in world → rotate -90°
            return -90.0
        else:  # tiles above in grid = +Y in world → rotate 90°
            return 90.0

    # Vertical edge (left col == each other, right col == each other, differ)
    if tl == bl and tr == br and tl != tr:
        if tr:  # tiles on right → cutout points +X → rotate 0°
            return 0.0
        else:  # tiles on left → cutout points -X → rotate 180°
            return 180.0

    return 0.0


def compute_eligible_connector_positions(layout: list[list[Slot]]) -> list[list[bool]]:
    """Compute which summit positions are eligible for connectors.

    For an NxM grid, there are (N+1)x(M+1) summits. Summit (i, j) is eligible
    iff its 4 neighbors form a pair of tiles sharing an edge (not diagonal).
    Out-of-bounds neighbors are treated as Hole.
    """
    n_rows = len(layout)
    n_cols = len(layout[0])

    def is_tile(r: int, c: int) -> bool:
        if 0 <= r < n_rows and 0 <= c < n_cols:
            return isinstance(layout[r][c], Tile)
        return False

    result: list[list[bool]] = []
    for i in range(n_rows + 1):
        row: list[bool] = []
        for j in range(n_cols + 1):
            tl = is_tile(i - 1, j - 1)
            tr = is_tile(i - 1, j)
            bl = is_tile(i, j - 1)
            br = is_tile(i, j)
            eligible = (tl == tr and bl == br and tl != bl) or (tl == bl and tr == br and tl != tr)
            row.append(eligible)
        result.append(row)
    return result
