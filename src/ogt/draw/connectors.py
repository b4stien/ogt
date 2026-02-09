"""openGrid connector cutout

Retroengineered from the original STEP file, see ./retroengineer.

"""

import math

import cadquery as cq


CONNECTOR_CUTOUT_HEIGHT = 2.4

_BOTTOM_ARC_R = 2.600
_BOTTOM_ARC_DEPTH = 2.500
_CONNECTING_ARC_R = 2.795
_CONNECTING_ARC_OFFSET = 5.100
_INNER_FILLET_R = 0.500
_OUTER_FILLET_R = 0.250


def _arc_mid(
    cx: float, cy: float, r: float, ax: float, ay: float, bx: float, by: float
) -> tuple[float, float]:
    """Return a point on the shorter arc from A to B on circle (cx, cy, r).

    For semicircles (sweep ≈ pi), picks the arc on the +X side of the center
    to match the profile's outward bulge direction.
    """
    a_ang = math.atan2(ay - cy, ax - cx)
    b_ang = math.atan2(by - cy, bx - cx)
    # CW sweep (negative direction)
    cw = (a_ang - b_ang) % (2 * math.pi)
    # CCW sweep (positive direction)
    ccw = (b_ang - a_ang) % (2 * math.pi)
    if cw < ccw:
        # Shorter arc is CW
        mid = a_ang - cw / 2
    elif ccw < cw:
        # Shorter arc is CCW
        mid = a_ang + ccw / 2
    else:
        # Semicircle: pick the side with larger x (outward from tile wall)
        mid_ccw = a_ang + ccw / 2
        mid_cw = a_ang - cw / 2
        x_ccw = cx + r * math.cos(mid_ccw)
        x_cw = cx + r * math.cos(mid_cw)
        mid = mid_ccw if x_ccw > x_cw else mid_cw
    return (cx + r * math.cos(mid), cy + r * math.sin(mid))


def make_connector_cutout() -> cq.Workplane:
    """Build the connector cutout tool in canonical orientation.

    Canonical orientation: flat face at x=0 (the tile edge), shape
    extends in +X (into tile material), centered on Y, Z from 0 to
    CONNECTOR_CUTOUT_HEIGHT.

    The profile is the exact 9-edge wire extracted from the original
    OpenGrid STEP file, extruded by CONNECTOR_CUTOUT_HEIGHT.
    """
    # Profile vertices in canonical coords (x=depth, y=lateral).
    # Edge table: (type, from, to, center, radius)
    edges = [
        # 1: outer fillet bottom-left
        ("ARC", (0.000, -2.567), (0.275, -2.318), (0.250, -2.567), 0.250),
        # 2: connecting arc (left dimple)
        ("ARC", (0.275, -2.318), (1.156, -2.555), (0.000, -5.100), 2.795),
        # 3: inner fillet bottom
        ("ARC", (1.156, -2.555), (1.363, -2.600), (1.363, -2.100), 0.500),
        # 4: bottom flat
        ("LINE", (1.363, -2.600), (2.500, -2.600), None, None),
        # 5: bottom arc (big semicircle)
        ("ARC", (2.500, -2.600), (2.500, 2.600), (2.500, 0.000), 2.600),
        # 6: top flat
        ("LINE", (2.500, 2.600), (1.363, 2.600), None, None),
        # 7: inner fillet top
        ("ARC", (1.363, 2.600), (1.156, 2.555), (1.363, 2.100), 0.500),
        # 8: connecting arc (right dimple)
        ("ARC", (1.156, 2.555), (0.275, 2.318), (0.000, 5.100), 2.795),
        # 9: outer fillet top-left
        ("ARC", (0.275, 2.318), (0.000, 2.567), (0.250, 2.567), 0.250),
        # 10: closing line
        ("LINE", (0.000, 2.567), (0.000, -2.567), None, None),
    ]

    # Build the wire as a CadQuery sketch on the XY plane, then extrude in Z.
    wp = cq.Workplane("XY").moveTo(0.000, -2.567)

    for kind, _start, end, center, radius in edges:
        if kind == "LINE":
            wp = wp.lineTo(end[0], end[1])
        else:
            assert center is not None
            assert radius is not None
            cx, cy, r = center[0], center[1], radius
            mid = _arc_mid(cx, cy, r, _start[0], _start[1], end[0], end[1])
            wp = wp.threePointArc((mid[0], mid[1]), (end[0], end[1]))

    wp = wp.close().extrude(CONNECTOR_CUTOUT_HEIGHT)
    return wp
