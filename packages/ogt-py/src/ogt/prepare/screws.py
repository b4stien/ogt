"""Screw hole eligibility computation."""

from ogt.slot import Slot, Tile


def compute_eligible_screw_positions(
    layout: list[list[Slot]],
) -> list[list[bool]]:
    """Compute which summit positions are eligible for screw holes.

    Summit (i, j) is eligible iff all 4 adjacent cells are Tiles.
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
            row.append(tl and tr and bl and br)
        result.append(row)
    return result


def compute_corner_screw_positions(
    eligible: list[list[bool]],
) -> list[list[bool]]:
    """Filter eligible positions to only corner screws.

    A summit is a corner if it is eligible and has no pass-through on
    any axis — i.e., it does NOT have both neighbors on the same axis
    eligible (not both left+right, and not both up+down).
    Out-of-bounds counts as not eligible.

    """
    n_rows = len(eligible)
    n_cols = len(eligible[0])

    def is_eligible(r: int, c: int) -> bool:
        if 0 <= r < n_rows and 0 <= c < n_cols:
            return eligible[r][c]
        return False

    result: list[list[bool]] = []
    for i in range(n_rows):
        row: list[bool] = []
        for j in range(n_cols):
            if not eligible[i][j]:
                row.append(False)
                continue
            # Pass-through on an axis = both neighbors on that axis are eligible
            h_through = is_eligible(i, j - 1) and is_eligible(i, j + 1)
            v_through = is_eligible(i - 1, j) and is_eligible(i + 1, j)
            row.append(not h_through and not v_through)
        result.append(row)
    return result
