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
    print(f"  Z range: {bb.zmin:.1f} to {bb.zmax:.1f}")
    return centered, bb


def extract_center_tile(piece, bb):
    """Cut a single center tile (28x28) from the piece.

    For the 5x5 lite grid, the center tile at (0,0) has no screw holes,
    making it ideal for profile analysis.
    """
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


def shift_z(path, z_offset):
    """Shift Z values in a profile path by z_offset (to convert from centered to Z=0 at bottom)."""
    return [(y, round(z + z_offset, 3)) for y, z in path]


def retroengineer_tile_inner_walls(center_tile, z_min):
    """Analyze the wall profile by slicing the center tile on the YZ plane."""
    print("\n=== Inner wall profile ===")
    print("  This is the YZ cross-section of one of the tile's four walls,")
    print("  taken at X=0 (middle of the wall's length). Unlike the full tile,")
    print("  the lite profile is NOT symmetric about the Z midplane: the bottom")
    print("  (Z=0) has the interlocking lip; the top is a plain wall.")

    section = cq.Workplane("YZ").add(center_tile.val()).section(0.0)
    edges = section.val().Edges()

    # Take the negative-Y wall (one half of the tile)
    wall_edges = [e for e in edges if all(v.Y <= -1 for v in e.Vertices())]
    path = trace_profile(wall_edges)

    print_profile("Wall profile (raw, Z-centered)", path)

    # Shift Z so Z=0 is at the bottom (for CadQuery construction)
    shifted = shift_z(path, -z_min)
    print_profile("Wall profile (shifted, Z=0 at bottom)", shifted)

    # Wall positioning context
    tile_thickness = round(-2 * z_min, 1)
    print(f"\n  Wall positioning:")
    print(f"    The wall outer face sits at Y = PITCH/2 = {PITCH / 2:.0f}mm from tile center.")
    print(f"    Wall thickness = profile Y value at each Z level (shifted):")
    thick_by_z = {}
    for y, z in shifted:
        z_r = round(z, 1)
        if z_r not in thick_by_z or y > thick_by_z[z_r]:
            thick_by_z[z_r] = y
    for z_level in sorted(thick_by_z.keys()):
        y = thick_by_z[z_level]
        if y == 0.0:
            continue
        print(
            f"      Z={z_level:.1f}: thickness = {y:.1f}mm  ->  inner face at Y = {PITCH / 2 - y:.1f}mm"
        )
    print(f"    NOTE: The profile is NOT symmetric in Z. The bottom (Z=0) has the")
    print(f"    accessory clip lip; the top (Z={tile_thickness}) is a plain 0.8mm wall.")

    print(f"\n  FRAME CONSTRUCTION:")
    print(f"    To build one wall of the axis-aligned frame:")
    print(f"    - Use the SHIFTED profile points as a closed polygon: close from")
    print(f"      the last point back to the first via the outer face (Y=0).")
    print(f"    - Extrude the closed polygon {PITCH:.0f}mm along X (wall length = PITCH).")
    print(f"    - Position the outer face at Y = -PITCH/2 = -{PITCH / 2:.0f}mm from tile center.")
    print(f"    - Rotate copies at 90deg, 180deg, 270deg around Z for all 4 walls.")
    return shifted


