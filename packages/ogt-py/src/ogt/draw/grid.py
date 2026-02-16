"""Grid drawing: produce CadQuery geometry from a GridPlan."""

import cadquery as cq

from ogt.constants import TILE_SIZE
from ogt.draw.connectors import CONNECTOR_CUTOUT_HEIGHT, make_connector_cutout
from ogt.draw.screws import make_screw_cutout
from ogt.draw.tile.chamfers import TILE_CHAMFER_CUTOUT
from ogt.draw.tile.full import TILE_THICKNESS, make_opengrid_full_tile
from ogt.prepare.types import GridPlan


def draw_grid(plan: GridPlan) -> cq.Workplane:
    """Create CadQuery geometry from a GridPlan.

    Parameters
    ----------
    plan : GridPlan
        Exhaustive specification of what to draw.

    Returns
    -------
    cq.Workplane
        Unioned grid of tiles with cutouts applied.
    """
    result: cq.Workplane | None = None

    # Place tiles
    for row_idx, row in enumerate(plan.tiles):
        for col_idx, is_tile in enumerate(row):
            if not is_tile:
                continue

            x = col_idx * TILE_SIZE + TILE_SIZE / 2
            y = -(row_idx * TILE_SIZE + TILE_SIZE / 2)

            if plan.opengrid_type == "full":
                tile = make_opengrid_full_tile()
            elif plan.opengrid_type == "light":
                raise NotImplementedError("light tiles are not yet implemented")

            tile = tile.translate((x, y, 0))

            if result is None:
                result = tile
            else:
                result = result.union(tile)

    if result is None:
        return cq.Workplane("XY")

    # Prepare cutout templates (created once, reused)
    connector_template: cq.Workplane | None = None
    connector_z: float = 0.0
    chamfer_template = TILE_CHAMFER_CUTOUT
    screw_template: cq.Workplane | None = None

    # Apply summit features
    for i, row in enumerate(plan.summits):
        for j, summit in enumerate(row):
            sx = j * TILE_SIZE
            sy = -i * TILE_SIZE

            if summit.connector_angle is not None:
                if connector_template is None:
                    connector_template = make_connector_cutout()
                    connector_z = TILE_THICKNESS / 2 - CONNECTOR_CUTOUT_HEIGHT / 2
                cutout = connector_template.rotate(
                    (0, 0, 0), (0, 0, 1), summit.connector_angle
                ).translate((sx, sy, connector_z))
                result = result.cut(cutout)

            if summit.tile_chamfer:
                cutout = chamfer_template.translate((sx, sy, 0))
                result = result.cut(cutout)

            if summit.screw:
                if screw_template is None:
                    screw_template = make_screw_cutout(plan.screw_size)
                result = result.cut(screw_template.translate((sx, sy, 0)))

    return result
