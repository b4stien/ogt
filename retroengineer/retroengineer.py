import math
from collections import defaultdict

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Curve

sqrt2 = math.sqrt(2)
PITCH = 28.0


def load_and_center(step_file):
    """Import a STEP file and center it on the origin."""
    raw = cq.importers.importStep(step_file)
    bb = raw.val().BoundingBox()
    centered = raw.translate((-bb.center.x, -bb.center.y, -bb.center.z))
    bb = centered.val().BoundingBox()
    print(
        f"Loaded {step_file}, centered from ({bb.center.x:.0f}, {bb.center.y:.0f}, {bb.center.z:.0f})"
    )
    print(f"  Bounding box: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}")
    return centered, bb


def extract_center_tile(piece, bb):
    """Cut a single center tile (28x28x6.8) from the piece."""
    cut_box = cq.Workplane("XY").box(PITCH, PITCH, bb.zlen)
    return cq.Workplane("XY").add(piece.val()).intersect(cut_box)


def trace_profile(edges, normalize_y=True, axes=("Y", "Z")):
    """Build adjacency graph from edges and walk a connected path.
    Returns list of (axis0, axis1) points.  *axes* selects which vertex
    attributes to use (default: Y, Z)."""
    ax0, ax1 = axes
    adj = defaultdict(list)
    for edge in edges:
        verts = edge.Vertices()
        a = (round(getattr(verts[0], ax0), 3), round(getattr(verts[0], ax1), 3))
        b = (round(getattr(verts[1], ax0), 3), round(getattr(verts[1], ax1), 3))
        adj[a].append(b)
        adj[b].append(a)

    if not adj:
        return []

    if normalize_y:
        y_min = min(p[0] for p in adj)
        adj_shifted = defaultdict(list)
        for k, vs in adj.items():
            nk = (round(k[0] - y_min, 3), k[1])
            for v in vs:
                nv = (round(v[0] - y_min, 3), v[1])
                adj_shifted[nk].append(nv)
        adj = adj_shifted

    zero_y_pts = [p for p in adj if p[0] == 0.0]
    if not zero_y_pts:
        zero_y_pts = [min(adj.keys())]
    start = max(zero_y_pts, key=lambda p: p[1])

    path = [start]
    visited = {start}
    current = start
    while True:
        neighbors = [n for n in adj[current] if n not in visited]
        if not neighbors:
            break
        current = neighbors[0]
        path.append(current)
        visited.add(current)

    return path


def print_profile(name, path, labels=("Y", "Z")):
    print(f"\n{name} ({len(path)} points):")
    print(f"  {labels[0]:>8s}   {labels[1]:>8s}")
    for a, b in path:
        print(f"  {a:8.3f}   {b:8.3f}")


