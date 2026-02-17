"""Naive screw hole cutout geometry."""

import math

import cadquery as cq

from ogt.prepare.types import ScrewSize

SCREW_HEAD_COUNTERSUNK_DEGREE = 90


def make_screw_cutout(
    screw_size: ScrewSize = ScrewSize(),
    tile_thickness: float = 6.8,
    head_at_bottom: bool = False,
) -> cq.Workplane:
    """Build a single screw hole cutout tool.

    Three-part geometry:
    1. Main cylinder through the full tile thickness.
    2. Countersink cone.
    3. Head (counterbore) cylinder.

    When *head_at_bottom* is False (default), the head sits at the top
    of the tile (full tile orientation).  When True, the head sits at
    the bottom (lite tile orientation).
    """
    main_r = screw_size.diameter / 2
    head_r = screw_size.head_diameter / 2
    countersink_h = math.tan(math.radians(SCREW_HEAD_COUNTERSUNK_DEGREE / 2)) * (head_r - main_r)

    # Main cylinder, full height through tile
    main_cyl = cq.Workplane("XY").circle(main_r).extrude(tile_thickness)

    if head_at_bottom:
        # Head (counterbore) at Z=0
        head = cq.Workplane("XY").circle(head_r).extrude(screw_size.head_inset)

        # Countersink cone above the counterbore (head_r -> main_r going up)
        countersink = (
            cq.Workplane("XY")
            .circle(head_r)
            .workplane(offset=countersink_h)
            .circle(main_r)
            .loft()
            .translate((0, 0, screw_size.head_inset))
        )
    else:
        # Countersink cone near the top (main_r -> head_r going up)
        countersink_base_z = tile_thickness - screw_size.head_inset - countersink_h
        countersink = (
            cq.Workplane("XY")
            .circle(main_r)
            .workplane(offset=countersink_h)
            .circle(head_r)
            .loft()
            .translate((0, 0, countersink_base_z))
        )

        # Head inset cylinder at the top
        head = (
            cq.Workplane("XY")
            .circle(head_r)
            .extrude(screw_size.head_inset)
            .translate((0, 0, tile_thickness - screw_size.head_inset))
        )

    return main_cyl.union(countersink).union(head)