def retroengineer_tile_inner_corners(center_tile, z_min):
    """Analyze the corner post profile by rotating the center tile 45 deg and slicing."""
    print("\n=== Inner corner profile ===")
    print("  This is the cross-section of one of the tile's four corner")
    print("  posts, taken at 45 deg. To capture its profile, the tile is")
    print("  rotated 45 deg around Z and then sliced on the YZ plane.")
    print("  Y=0 is the outermost point of the post.")

    rotated = center_tile.rotate((0, 0, 0), (0, 0, 1), 45)
    section = cq.Workplane("YZ").add(rotated.val()).section(0.0)
    edges = section.val().Edges()

    # Take the negative-Y half
    corner_edges = [e for e in edges if all(v.Y <= -1 for v in e.Vertices())]

    path = trace_profile(corner_edges)
    print_profile("Corner profile (raw, Z-centered)", path)

    # Shift Z
    shifted = shift_z(path, -z_min)
    print_profile("Corner profile (shifted, Z=0 at bottom)", shifted)

    # Corner position relative to tile
    raw_path = trace_profile(corner_edges, normalize_y=False)
    wall_intersection_y = -PITCH / 2 * sqrt2  # -19.799

    if raw_path:
        y_outer = min(p[0] for p in raw_path)
        y_inner = max(p[0] for p in raw_path)
        recess = y_outer - wall_intersection_y
        extent_45 = y_inner - y_outer
        extent_xy = extent_45 / sqrt2

        print(f"\n  Corner post outer face position:")
        print(f"    Full tile diagonal boundary: Y = -PITCH/2*sqrt(2) = {wall_intersection_y:.3f}")
        print(f"    Lite corner outer face at: Y = {y_outer:.3f}")
        print(f"    Recess from boundary: {abs(recess):.3f}")
        if abs(recess) < 0.01:
            print(f"    -> Corner is at the FULL diagonal boundary (same as full tile, NO recess)")
        else:
            print(f"    -> Corner is recessed {abs(recess):.3f}mm inward from boundary")

        # Break down extent into flat section + bottom taper.
        # Unlike the full tile (symmetric, taper at both top and bottom),
        # the lite profile is asymmetric: taper at the BOTTOM only.
        # At the top (Z=4.0), the corner is at full width.
        # At the bottom (Z=0), it's narrower due to the taper.
        tile_thickness = round(-2 * z_min, 1)
        max_y = max(y for y, _ in shifted)
        min_z_at_max_y = min(z for y, z in shifted if abs(y - max_y) < 0.01)
        # Width at the bottom (Z=0)
        bottom_y = max(y for y, z in shifted if abs(z) < 0.01 and y > 0)
        taper_45 = max_y - bottom_y
        taper_xy = taper_45 / sqrt2
        taper_z = min_z_at_max_y  # Z height where max width starts

        print(f"\n  Corner post dimensions (in 45deg frame, as measured):")
        print(f"    Width at top (Z={tile_thickness}): {max_y:.3f} (full extent)")
        print(f"    Width at bottom (Z=0):    {bottom_y:.3f} (after taper)")
        print(f"    Bottom taper:             {taper_45:.3f} in Y x {taper_z:.3f} in Z")

        print(f"\n  Corner post dimensions (in X/Y coords, / sqrt(2)):")
        print(f"    Width at top:             {max_y / sqrt2:.3f}")
        print(f"    Width at bottom:          {bottom_y / sqrt2:.3f}")
        print(f"    Bottom taper:             {taper_xy:.3f} in Y x {taper_z:.3f} in Z")

        print(f"\n  ROUND-NUMBER INTERPRETATION:")
        print(f"    The bottom taper is {taper_45:.1f} x {taper_z:.1f} in the 45deg frame")
        print(f"    = {taper_xy:.3f} x {taper_z:.1f} in X/Y -> ~{round(taper_xy, 1)} x {taper_z:.1f} taper")
        print(f"    The full width {max_y:.3f} in the 45deg frame")
        print(f"    = {max_y / sqrt2:.3f} in X/Y (not a round number because")
        print(f"    the designer works in the 45deg frame)")
        print(f"    The bottom width {bottom_y:.3f} in the 45deg frame")
        print(f"    = {bottom_y / sqrt2:.3f} in X/Y")

    print(f"\n  FRAME CONSTRUCTION:")
    print(f"    To build one wall of the 45deg-rotated frame:")
    print(f"    - Use the SHIFTED profile points as a closed polygon: close from")
    print(f"      the last point back to the first via the outer face (Y=0).")
    print(f"    - Extrude the closed polygon PITCH*sqrt(2) = {PITCH * sqrt2:.1f}mm along X.")
    if abs(recess) < 0.01:
        print(f"    - Position the outer face at Y = -PITCH/2*sqrt(2) = -{PITCH / 2 * sqrt2:.1f}mm")
        print(f"      (same as full tile, no recess).")
    else:
        print(f"    - Position the outer face at Y = -(PITCH/2*sqrt(2) - {abs(recess):.3f})")
    print(f"    - Rotate copies at 90deg, 180deg, 270deg around Z for all 4 walls.")
    print(f"    - Rotate the entire 4-wall frame 45deg around Z.")
    return shifted


