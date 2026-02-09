"""Naive screw hole cutout geometry."""

import math

import cadquery as cq

from ogt.prepare.types import ScrewSize
from ogt.draw.tile.full import TILE_THICKNESS

SCREW_HEAD_COUNTERSUNK_DEGREE = 90


def make_screw_cutout(screw_size: ScrewSize = ScrewSize()) -> cq.Workplane:
    """Build a single screw hole cutout tool.

    Three-part geometry (bottom to top):
    1. Main cylinder through the full tile thickness.
    2. Countersink cone w SCREW_HEAD_COUNTERSUNK_DEGREE.
    3. Head cylinder at the top.

    """
    main_r = screw_size.diameter / 2
    head_r = screw_size.head_diameter / 2
    countersink_h = math.tan(math.radians(SCREW_HEAD_COUNTERSUNK_DEGREE / 2)) * (head_r - main_r)

    # Main cylinder, full height through tile
    main_cyl = cq.Workplane("XY").circle(main_r).extrude(TILE_THICKNESS)

    # Countersink countersink
    countersink_base_z = TILE_THICKNESS - screw_size.head_inset - countersink_h
    countersink = (
        cq.Workplane("XY")
        .circle(main_r)
        .workplane(offset=countersink_h)
        .circle(head_r)
        .loft()
        .translate((0, 0, countersink_base_z))
    )

    # Head inset cylinder
    head = (
        cq.Workplane("XY")
        .circle(head_r)
        .extrude(screw_size.head_inset)
        .translate((0, 0, TILE_THICKNESS - screw_size.head_inset))
    )

    return main_cyl.union(countersink).union(head)
