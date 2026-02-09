"""openGrid chamfer cutout

Retroengineered from the original STEP file, see ./retroengineer.

"""

import math

import cadquery as cq

from ogt.draw.tile.full import TILE_THICKNESS as FULL_TILE_THICKNESS

INTERSECTION_DISTANCE = 4.2

TILE_CHAMFER = math.sqrt(INTERSECTION_DISTANCE**2 * 2)
TILE_CHAMFER_CUTOUT = (
    cq.Workplane("XY")
    .rect(TILE_CHAMFER, TILE_CHAMFER)
    .extrude(FULL_TILE_THICKNESS)
    .rotate((0, 0, 0), (0, 0, 1), 45)
    .translate((0, 0, 0))
)
