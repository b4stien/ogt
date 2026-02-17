from functools import lru_cache

import pytest
import trimesh

from ogt import Tile, make_opengrid
from ogt.constants import TILE_SIZE
from ogt.draw.tile.full import TILE_THICKNESS
from ogt.draw.tile.lite import LITE_TILE_THICKNESS

from grid_fixtures import GRID_CONFIGS, GridConfig, load_reference_mesh


@lru_cache
def build_grid(config: GridConfig):
    layout = [[Tile()] * config.cols for _ in range(config.rows)]
    return make_opengrid(
        layout,
        opengrid_type=config.opengrid_type,
        connectors=config.connectors,
        tile_chamfers=config.chamfers,
        screws=config.screws,
    )


@lru_cache
def build_grid_mesh(config: GridConfig) -> trimesh.Trimesh:
    grid = build_grid(config)
    verts, faces = grid.val().tessellate(tolerance=0.01, angularTolerance=0.1)
    verts = [(v.x, v.y, v.z) for v in verts]
    return trimesh.Trimesh(vertices=verts, faces=faces)


@lru_cache
def _load_reference_mesh(config: GridConfig) -> trimesh.Trimesh:
    return load_reference_mesh(config, build_grid_mesh(config))


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_volume_against_reference(config):
    grid = build_grid(config)
    reference_mesh = _load_reference_mesh(config)
    cq_volume = grid.val().Volume()
    ref_volume = reference_mesh.volume
    assert ref_volume > 0, "Reference mesh has zero volume"
    assert cq_volume == pytest.approx(ref_volume, rel=0.005)


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_bounding_box_against_reference(config):
    grid = build_grid(config)
    reference_mesh = _load_reference_mesh(config)
    bb = grid.val().BoundingBox()
    cq_extents = sorted([bb.xlen, bb.ylen, bb.zlen])
    ref_extents = sorted(reference_mesh.bounding_box.extents)
    for cq_ext, ref_ext in zip(cq_extents, ref_extents):
        assert cq_ext == pytest.approx(ref_ext, abs=0.005)


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_surface_area_against_reference(config):
    grid = build_grid(config)
    reference_mesh = _load_reference_mesh(config)
    cq_area = grid.val().Area()
    ref_area = reference_mesh.area
    assert ref_area > 0, "Reference mesh has zero area"
    assert cq_area == pytest.approx(ref_area, rel=0.005)


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_symmetric_difference_volume(config):
    grid_mesh = build_grid_mesh(config)
    reference_mesh = _load_reference_mesh(config)
    union = trimesh.boolean.union([grid_mesh, reference_mesh])
    intersection = trimesh.boolean.intersection([grid_mesh, reference_mesh])
    xor_volume = union.volume - intersection.volume
    total_volume = grid_mesh.volume
    assert xor_volume / total_volume < 0.001, (
        f"XOR volume {xor_volume:.4f} is {xor_volume / total_volume:.4%} of total "
        f"volume {total_volume:.4f}, exceeds 0.1% threshold"
    )


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_grid_is_not_empty(config):
    grid = build_grid(config)
    assert grid.val().Volume() > 0


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_bounding_box_dimensions(config):
    grid = build_grid(config)
    bb = grid.val().BoundingBox()
    extents = sorted([bb.xlen, bb.ylen, bb.zlen])
    expected_x = TILE_SIZE * config.cols
    expected_y = TILE_SIZE * config.rows
    thickness = LITE_TILE_THICKNESS if config.opengrid_type == "lite" else TILE_THICKNESS
    expected = sorted([expected_x, expected_y, thickness])
    for actual, exp in zip(extents, expected):
        assert actual == pytest.approx(exp, abs=0.005)


# ── Lite tile tests ──


def test_lite_tile_not_empty():
    layout = [[Tile()] * 2 for _ in range(2)]
    grid = make_opengrid(layout, opengrid_type="lite")
    assert grid.val().Volume() > 0


def test_lite_tile_bounding_box():
    layout = [[Tile()] * 2 for _ in range(2)]
    grid = make_opengrid(layout, opengrid_type="lite")
    bb = grid.val().BoundingBox()
    extents = sorted([bb.xlen, bb.ylen, bb.zlen])
    expected = sorted([TILE_SIZE * 2, TILE_SIZE * 2, LITE_TILE_THICKNESS])
    for actual, exp in zip(extents, expected):
        assert actual == pytest.approx(exp, abs=0.005)


def test_lite_tile_thinner_than_full():
    layout = [[Tile()]]
    full = make_opengrid(layout, opengrid_type="full")
    lite = make_opengrid(layout, opengrid_type="lite")
    assert lite.val().Volume() < full.val().Volume()
