"""Tile chamfer eligibility computation."""

from ogt.slot import Slot, Tile


def compute_eligible_tile_chamfer_positions(
    layout: list[list[Slot]],
) -> list[list[bool]]:
    """Compute which summit positions are eligible for tile chamfer
    cutouts.

    For an NxM grid, there are (N+1)x(M+1) summits. Summit (i, j) is
    eligible iff exactly one of its 4 neighboring cells is a Tile.

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
            row.append(sum((tl, tr, bl, br)) == 1)
        result.append(row)
    return result
