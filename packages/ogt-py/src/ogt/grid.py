"""openGrid NxM grid assembly.

Arranges full tiles into a grid based on a 2D layout of Slot objects.

"""

from typing import Literal

import cadquery as cq

from ogt.draw import draw_grid
from ogt.prepare import prepare_grid
from ogt.prepare.types import ScrewSize
from ogt.slot import Slot


def make_opengrid(
    layout: list[list[Slot]],
    opengrid_type: Literal["full", "light"] = "full",
    connectors: bool = False,
    tile_chamfers: bool = False,
    screws: None | Literal["corners", "all"] = None,
    screw_size: ScrewSize = ScrewSize(),
) -> cq.Workplane:
    """Create an NxM grid of openGrid tiles.

    Parameters
    ----------
    layout : list[list[Slot]]
        2D array of Slot objects. Tile slots place a tile, Hole slots
        leave a gap.
        Row 0 at Y=0, increasing rows go -Y (they go "down").
        Col 0 at X=0, increasing cols go +X (they go "right").
    opengrid_type : ``"full"`` | ``"light"``
        Which tile variant to use.

    Returns
    -------
    cq.Workplane
        Unioned grid of tiles with layout[0][0] top-left corner at the origin.
    """
    plan = prepare_grid(layout, opengrid_type, connectors, tile_chamfers, screws, screw_size)
    return draw_grid(plan)