def retroengineer_tile_inner_walls(center_tile):
    """Analyze the wall profile by slicing the center tile on the YZ plane."""
    print("\n=== Inner wall profile ===")
    print("  This is the YZ cross-section of one of the tile's four walls,")
    print("  taken at X=0 (middle of the wall's length). The profile is")
    print("  symmetric about Z=0 (top and bottom are identical). Y=0 is")
    print("  the outer face of the wall (flat), and Y increases inward")
    print("  toward the tile interior, forming the interlocking lip that")
    print("  accessories clip onto.")

    section = cq.Workplane("YZ").add(center_tile.val()).section(0.0)
    edges = section.val().Edges()

    # Take the negative-Y wall (one half of the tile)
    wall_edges = [e for e in edges if all(v.Y <= -1 for v in e.Vertices())]
    path = trace_profile(wall_edges)
    print_profile("Wall profile", path)

    # Wall positioning context
    print(f"\n  Wall positioning:")
    print(f"    The wall outer face sits at Y = PITCH/2 = {PITCH / 2:.0f}mm from tile center.")
    print(f"    Wall thickness = profile Y value at each Z level:")
    # Deduplicate: keep max thickness per Z level, show only positive Z
    thick_by_z = {}
    for y, z in path:
        z_abs = round(abs(z), 1)
        if z_abs not in thick_by_z or y > thick_by_z[z_abs]:
            thick_by_z[z_abs] = y
    # The wall at Z=0 is between the ±1 points (constant 0.8mm section)
    if 0.0 not in thick_by_z and 1.0 in thick_by_z:
        thick_by_z[0.0] = thick_by_z[1.0]
    for z_abs in sorted(thick_by_z.keys()):
        y = thick_by_z[z_abs]
        if y == 0.0:
            continue  # skip outer-edge zero-thickness entries
        print(
            f"      Z={z_abs:+.1f}: thickness = {y:.1f}mm  →  inner face at Y = {PITCH / 2 - y:.1f}mm"
        )
    print(f"    The profile is symmetric top-to-bottom about Z=0.")

    print(f"\n  FRAME CONSTRUCTION:")
    print(f"    To build one wall of the axis-aligned frame:")
    print(f"    - Use the profile points above as a closed polygon: close from")
    print(f"      the last point back to the first via the outer face (Y=0).")
    print(f"    - Extrude the closed polygon {PITCH:.0f}mm along X (wall length = PITCH).")
    print(f"    - Position the outer face at Y = -PITCH/2 = -{PITCH / 2:.0f}mm from tile center.")
    print(f"    - Rotate copies at 90deg, 180deg, 270deg around Z for all 4 walls.")
    return path


def retroengineer_tile_inner_corners(center_tile):
    """Analyze the corner post profile by rotating the center tile 45° and slicing."""
    print("\n=== Inner corner profile ===")
    print("  This is the cross-section of one of the tile's four corner")
    print("  posts, taken at 45°. To capture its profile, the tile is")
    print("  rotated 45° around Z and then sliced on")
    print("  the YZ plane. Y=0 is the outermost point of the post.")

    rotated = center_tile.rotate((0, 0, 0), (0, 0, 1), 45)
    section = cq.Workplane("YZ").add(rotated.val()).section(0.0)
    edges = section.val().Edges()

    # Take the negative-Y half
    corner_edges = [e for e in edges if all(v.Y <= -1 for v in e.Vertices())]

    path = trace_profile(corner_edges)
    print_profile("Corner profile", path)

    # Corner position relative to tile
    raw_path = trace_profile(corner_edges, normalize_y=False)
    wall_intersection_y = -PITCH / 2 * sqrt2  # -19.799

    if raw_path:
        y_outer = min(p[0] for p in raw_path)
        y_inner = max(p[0] for p in raw_path)
        print(
            f"\n  Corner starts at wall intersection (offset: {y_outer - wall_intersection_y:.3f})"
        )
        extent_xy = (y_inner - wall_intersection_y) / sqrt2
        extent_45 = y_inner - wall_intersection_y
        print(f"  Extends {extent_xy:.3f} inward (X/Y coords)")

        # Break down the extent in the 45° frame where numbers are rounder.
        # The full height of the post is ±3.4 (same as the wall). The flat
        # section is the part at full height; the chamfer tapers off after.
        full_h = max(abs(z) for _, z in path)
        flat_end = max(y for y, z in path if abs(abs(z) - full_h) < 0.01)
        chamfer = max(y for y, _ in path) - flat_end
        print(f"\n  In the 45° frame the extent is {extent_45:.3f}:")
        print(f"    flat section (full height): {flat_end:.3f}")
        print(f"    chamfer taper:              {chamfer:.3f}")
        print(f"  Dividing by sqrt(2) gives the non-round X/Y value {extent_xy:.3f}.")

    print(f"\n  FRAME CONSTRUCTION:")
    print(f"    To build one wall of the 45deg-rotated frame:")
    print(f"    - Use the profile points above as a closed polygon: close from")
    print(f"      the last point back to the first via the outer face (Y=0).")
    print(f"    - Extrude the closed polygon PITCH*sqrt(2) = {PITCH * sqrt2:.1f}mm along X.")
    print(
        f"    - Position the outer face at Y = -PITCH/2*sqrt(2) = -{PITCH / 2 * sqrt2:.1f}mm from tile center."
    )
    print(f"    - Rotate copies at 90deg, 180deg, 270deg around Z for all 4 walls.")
    print(f"    - Rotate the entire 4-wall frame 45deg around Z.")
    print(f"    The intersection of this rotated-square void with the axis-aligned")
    print(f"    square void from the wall frame produces the octagonal cavity.")
    return path