def retroengineer_corner_pockets(center_tile, z_min, z_max):
    """Check whether corner pockets exist.

    If the corner post reaches the full tile diagonal boundary, no pockets
    are needed. If it's recessed, pockets with variable-radius fillets
    clean up the excess wall material at the corners.
    """
    print("\n=== Corner pockets ===")
    print("  Checking whether the tile corners have filleted pockets...")

    # Analyze the pocket at the SW corner (-14, -14) by taking XY sections
    # at various Z levels within the actual Z range
    corner_box = (
        cq.Workplane("XY")
        .transformed(offset=(-PITCH / 2 + 3, -PITCH / 2 + 3, 0))
        .box(8, 8, 10)
    )
    corner_region = cq.Workplane("XY").add(center_tile.val()).intersect(corner_box)

    z_radii = []
    # Scan the actual Z range of the centered STEP
    for z_int in range(int(z_min * 10), int(z_max * 10) + 1):
        z = z_int / 10.0
        try:
            s = cq.Workplane("XY").add(corner_region.val()).section(z)
            edges = s.val().Edges()
            arcs = [e for e in edges if e.geomType() == "CIRCLE"]
            if arcs:
                for arc in arcs:
                    r = round(arc.radius(), 3)
                    z_radii.append((z, r))
                    break
        except Exception:
            pass

    if z_radii:
        print(f"\n  Pocket fillet radii found:")
        print(f"  {'Z (raw)':>8s}   {'Z (shifted)':>11s}   {'Radius':>8s}")
        for z, r in z_radii:
            print(f"  {z:8.2f}   {z - z_min:11.2f}   {r:8.3f}")
    else:
        print(f"\n  FINDING: No corner pocket fillets found.")
        print(f"    The corner posts extend to the full tile boundary,")
        print(f"    so no corner pockets are needed.")
        print(f"    (This means the lite tile corner geometry is the same as")
        print(f"    the full tile, just truncated at the lite thickness.)")


def retroengineer_grid_outer_corners(piece, bb):
    """Analyze the 45 deg corner cut on the grid perimeter using a corner tile."""
    print("\n=== Grid outer corner cut (OPTIONAL) ===")
    print("  This is an optional cosmetic feature. A 45 deg chamfer is cut")
    print("  across each of the four outermost corners of the grid perimeter.")

    # For a 5x5 grid, the outermost tiles are at +-2*PITCH from center
    offset_x = -2 * PITCH
    offset_y = 2 * PITCH
    tl_box = (
        cq.Workplane("XY")
        .transformed(offset=(offset_x, offset_y, 0))
        .box(PITCH, PITCH, bb.zlen)
    )
    top_left_tile = cq.Workplane("XY").add(piece.val()).intersect(tl_box)

    # XY section at Z=0 to see the 45 deg cut
    section = cq.Workplane("XY").add(top_left_tile.val()).section(0.0)
    edges = section.val().Edges()

    # Find the 45 deg cut edge on the outer corner
    outer_x = offset_x - PITCH / 2  # -70
    outer_y = offset_y + PITCH / 2  # 70
    for e in edges:
        if e.geomType() == "LINE":
            verts = e.Vertices()
            a, b = verts[0], verts[1]
            if (abs(a.X - outer_x) < 0.01 and abs(b.Y - outer_y) < 0.01) or (
                abs(b.X - outer_x) < 0.01 and abs(a.Y - outer_y) < 0.01
            ):
                x_on_wall = max(a.X, b.X)
                y_on_wall = min(a.Y, b.Y)
                cut_leg_x = abs(x_on_wall - outer_x)
                cut_leg_y = abs(outer_y - y_on_wall)
                print(f"  45 deg cut on grid corner ({outer_x:.0f}, {outer_y:.0f}):")
                print(f"    Meets X={outer_x:.0f} wall at Y={y_on_wall:.1f} ({cut_leg_y:.1f} from corner)")
                print(f"    Meets Y={outer_y:.0f} wall at X={x_on_wall:.1f} ({cut_leg_x:.1f} from corner)")
                print(f"    Leg length: {cut_leg_x:.1f}")
                break
    else:
        print("  No 45 deg corner cut found on the grid perimeter.")


