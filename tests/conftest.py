from pathlib import Path

import pytest
import numpy as np
import trimesh

from ogt import Tile, make_opengrid

REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"

GRID_CONFIGS = [
    pytest.param(
        {
            "cols": 2,
            "rows": 2,
            "chamfers": True,
            "connectors": True,
            "ref_file": "printables_davidd-2x2-chamfers-connectors.3mf",
        },
        id="2x2-chamfers-connectors",
    ),
    pytest.param(
        {
            "cols": 4,
            "rows": 2,
            "chamfers": True,
            "connectors": True,
            "ref_file": "printables_davidd-4x2-chamfers-connectors.3mf",
        },
        id="4x2-chamfers-connectors",
    ),
    pytest.param(
        {
            "cols": 6,
            "rows": 3,
            "chamfers": True,
            "connectors": True,
            "ref_file": "printables_davidd-6x3-chamfers-connectors.3mf",
        },
        id="6x3-chamfers-connectors",
    ),
    pytest.param(
        {
            "cols": 4,
            "rows": 2,
            "chamfers": True,
            "connectors": True,
            "screws": "corners",
            "ref_file": "gridfinity_perplexinglabs-4x2-chamfers-connectors-screws.stl",
        },
        id="4x2-chamfers-connectors-screws",
    ),
    pytest.param(
        {
            "cols": 8,
            "rows": 4,
            "chamfers": True,
            "connectors": True,
            "ref_file": "gridfinity_perplexinglabs-8x4-chamfers-connectors.stl",
        },
        id="8x4-chamfers-connectors",
    ),
    pytest.param(
        {
            "cols": 8,
            "rows": 4,
            "chamfers": True,
            "connectors": True,
            "screws": "corners",
            "ref_file": "gridfinity_perplexinglabs-8x4-chamfers-connectors-screws.stl",
        },
        id="8x4-chamfers-connectors-screws",
    ),
]


@pytest.fixture(scope="session", params=GRID_CONFIGS)
def grid_config(request):
    return request.param


@pytest.fixture(scope="session")
def grid(grid_config):
    cols, rows = grid_config["cols"], grid_config["rows"]
    layout = [[Tile()] * cols for _ in range(rows)]
    return make_opengrid(
        layout,
        connectors=grid_config.get("connectors", False),
        tile_chamfers=grid_config.get("chamfers", False),
        screws=grid_config.get("screws"),
    )


@pytest.fixture(scope="session")
def grid_mesh(grid) -> trimesh.Trimesh:
    verts, faces = grid.val().tessellate(tolerance=0.01, angularTolerance=0.1)
    verts = [(v.x, v.y, v.z) for v in verts]
    return trimesh.Trimesh(vertices=verts, faces=faces)


@pytest.fixture(scope="session")
def reference_mesh(grid_mesh: trimesh.Trimesh, grid_config):
    path = REFERENCES_DIR / grid_config["ref_file"]
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
        # Swap X and Y axes
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