def retroengineer_grid_outer_corners(piece, bb):
    """Analyze the 45° corner cut on the grid perimeter using the top-left tile."""
    print("\n=== Grid outer corner cut (OPTIONAL) ===")
    print("  This is an optional cosmetic feature. A 45° chamfer is cut")
    print("  across each of the four outermost corners of the grid perimeter,")
    print("  removing a small triangle. It is purely aesthetic — not all")
    print("  opengrid boards have it.")

    # Extract top-left tile: center at (-28, 28)
    tl_box = cq.Workplane("XY").transformed(offset=(-PITCH, PITCH, 0)).box(PITCH, PITCH, bb.zlen)
    top_left_tile = cq.Workplane("XY").add(piece.val()).intersect(tl_box)

    # XY section at Z=0 to see the 45° cut
    section = cq.Workplane("XY").add(top_left_tile.val()).section(0.0)
    edges = section.val().Edges()

    # Find the 45° cut edge: a LINE on the outer boundary going from
    # the X=-42 wall to the Y=42 wall at 45°
    for e in edges:
        if e.geomType() == "LINE":
            verts = e.Vertices()
            a, b = verts[0], verts[1]
            # The cut connects two outer walls at 45°
            if (abs(a.X - (-42)) < 0.01 and abs(b.Y - 42) < 0.01) or (
                abs(b.X - (-42)) < 0.01 and abs(a.Y - 42) < 0.01
            ):
                x_on_wall = max(a.X, b.X)  # the X where cut meets Y=42
                y_on_wall = min(a.Y, b.Y)  # the Y where cut meets X=-42
                cut_leg_x = abs(x_on_wall - (-42))
                cut_leg_y = abs(42 - y_on_wall)
                print(f"  45° cut on grid corner (-42, 42):")
                print(f"    Meets X=-42 wall at Y={y_on_wall:.1f} ({cut_leg_y:.1f} from corner)")
                print(f"    Meets Y=42 wall at X={x_on_wall:.1f} ({cut_leg_x:.1f} from corner)")
                print(f"    Leg length: {cut_leg_x:.1f}")
                break