def retroengineer_grid_connectors(piece, bb):
    """Analyze the connector tab on the outer wall between two tiles."""
    print("\n=== Grid connector tab (OPTIONAL) ===")
    print("  Semicircular receptacles cut into the outer walls at tile")
    print("  boundaries for joining two boards side by side.")

    wall_y = bb.ymax
    conn_box = (
        cq.Workplane("XY")
        .transformed(offset=(PITCH / 2, wall_y - 7, 0))
        .box(PITCH, 14, bb.zlen + 1)
    )
    connector = cq.Workplane("XY").add(piece.val()).intersect(conn_box)

    # XY section at Z=0
    section = cq.Workplane("XY").add(connector.val()).section(0.0)
    edges = section.val().Edges()

    tab_edges = [
        e
        for e in edges
        if all(v.Y >= wall_y - 3 for v in e.Vertices())
        and all(abs(v.X - PITCH / 2) <= 4 for v in e.Vertices())
    ]

    if not tab_edges:
        print("  No connector tab found.")
        return

    tab_points = set()
    for e in tab_edges:
        for v in e.Vertices():
            tab_points.add((round(v.X, 3), round(v.Y, 3)))

    xs = [p[0] for p in tab_points]
    ys = [p[1] for p in tab_points]
    tab_center_x = (min(xs) + max(xs)) / 2
    slot_half_width = (max(xs) - min(xs)) / 2
    depth = max(ys) - min(ys)

    arc_radii = sorted({round(e.radius(), 3) for e in tab_edges if e.geomType() == "CIRCLE"})
    if len(arc_radii) >= 4:
        outer_fillet_r = arc_radii[0]
        inner_fillet_r = arc_radii[1]
        bottom_arc_r = arc_radii[2]
        connecting_arc_r = arc_radii[3]
    else:
        print(f"  Found {len(arc_radii)} arc radii: {arc_radii}")
        for i, r in enumerate(arc_radii):
            print(f"    Arc radius {i + 1}: {r:.3f}")

    # Connector height: scan Z levels (use actual Z range)
    tab_z_min = None
    tab_z_max = None
    for z_test in [z / 10 for z in range(int(bb.zmin * 10), int(bb.zmax * 10) + 1)]:
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

    if tab_z_min is not None:
        tab_height = tab_z_max - tab_z_min
        print(f"  Center: X={tab_center_x:.3f} (tile boundary)")
        print(f"  Z extent (raw): {tab_z_min:.1f} to {tab_z_max:.1f} (height: {tab_height:.1f})")
        print(f"  Z extent (shifted): {tab_z_min - bb.zmin:.1f} to {tab_z_max - bb.zmin:.1f}")
        print(f"  Slot half-width: {slot_half_width:.3f}")
        print(f"  Depth from wall: {depth:.3f}")
        if len(arc_radii) >= 4:
            print(f"  Bottom arc radius: {bottom_arc_r:.3f}")
            print(f"  Connecting arc radius: {connecting_arc_r:.3f}")
            print(f"  Inner fillet radius: {inner_fillet_r:.3f}")
            print(f"  Outer fillet radius: {outer_fillet_r:.3f}")

    # Edge-by-edge slot profile in WALK ORDER
    def vtx_key(v):
        return (round(v.X - tab_center_x, 3), round(v.Y - wall_y, 3))

    edge_adj = defaultdict(list)
    for e in tab_edges:
        verts = e.Vertices()
        a, b = vtx_key(verts[0]), vtx_key(verts[1])
        edge_adj[a].append((b, e))
        edge_adj[b].append((a, e))

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


