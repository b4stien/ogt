"""Compare JS (replicad) generated geometry against reference files.

For each grid config, this test:
1. Builds a GridPlan via Python's prepare_grid
2. Encodes it as a compact code
3. Calls the JS generate script (packages/ogt-web/scripts/generate.ts) to produce an STL
4. Loads the JS-generated STL with trimesh
5. Compares against the reference 3MF/STL files
"""

import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import pytest
import trimesh

from ogt import Tile, prepare_grid
from ogt.compact import encode
from ogt.constants import TILE_SIZE
from ogt.draw.tile.full import TILE_THICKNESS
from ogt.draw.tile.lite import LITE_TILE_THICKNESS

from grid_fixtures import GRID_CONFIGS, GridConfig, load_reference_mesh

OGT_WEB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "packages" / "ogt-web"

# Holds TemporaryDirectory instances so they (and the STL files inside)
# survive for the whole test session and are cleaned up at interpreter exit.
_tmpdir_cache: dict[GridConfig, tempfile.TemporaryDirectory] = {}


def _compact_code(config: GridConfig) -> str:
    """Build a GridPlan and encode it as a compact code."""
    layout = [[Tile()] * config.cols for _ in range(config.rows)]
    plan = prepare_grid(
        layout,
        opengrid_type=config.opengrid_type,
        connectors=config.connectors,
        tile_chamfers=config.chamfers,
        screws=config.screws,
    )
    return encode(plan)


@lru_cache
def _generate_js_stl(config: GridConfig) -> Path:
    """Call the JS generate script and return the path to the generated STL."""
    code = _compact_code(config)
    td = tempfile.TemporaryDirectory()
    _tmpdir_cache[config] = td
    out = Path(td.name) / "output.stl"
    result = subprocess.run(
        ["npx", "tsx", "scripts/generate.ts", code, "--format", "stl", "-o", str(out)],
        cwd=str(OGT_WEB_DIR),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"JS generate failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    assert out.exists(), f"Expected output file {out} not found"
    return out


@lru_cache
def _load_js_mesh(config: GridConfig) -> trimesh.Trimesh:
    """Generate and load JS mesh."""
    stl_path = _generate_js_stl(config)
    mesh = trimesh.load(str(stl_path))
    assert isinstance(mesh, trimesh.Trimesh)
    return mesh


@lru_cache
def _load_reference_mesh(config: GridConfig) -> trimesh.Trimesh:
    return load_reference_mesh(config, _load_js_mesh(config))


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_js_volume_against_reference(config):
    js_mesh = _load_js_mesh(config)
    reference_mesh = _load_reference_mesh(config)
    js_volume = js_mesh.volume
    ref_volume = reference_mesh.volume
    assert ref_volume > 0, "Reference mesh has zero volume"
    assert js_volume == pytest.approx(ref_volume, rel=0.005)


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_js_bounding_box_against_reference(config):
    js_mesh = _load_js_mesh(config)
    reference_mesh = _load_reference_mesh(config)
    js_extents = sorted(js_mesh.bounding_box.extents)
    ref_extents = sorted(reference_mesh.bounding_box.extents)
    for js_ext, ref_ext in zip(js_extents, ref_extents):
        assert js_ext == pytest.approx(ref_ext, abs=0.005)


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_js_surface_area_against_reference(config):
    js_mesh = _load_js_mesh(config)
    reference_mesh = _load_reference_mesh(config)
    js_area = js_mesh.area
    ref_area = reference_mesh.area
    assert ref_area > 0, "Reference mesh has zero area"
    assert js_area == pytest.approx(ref_area, rel=0.005)


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_js_bounding_box_dimensions(config):
    js_mesh = _load_js_mesh(config)
    extents = sorted(js_mesh.bounding_box.extents)
    expected_x = TILE_SIZE * config.cols
    expected_y = TILE_SIZE * config.rows
    thickness = LITE_TILE_THICKNESS if config.opengrid_type == "lite" else TILE_THICKNESS
    expected = sorted([expected_x, expected_y, thickness])
    for actual, exp in zip(extents, expected):
        assert actual == pytest.approx(exp, abs=0.005)


@pytest.mark.parametrize("config", GRID_CONFIGS)
def test_js_grid_is_not_empty(config):
    js_mesh = _load_js_mesh(config)
    assert js_mesh.volume > 0
