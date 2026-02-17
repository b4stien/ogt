"""Shared grid test fixtures: configs, reference mesh loading."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pytest
import trimesh

REFERENCES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "references"


@dataclass(frozen=True)
class GridConfig:
    cols: int
    rows: int
    chamfers: bool
    connectors: bool
    ref_file: str
    screws: Literal["corners", "all"] | None = None
    opengrid_type: Literal["full", "lite"] = "full"


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
    pytest.param(
        GridConfig(
            cols=2,
            rows=2,
            chamfers=True,
            connectors=True,
            screws="corners",
            opengrid_type="lite",
            ref_file="printables_davidd-lite-2x2-chamfers-connectors-screws.3mf",
        ),
        id="lite-2x2-chamfers-connectors-screws",
    ),
    pytest.param(
        GridConfig(
            cols=4,
            rows=2,
            chamfers=True,
            connectors=True,
            screws="corners",
            opengrid_type="lite",
            ref_file="printables_davidd-lite-4x2-chamfers-connectors-screws.3mf",
        ),
        id="lite-4x2-chamfers-connectors-screws",
    ),
]


def load_reference_mesh(
    config: GridConfig,
    target_mesh: trimesh.Trimesh,
) -> trimesh.Trimesh:
    """Load a reference mesh, aligned to *target_mesh*.

    Swaps X/Y axes if the reference extents don't match the target, then
    translates so that the min corners coincide.
    """
    path = REFERENCES_DIR / config.ref_file
    scene = trimesh.load(str(path))
    if isinstance(scene, trimesh.Scene):
        mesh = scene.to_geometry()
    else:
        mesh = scene
    assert isinstance(mesh, trimesh.Trimesh)
    # Reference meshes may have X/Y swapped; swap if needed
    ref_extents = mesh.bounding_box.extents
    target_extents = target_mesh.bounding_box.extents
    if not np.allclose(ref_extents[:2], target_extents[:2], atol=0.1):
        swap = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]], dtype=float)
        mesh.apply_transform(
            np.vstack(
                [
                    np.hstack([swap, [[0], [0], [0]]]),
                    [0, 0, 0, 1],
                ]
            )
        )
    # Align reference mesh to target mesh by matching min corners
    offset = target_mesh.bounds[0] - mesh.bounds[0]
    mesh.apply_translation(offset)
    return mesh
