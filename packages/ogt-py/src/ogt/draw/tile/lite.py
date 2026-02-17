"""openGrid 1x1 lite tile

Lite variant: 4mm-thick version of the full 6.8mm tile.
Retroengineered from the original STEP file, see ./retroengineer.

Construction: same two-frame union as the full tile (axis-aligned walls +
45-degree-rotated corner posts), clipped to the tile footprint.  The corner
post geometry is identical to the full tile, just truncated at 4mm height.
The wall profile is NOT symmetric in Z: the bottom (Z=0) has the accessory
clip lip, the top (Z=4.0) is a plain 0.8mm wall.

"""

import functools
import math

import cadquery as cq

from ogt.constants import TILE_SIZE

LITE_TILE_THICKNESS = 4.0
_SQRT2 = math.sqrt(2)


def _make_tile_wall() -> cq.Workplane:
    """Axis-aligned wall segment (one side of the square frame).

    Profile (YZ, Z=0 at bottom):
        (0, 4.0) -> (0, 0) -> (1.1, 0) -> (1.5, 0.4) -> (1.5, 1.4)
        -> (0.8, 2.4) -> (0.8, 4.0) -> close

    NOT symmetric in Z: bottom has the clip lip, top is a plain 0.8mm wall.
    """
    half_size = TILE_SIZE / 2  # 14

    profile = (
        cq.Workplane("YZ")
        .moveTo(0.0, LITE_TILE_THICKNESS)
        .lineTo(0.0, 0.0)
        .lineTo(1.1, 0.0)
        .lineTo(1.5, 0.4)
        .lineTo(1.5, 1.4)
        .lineTo(0.8, 2.4)
        .lineTo(0.8, LITE_TILE_THICKNESS)
        .close()
        .extrude(TILE_SIZE)
    )

    # Center on X, outer face at Y = -14
    return profile.translate((-half_size, -half_size, 0))


def _make_corner_wall() -> cq.Workplane:
    """45-degree frame wall segment (corner post).

    Same geometry as the full tile corner post, just truncated at 4mm.
    The bottom taper is 1.4 x 1.4 in the 45-degree frame.

    Profile (YZ, Z=0 at bottom):
        (0, 4.0) -> (5.57, 4.0) -> (5.57, 1.4) -> (4.17, 0) -> (0, 0) -> close
    """
    half_size = TILE_SIZE / 2  # 14
    extrude_len = TILE_SIZE * _SQRT2

    profile = (
        cq.Workplane("YZ")
        .moveTo(0.0, LITE_TILE_THICKNESS)
        .lineTo(5.57, LITE_TILE_THICKNESS)
        .lineTo(5.57, 1.4)
        .lineTo(4.17, 0.0)
        .lineTo(0.0, 0.0)
        .close()
        .extrude(extrude_len)
    )

    # Center on X, outer face at Y = -14*sqrt(2)
    return profile.translate((-extrude_len / 2, -half_size * _SQRT2, 0))


@functools.lru_cache(maxsize=1)
def make_opengrid_lite_tile() -> cq.Workplane:
    """Build a complete 1x1 openGrid lite tile."""
    # Axis-aligned frame: 4 walls at 0, 90, 180, 270
    wall = _make_tile_wall()
    axis_frame = wall
    for angle in (90, 180, 270):
        axis_frame = axis_frame.union(wall.rotate((0, 0, 0), (0, 0, 1), angle))

    # 45-degree frame: 4 corner walls, then rotate entire frame 45
    corner = _make_corner_wall()
    diag_frame = corner
    for angle in (90, 180, 270):
        diag_frame = diag_frame.union(corner.rotate((0, 0, 0), (0, 0, 1), angle))
    diag_frame = diag_frame.rotate((0, 0, 0), (0, 0, 1), 45)

    # Union both frames
    tile = axis_frame.union(diag_frame)

    # Intersect with bounding box to clip to tile footprint
    bbox = (
        cq.Workplane("XY")
        .box(TILE_SIZE, TILE_SIZE, LITE_TILE_THICKNESS)
        .translate((0, 0, LITE_TILE_THICKNESS / 2))
    )
    tile = tile.intersect(bbox)

    return tile
