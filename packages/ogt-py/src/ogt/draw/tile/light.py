"""openGrid 1x1 light tile

Light variant: 4mm-thick version of the full 6.8mm tile.
Created by cutting the full tile profile at z=2.8mm and shifting down to z=0.

"""

import functools
import math

import cadquery as cq

from ogt.constants import TILE_SIZE

LITE_TILE_THICKNESS = 4.0
_SQRT2 = math.sqrt(2)


def _make_tile_wall() -> cq.Workplane:
    """Axis-aligned wall segment (one side of the square frame)."""
    half_size = TILE_SIZE / 2  # 14

    profile = (
        cq.Workplane("YZ")
        .moveTo(0.0, LITE_TILE_THICKNESS)
        .lineTo(0.0, 0.0)
        .lineTo(0.8, 0.0)
        .lineTo(0.8, 1.6)
        .lineTo(1.5, 2.6)
        .lineTo(1.5, 3.6)
        .lineTo(1.1, LITE_TILE_THICKNESS)
        .close()
        .extrude(TILE_SIZE)
    )

    # Center on X, outer face at Y = -14
    return profile.translate((-half_size, -half_size, 0))


def _make_corner_wall() -> cq.Workplane:
    """45-degree frame wall segment (corner post)."""
    half_size = TILE_SIZE / 2  # 14
    extrude_len = TILE_SIZE * _SQRT2

    profile = (
        cq.Workplane("YZ")
        .moveTo(0.0, LITE_TILE_THICKNESS)
        .lineTo(4.17, LITE_TILE_THICKNESS)
        .lineTo(5.57, 2.6)
        .lineTo(5.57, 0.0)
        .lineTo(0.0, 0.0)
        .close()
        .extrude(extrude_len)
    )

    # Center on X, outer face at Y = -14*sqrt(2)
    return profile.translate((-extrude_len / 2, -half_size * _SQRT2, 0))


@functools.lru_cache(maxsize=1)
def make_opengrid_light_tile() -> cq.Workplane:
    """Build a complete 1x1 openGrid light tile."""
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