def retroengineer_grid_connectors(piece, bb):
    """Analyze the connector tab on the outer wall between two tiles."""
    print("\n=== Grid connector tab (OPTIONAL) ===")
    print("  This is an optional feature. Semicircular receptacles are cut")
    print("  into the outer walls at tile boundaries. A plastic peg can be")
    print("  inserted to join two separate boards side by side. Not all")
    print("  opengrid boards include these connectors.")

    # Take a 28x14 box on the top edge (Y=42), straddling the tile boundary at X=14
    conn_box = (
        cq.Workplane("XY").transformed(offset=(PITCH / 2, 42 - 7, 0)).box(PITCH, 14, bb.zlen + 1)
    )
    connector = cq.Workplane("XY").add(piece.val()).intersect(conn_box)

    # XY section at Z=0
    section = cq.Workplane("XY").add(connector.val()).section(0.0)
    edges = section.val().Edges()

    # The wall is at the max Y of the bounding box
    wall_y = bb.ymax

    # Find the tab: circle arcs near the tile boundary (X≈14), close to the wall
    tab_edges = [
        e
        for e in edges
        if all(v.Y >= wall_y - 3 for v in e.Vertices())
        and all(abs(v.X - PITCH / 2) <= 4 for v in e.Vertices())
    ]

    # Collect all tab vertices
    tab_points = set()
    for e in tab_edges:
        for v in e.Vertices():
            tab_points.add((round(v.X, 3), round(v.Y, 3)))

    xs = [p[0] for p in tab_points]
    ys = [p[1] for p in tab_points]
    tab_center_x = (min(xs) + max(xs)) / 2
    slot_half_width = (max(xs) - min(xs)) / 2
    depth = max(ys) - min(ys)

    # Classify arcs by radius
    arc_radii = sorted({round(e.radius(), 3) for e in tab_edges if e.geomType() == "CIRCLE"})
    # Smallest = outer fillet, then inner fillet, then bottom arc, largest = connecting arc (tangent-derived)
    outer_fillet_r = arc_radii[0]
    inner_fillet_r = arc_radii[1]
    bottom_arc_r = arc_radii[2]
    connecting_arc_r = arc_radii[3]

    # Connector height: scan Z levels for the tab presence
    tab_z_min = None
    tab_z_max = None
    for z_test in [z / 10 for z in range(-34, 35)]:
        try:
            s = cq.Workplane("XY").add(connector.val()).section(z_test)
            has_tab = any(
                e.geomType() == "CIRCLE"
                and all(abs(v.X - PITCH / 2) <= 4 for v in e.Vertices())
                and all(v.Y >= wall_y - 3 for v in e.Vertices())
                for e in s.val().Edges()
            )
            if has_tab:
                if tab_z_min is None:
                    tab_z_min = z_test
                tab_z_max = z_test
        except Exception:
            pass

    tab_height = tab_z_max - tab_z_min if tab_z_min is not None else 0

    print(f"  Center: X={tab_center_x:.3f} (tile boundary)")
    print(f"  Z extent: {tab_z_min:.1f} to {tab_z_max:.1f} (height: {tab_height:.1f})")
    print(f"  Slot half-width: {slot_half_width:.3f}")
    print(f"  Depth from wall: {depth:.3f}")
    print(f"  Bottom arc radius: {bottom_arc_r:.3f}")
    print(f"  Connecting arc radius: {connecting_arc_r:.3f} (derived from tangency)")
    print(f"  Inner fillet radius: {inner_fillet_r:.3f}")
    print(f"  Outer fillet radius: {outer_fillet_r:.3f}")

    # Edge-by-edge slot profile in WALK ORDER (X=0 at slot center, Y=0 at wall surface)
    # Build adjacency from edge endpoints to chain edges in order
    def vtx_key(v):
        return (round(v.X - tab_center_x, 3), round(v.Y - wall_y, 3))

    edge_adj = defaultdict(list)
    for e in tab_edges:
        verts = e.Vertices()
        a, b = vtx_key(verts[0]), vtx_key(verts[1])
        edge_adj[a].append((b, e))
        edge_adj[b].append((a, e))

    # Start from the leftmost vertex on the wall surface (Y=0, most negative X)
    wall_verts = [(k, k[0]) for k in edge_adj if abs(k[1]) < 0.01]
    if wall_verts:
        start = min(wall_verts, key=lambda t: t[1])[0]
    else:
        start = min(edge_adj.keys())

    ordered_edges = []
    visited_edges = set()
    current = start
    while True:
        found = False
        for neighbor, edge in edge_adj[current]:
            if id(edge) not in visited_edges:
                visited_edges.add(id(edge))
                ordered_edges.append((current, neighbor, edge))
                current = neighbor
                found = True
                break
        if not found:
            break

    print(f"\n  Slot edges in WALK ORDER (X=0 at slot center, Y=0 at wall surface):")
    print(f"  Start at left wall surface, walk clockwise back to right wall surface.")
    for i, (pt_a, pt_b, e) in enumerate(ordered_edges):
        x1, y1 = pt_a
        x2, y2 = pt_b
        if e.geomType() == "CIRCLE":
            adaptor = BRepAdaptor_Curve(e.wrapped)
            circ = adaptor.Circle()
            loc = circ.Location()
            r = round(e.radius(), 3)
            cx = round(loc.X() - tab_center_x, 3)
            cy = round(loc.Y() - wall_y, 3)
            print(
                f"    {i + 1}. ARC  r={r:<7.3f} center=({cx:>7.3f}, {cy:>7.3f})  ({x1:>7.3f}, {y1:>7.3f}) -> ({x2:>7.3f}, {y2:>7.3f})"
            )
        else:
            print(f"    {i + 1}. LINE  ({x1:>7.3f}, {y1:>7.3f}) -> ({x2:>7.3f}, {y2:>7.3f})")

    # Construction hint
    print(f"\n  CONSTRUCTION HINT:")
    print(f"    The slot is symmetric about X=0 (slot center at tile boundary).")
    print(
        f"    It is extruded from Z={tab_z_min:.1f} to Z={tab_z_max:.1f} (height {tab_height:.1f}mm)."
    )
    print(f"    The slot is cut into the outer wall at each tile boundary.")
    print(f"    To build: construct the wire from the ordered edges above,")
    print(f"    close it with a straight line from the last point to the first,")
    print(f"    extrude to {tab_height:.1f}mm, and subtract from the outer wall.")


