"""Grid preparation: build a GridPlan from a layout."""

from typing import Literal

from ogt.prepare.connectors import (
    _connector_direction,
    compute_eligible_connector_positions,
)
from ogt.prepare.screws import (
    compute_corner_screw_positions,
    compute_eligible_screw_positions,
)
from ogt.prepare.tile_chamfers import compute_eligible_tile_chamfer_positions
from ogt.prepare.types import (
    LITE_DEFAULT_SCREW_DIAMETER,
    LITE_DEFAULT_SCREW_HEAD_DIAMETER,
    LITE_DEFAULT_SCREW_HEAD_INSET,
    GridPlan,
    ScrewSize,
    SummitFeatures,
)
from ogt.slot import Slot, Tile


def prepare_grid(
    layout: list[list[Slot]],
    opengrid_type: Literal["full", "lite"] = "full",
    connectors: bool = False,
    tile_chamfers: bool = False,
    screws: None | Literal["corners", "all"] = None,
    screw_size: ScrewSize | None = None,
) -> GridPlan:
    """Analyze a layout and produce an exhaustive GridPlan.

    Parameters
    ----------
    layout : list[list[Slot]]
        2D array of Slot objects.
    opengrid_type : ``"full"`` | ``"lite"``
        Which tile variant to use.
    connectors : bool
        Whether to add connector cutouts.
    tile_chamfers : bool
        Whether to add tile chamfer cutouts.
    screws : None | ``"corners"`` | ``"all"``
        Screw placement mode.
    screw_size : ScrewSize | None
        Screw dimensions.  ``None`` uses type-specific defaults.

    Returns
    -------
    GridPlan
    """
    if screw_size is None:
        if opengrid_type == "lite":
            screw_size = ScrewSize(
                diameter=LITE_DEFAULT_SCREW_DIAMETER,
                head_diameter=LITE_DEFAULT_SCREW_HEAD_DIAMETER,
                head_inset=LITE_DEFAULT_SCREW_HEAD_INSET,
            )
        else:
            screw_size = ScrewSize()

    n_rows = len(layout)
    n_cols = len(layout[0])

    # Build tiles bool grid
    tiles = [[isinstance(slot, Tile) for slot in row] for row in layout]

    # Initialize summits
    summits = [[SummitFeatures() for _ in range(n_cols + 1)] for _ in range(n_rows + 1)]

    # Connectors
    if connectors:
        eligible = compute_eligible_connector_positions(layout)
        for i in range(n_rows + 1):
            for j in range(n_cols + 1):
                if eligible[i][j]:
                    summits[i][j].connector_angle = _connector_direction(layout, i, j)

    # Tile chamfers
    if tile_chamfers:
        if screws:
            # When screws are enabled, chamfers apply only at outside grid corners
            corners = [(0, 0), (0, n_cols), (n_rows, 0), (n_rows, n_cols)]
            for ci, cj in corners:
                summits[ci][cj].tile_chamfer = True
        else:
            eligible = compute_eligible_tile_chamfer_positions(layout)
            for i in range(n_rows + 1):
                for j in range(n_cols + 1):
                    if eligible[i][j]:
                        summits[i][j].tile_chamfer = True

    # Screws
    if screws:
        eligible = compute_eligible_screw_positions(layout)
        if screws == "corners":
            placement = compute_corner_screw_positions(eligible)
        else:
            placement = eligible
        for i in range(len(placement)):
            for j in range(len(placement[i])):
                if placement[i][j]:
                    summits[i][j].screw = True

    return GridPlan(
        tiles=tiles,
        summits=summits,
        opengrid_type=opengrid_type,
        screw_size=screw_size,
    )