def retroengineer_grid_screws(piece, bb):
    """Analyze screw hole geometry on the lite grid.

    The lite grid has screw holes at each summit (grid intersection).
    In summit notation, the first hole is at (1,1). The center tile of a
    5x5 grid is at tile (2,2)-(3,3), so it has no screw holes, but the
    surrounding tiles do.
    """
    print("\n=== Screw holes ===")
    print("  The lite grid has screw holes at summit positions (grid vertices).")
    print("  In a 5x5 grid, screws are at summits (1,1) through (4,4).")

    # Take a tile that has a screw hole: tile at (1,1) = center at (PITCH, PITCH)
    tile_with_screw_box = (
        cq.Workplane("XY")
        .transformed(offset=(PITCH, PITCH, 0))
        .box(PITCH, PITCH, bb.zlen)
    )
    tile_with_screw = cq.Workplane("XY").add(piece.val()).intersect(tile_with_screw_box)

    # XY section at Z=0 to find the hole
    section = cq.Workplane("XY").add(tile_with_screw.val()).section(0.0)
    edges = section.val().Edges()

    circle_edges = [e for e in edges if e.geomType() == "CIRCLE"]
    if not circle_edges:
        print("  No circular features found in tile at (PITCH, PITCH).")
        return

    screw_summit_x = PITCH / 2
    screw_summit_y = PITCH / 2
    for arc in circle_edges:
        adaptor = BRepAdaptor_Curve(arc.wrapped)
        circ = adaptor.Circle()
        loc = circ.Location()
        cx = round(loc.X() - PITCH, 3)
        cy = round(loc.Y() - PITCH, 3)
        r = round(arc.radius(), 3)
        if abs(cx - screw_summit_x) < 2 and abs(cy - screw_summit_y) < 2:
            print(f"  Screw hole found:")
            print(f"    Center relative to tile: ({cx:.3f}, {cy:.3f})")
            print(f"    i.e. at summit (grid vertex) position")
            print(f"    Radius at Z=0 (midplane): {r:.3f} (diameter: {2 * r:.3f})")

    # Scan Z levels for radius changes (countersink/counterbore)
    print(f"\n  Screw hole Z profile (scanning from bottom to top):")
    print(f"  {'Z (raw)':>8s}   {'Z (shifted)':>11s}   {'Radius':>8s}   {'Diameter':>10s}")
    z_profile = []
    for z_int in range(int(bb.zmin * 10), int(bb.zmax * 10) + 1):
        z = z_int / 10.0
        try:
            s = cq.Workplane("XY").add(tile_with_screw.val()).section(z)
            arcs = [e for e in s.val().Edges() if e.geomType() == "CIRCLE"]
            for arc in arcs:
                adaptor = BRepAdaptor_Curve(arc.wrapped)
                circ = adaptor.Circle()
                loc = circ.Location()
                cx = round(loc.X() - PITCH, 3)
                cy = round(loc.Y() - PITCH, 3)
                r = round(arc.radius(), 3)
                if abs(cx - screw_summit_x) < 2 and abs(cy - screw_summit_y) < 2:
                    z_shifted = round(z - bb.zmin, 1)
                    print(f"  {z:8.1f}   {z_shifted:11.1f}   {r:8.3f}   {2 * r:10.3f}")
                    z_profile.append((z_shifted, r))
                    break
        except Exception:
            pass

    # Summarize the screw hole shape
    if z_profile:
        r_max = max(r for _, r in z_profile)
        r_min = min(r for _, r in z_profile)
        if abs(r_max - r_min) < 0.01:
            print(f"\n  Screw hole is a simple through-hole, constant radius {r_max:.3f}")
        else:
            # Find the three regions: counterbore, countersink cone, through-hole
            counterbore_end = None
            cone_end = None
            prev_r = z_profile[0][1]
            for z_s, r in z_profile[1:]:
                if counterbore_end is None and abs(r - prev_r) > 0.01:
                    counterbore_end = z_s - 0.1
                if abs(r - r_min) < 0.01 and abs(prev_r - r_min) > 0.01:
                    cone_end = z_s
                prev_r = r

            # Compute countersink angle
            if counterbore_end is not None and cone_end is not None:
                cone_height = cone_end - counterbore_end
                r_change = r_max - r_min
                half_angle = math.degrees(math.atan2(r_change, cone_height))
                full_angle = 2 * half_angle
            else:
                cone_height = 0
                full_angle = 0

            print(f"\n  Screw hole shape (3 zones from bottom to top):")
            print(f"    1. COUNTERBORE: Z=0.0 to Z={counterbore_end:.1f}")
            print(f"       r={r_max:.3f} (d={2 * r_max:.3f})")
            if cone_end is not None:
                print(f"    2. COUNTERSINK CONE: Z={counterbore_end:.1f} to Z={cone_end:.1f}")
                print(f"       Tapers from r={r_max:.3f} to r={r_min:.3f}")
                print(f"       Height: {cone_height:.1f}, angle: ~{full_angle:.0f} deg")
                print(f"    3. THROUGH-HOLE: Z={cone_end:.1f} to Z={-2 * bb.zmin:.1f}")
                print(f"       r={r_min:.3f} (d={2 * r_min:.3f})")

            print(f"\n  CONSTRUCTION:")
            print(f"    The screw is at each grid summit (vertex). Position: centered on")
            print(f"    the intersection of four adjacent tiles.")
            print(f"    Build as: cylinder r={r_min:.3f} (through-hole) + cone (countersink)")
            print(f"    + cylinder r={r_max:.3f} (counterbore at bottom).")
            print(f"    Cut from the tile at each summit position.")