if __name__ == "__main__":
    piece, bb = load_and_center("opengrid-3x3.step")
    center_tile = extract_center_tile(piece, bb)

    print("\n" + "=" * 60)
    print("OPENGRID CONSTRUCTION OVERVIEW")
    print("=" * 60)
    print(f"""
An opengrid board is an NxM array of square tiles on a {PITCH:.0f}mm pitch.
Each tile is a {PITCH:.0f}x{PITCH:.0f}x6.8mm box with an octagonal through-hole (no floor).
The grid is wall-mounted; bins and accessories clip onto the inner walls.

TWO-FRAME CONSTRUCTION (axis-aligned + 45°-rotated):
  The octagonal void emerges naturally from the intersection of two
  square frames rotated 45° relative to each other — no explicit
  octagon math is needed.

WALLS: Each tile has four walls, one per edge, running the full {PITCH:.0f}mm
  length. The wall cross-section (YZ plane at X=0) is constant along
  the wall's length and symmetric top-to-bottom about Z=0.

CORNER POSTS: The four corners correspond to the walls of the 45°-
  rotated frame. Their profile (visible in a 45° cross-section) has a
  chamfered shape.

TILE ADJACENCY: Each tile has its own complete walls. Adjacent tiles
  sit back-to-back at tile boundaries (no wall merging). To make an
  NxM grid, simply array tiles at {PITCH:.0f}mm pitch.

CADQUERY CONSTRUCTION RECIPE:
  1. Build axis-aligned frame (4 walls from wall profile):
     - Take the wall cross-section (YZ profile), close it back to the
       outer face (Y=0), extrude {PITCH:.0f}mm along X
     - Position outer face at Y = -PITCH/2 = -{PITCH / 2:.0f}mm
     - Duplicate at 90deg, 180deg, 270deg rotations around Z -> 4 walls
  2. Build 45deg-rotated frame (4 walls from corner profile):
     - Take the corner cross-section (YZ profile), close it back to
       the outer face (Y=0), extrude PITCH*sqrt(2) = {PITCH * sqrt2:.1f}mm along X
     - Position outer face at Y = -PITCH/2*sqrt(2) = -{PITCH / 2 * sqrt2:.1f}mm
     - Duplicate at 90deg, 180deg, 270deg rotations around Z -> 4 walls
     - Rotate entire frame 45deg around Z
  3. Union both frames
  4. Intersect with {PITCH:.0f}x{PITCH:.0f}x6.8mm box -> single tile
  5. Array tiles at {PITCH:.0f}mm pitch for NxM grid
  6. Optionally add perimeter corner chamfers and connector tab slots

WHY THIS WORKS:
  Each frame's square void is a rotated square. The intersection of a
  square and a 45deg-rotated square is a regular octagon (at Z levels
  where both frames have equal inset). Since wall and corner profiles
  vary independently with Z, the octagon shape varies per Z level —
  wider lips, narrower waist — all handled automatically.
""")

    retroengineer_tile_inner_walls(center_tile)
    retroengineer_tile_inner_corners(center_tile)
    retroengineer_grid_outer_corners(piece, bb)
    retroengineer_grid_connectors(piece, bb)
