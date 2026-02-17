"""Test the lite tile geometry against the center tile of the reference STEP."""

from pathlib import Path

import cadquery as cq
import pytest
import trimesh

from ogt.constants import TILE_SIZE
from ogt.draw.tile.lite import make_opengrid_lite_tile

RETROENGINEER_DIR = Path(__file__).resolve().parent.parent.parent.parent / "retroengineer"
STEP_FILE = RETROENGINEER_DIR / "opengrid-lite-5x5.step"


def _extract_center_tile_from_step() -> cq.Workplane:
    """Load the 5x5 lite STEP and cut the center 28x28 tile."""
    raw = cq.importers.importStep(str(STEP_FILE))
    bb = raw.val().BoundingBox()
    centered = raw.translate((-bb.center.x, -bb.center.y, -bb.center.z))
    bb = centered.val().BoundingBox()
    cut_box = cq.Workplane("XY").box(TILE_SIZE, TILE_SIZE, bb.zlen)
    return cq.Workplane("XY").add(centered.val()).intersect(cut_box)


def _to_trimesh(wp: cq.Workplane) -> trimesh.Trimesh:
    verts, faces = wp.val().tessellate(tolerance=0.01, angularTolerance=0.1)
    verts = [(v.x, v.y, v.z) for v in verts]
    return trimesh.Trimesh(vertices=verts, faces=faces)


@pytest.fixture(scope="module")
def reference_tile():
    """Center tile extracted from the reference STEP, shifted to Z=0 at bottom."""
    tile = _extract_center_tile_from_step()
    bb = tile.val().BoundingBox()
    # Shift so Z=0 is at the bottom (STEP is Z-centered)
    return tile.translate((0, 0, -bb.zmin))


@pytest.fixture(scope="module")
def generated_tile():
    make_opengrid_lite_tile.cache_clear()
    return make_opengrid_lite_tile()


def test_volume(generated_tile, reference_tile):
    gen_vol = generated_tile.val().Volume()
    ref_vol = reference_tile.val().Volume()
    assert ref_vol > 0
    assert gen_vol == pytest.approx(ref_vol, rel=0.005)


def test_bounding_box(generated_tile, reference_tile):
    gen_bb = generated_tile.val().BoundingBox()
    ref_bb = reference_tile.val().BoundingBox()
    gen_extents = sorted([gen_bb.xlen, gen_bb.ylen, gen_bb.zlen])
    ref_extents = sorted([ref_bb.xlen, ref_bb.ylen, ref_bb.zlen])
    for gen_ext, ref_ext in zip(gen_extents, ref_extents):
        assert gen_ext == pytest.approx(ref_ext, abs=0.005)


def test_surface_area(generated_tile, reference_tile):
    gen_area = generated_tile.val().Area()
    ref_area = reference_tile.val().Area()
    assert ref_area > 0
    assert gen_area == pytest.approx(ref_area, rel=0.005)


def test_symmetric_difference_volume(generated_tile, reference_tile):
    gen_mesh = _to_trimesh(generated_tile)
    ref_mesh = _to_trimesh(reference_tile)
    union = trimesh.boolean.union([gen_mesh, ref_mesh])
    intersection = trimesh.boolean.intersection([gen_mesh, ref_mesh])
    xor_volume = union.volume - intersection.volume
    total_volume = gen_mesh.volume
    assert xor_volume / total_volume < 0.001, (
        f"XOR volume {xor_volume:.4f} is {xor_volume / total_volume:.4%} of total "
        f"volume {total_volume:.4f}, exceeds 0.1% threshold"
    )