if __name__ == "__main__":
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    step_file = os.path.join(script_dir, "opengrid-lite-5x5.step")
    piece, bb = load_and_center(step_file)
    center_tile = extract_center_tile(piece, bb)

    tile_thickness = round(bb.zlen, 1)
    z_min = bb.zmin
    z_max = bb.zmax
    print("\n" + "=" * 60)
    print("OPENGRID LITE CONSTRUCTION OVERVIEW")
    print("=" * 60)
    print(f"""
An opengrid lite board is an NxM array of square tiles on a {PITCH:.0f}mm pitch.
Each tile is a {PITCH:.0f}x{PITCH:.0f}x{tile_thickness}mm box with an octagonal through-hole (no floor).
The lite variant is thinner ({tile_thickness}mm vs 6.8mm for the full tile), uses
less material, and has screw holes at the grid summits (vertices).

NOTE: The STEP file is Z-centered (Z from {z_min:.1f} to {z_max:.1f}).
  All "shifted" coordinates use Z=0 at the bottom for CadQuery construction.

KEY DIFFERENCES FROM FULL TILE:
  - Thickness: {tile_thickness}mm instead of 6.8mm
  - Profile is NOT symmetric in Z: bottom (Z=0) has the accessory clip
    lip, top (Z={tile_thickness}) is a plain wall
  - Screw holes at grid summits for wall mounting

TWO-FRAME CONSTRUCTION (same principle as full tile):
  The octagonal void emerges from the intersection of two square frames
  rotated 45 deg relative to each other.

WALLS: Each tile has four walls running the full {PITCH:.0f}mm length.
  The wall cross-section (YZ plane at X=0) is constant along the wall's
  length but NOT symmetric top-to-bottom.

CORNER POSTS: The four corners correspond to the walls of the 45 deg
  rotated frame.

CADQUERY CONSTRUCTION RECIPE:
  1. Build axis-aligned frame (4 walls from wall profile):
     - Take the wall cross-section (YZ profile), close it, extrude {PITCH:.0f}mm
     - Position outer face at Y = -PITCH/2 = -{PITCH / 2:.0f}mm
     - Duplicate at 90, 180, 270 deg rotations -> 4 walls
  2. Build 45 deg-rotated frame (4 walls from corner profile):
     - Take the corner cross-section (YZ profile), close it,
       extrude PITCH*sqrt(2) = {PITCH * sqrt2:.1f}mm
     - Position outer face at Y = -PITCH/2*sqrt(2) = -{PITCH / 2 * sqrt2:.1f}mm
     - Duplicate at 90, 180, 270 deg -> 4 walls, rotate frame 45 deg
  3. Union both frames
  4. Intersect with {PITCH:.0f}x{PITCH:.0f}x{tile_thickness}mm box -> single tile
  5. Array tiles at {PITCH:.0f}mm pitch for NxM grid
  6. Optionally add perimeter corner chamfers, connector tabs, screw holes
""")

    retroengineer_tile_inner_walls(center_tile, z_min)
    retroengineer_tile_inner_corners(center_tile, z_min)
    retroengineer_corner_pockets(center_tile, z_min, z_max)
    retroengineer_grid_outer_corners(piece, bb)
    retroengineer_grid_connectors(piece, bb)
    retroengineer_grid_screws(piece, bb)
