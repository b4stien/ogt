from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
import pytest
import trimesh

from ogt import Tile, make_opengrid
from ogt.constants import TILE_SIZE
from ogt.draw.tile.full import TILE_THICKNESS

REFERENCES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "references"


@dataclass(frozen=True)
class GridConfig:
    cols: int
    rows: int
    chamfers: bool
    connectors: bool
    ref_file: str
    screws: Literal["corners", "all"] | None = None


GRID_CONFIGS = [
    pytest.param(
        GridConfig(
            cols=2,
            rows=2,
            chamfers=True,
            connectors=True,
            ref_file="printables_davidd-2x2-chamfers-connectors.3mf",
        ),
        id="2x2-chamfers-connectors",
    ),
    pytest.param(
        GridConfig(
            cols=4,
            rows=2,
            chamfers=True,
            connectors=True,
            ref_file="printables_davidd-4x2-chamfers-connectors.3mf",
        ),
        id="4x2-chamfers-connectors",
    ),
    pytest.param(
        GridConfig(
            cols=6,
            rows=3,
            chamfers=True,
            connectors=True,
            ref_file="printables_davidd-6x3-chamfers-connectors.3mf",
        ),
        id="6x3-chamfers-connectors",
    ),
    pytest.param(
        GridConfig(
            cols=4,
            rows=2,
            chamfers=True,
            connectors=True,
            screws="corners",
            ref_file="gridfinity_perplexinglabs-4x2-chamfers-connectors-screws.stl",
        ),
        id="4x2-chamfers-connectors-screws",
    ),
    pytest.param(
        GridConfig(
            cols=8,
            rows=4,
            chamfers=True,
            connectors=True,
            ref_file="gridfinity_perplexinglabs-8x4-chamfers-connectors.stl",
        ),
        id="8x4-chamfers-connectors",
    ),
    pytest.param(
        GridConfig(
            cols=8,
            rows=4,
            chamfers=True,
            connectors=True,
            screws="corners",
            ref_file="gridfinity_perplexinglabs-8x4-chamfers-connectors-screws.stl",
        ),
        id="8x4-chamfers-connectors-screws",
    ),
]


@lru_cache
def build_grid(config: GridConfig):
    layout = [[Tile()] * config.cols for _ in range(config.rows)]
    return make_opengrid(
        layout,
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
def load_reference_mesh(config: GridConfig) -> trimesh.Trimesh:
    grid_mesh = build_grid_mesh(config)
    path = REFERENCES_DIR / config.ref_file
    scene = trimesh.load(str(path))
    if isinstance(scene, trimesh.Scene):
        mesh = scene.to_geometry()
    else:
        mesh = scene
    assert isinstance(mesh, trimesh.Trimesh)
    # Reference meshes have X/Y swapped vs CadQuery output; swap if needed
    ref_extents = mesh.bounding_box.extents
    grid_extents = grid_mesh.bounding_box.extents
    if not np.allclose(ref_extents[:2], grid_extents[:2], atol=0.1):
        swap = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]], dtype=float)
        mesh.apply_transform(
            np.vstack(
                [
                    np.hstack([swap, [[0], [0], [0]]]),
                    [0, 0, 0, 1],
                ]
            )
        )
    # Align reference mesh to generated mesh by matching min corners
    offset = grid_mesh.bounds[0] - mesh.bounds[0]
    mesh.apply_translation(offset)
    return mesh


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_volume_against_reference(config):
    grid = build_grid(config)
    reference_mesh = load_reference_mesh(config)
    cq_volume = grid.val().Volume()
    ref_volume = reference_mesh.volume
    assert ref_volume > 0, "Reference mesh has zero volume"
    assert cq_volume == pytest.approx(ref_volume, rel=0.005)


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_bounding_box_against_reference(config):
    grid = build_grid(config)
    reference_mesh = load_reference_mesh(config)
    bb = grid.val().BoundingBox()
    cq_extents = sorted([bb.xlen, bb.ylen, bb.zlen])
    ref_extents = sorted(reference_mesh.bounding_box.extents)
    for cq_ext, ref_ext in zip(cq_extents, ref_extents):
        assert cq_ext == pytest.approx(ref_ext, abs=0.005)


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_surface_area_against_reference(config):
    grid = build_grid(config)
    reference_mesh = load_reference_mesh(config)
    cq_area = grid.val().Area()
    ref_area = reference_mesh.area
    assert ref_area > 0, "Reference mesh has zero area"
    assert cq_area == pytest.approx(ref_area, rel=0.005)


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_symmetric_difference_volume(config):
    grid_mesh = build_grid_mesh(config)
    reference_mesh = load_reference_mesh(config)
    union = trimesh.boolean.union([grid_mesh, reference_mesh])
    intersection = trimesh.boolean.intersection([grid_mesh, reference_mesh])
    xor_volume = union.volume - intersection.volume
    total_volume = grid_mesh.volume
    assert xor_volume / total_volume < 0.001, (
        f"XOR volume {xor_volume:.4f} is {xor_volume / total_volume:.4%} of total "
        f"volume {total_volume:.4f}, exceeds 1% threshold"
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
    expected = sorted([expected_x, expected_y, TILE_THICKNESS])
    for actual, exp in zip(extents, expected):
        assert actual == pytest.approx(exp, abs=0.005)
