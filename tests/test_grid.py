import pytest
import trimesh

from ogt.constants import TILE_SIZE
from ogt.draw.tile.full import TILE_THICKNESS


class TestAgainstReference:
    """Compare CadQuery output to the reference 3MF mesh."""

    def test_volume_against_reference(self, grid, reference_mesh):
        cq_volume = grid.val().Volume()
        ref_volume = reference_mesh.volume
        assert ref_volume > 0, "Reference mesh has zero volume"
        assert cq_volume == pytest.approx(ref_volume, rel=0.005)

    def test_bounding_box_against_reference(self, grid, reference_mesh):
        bb = grid.val().BoundingBox()
        cq_extents = sorted([bb.xlen, bb.ylen, bb.zlen])
        ref_extents = sorted(reference_mesh.bounding_box.extents)
        for cq_ext, ref_ext in zip(cq_extents, ref_extents):
            assert cq_ext == pytest.approx(ref_ext, abs=0.005)

    def test_surface_area_against_reference(self, grid, reference_mesh):
        cq_area = grid.val().Area()
        ref_area = reference_mesh.area
        assert ref_area > 0, "Reference mesh has zero area"
        assert cq_area == pytest.approx(ref_area, rel=0.005)

    def test_symmetric_difference_volume(self, grid_mesh, reference_mesh):
        union = trimesh.boolean.union([grid_mesh, reference_mesh])
        intersection = trimesh.boolean.intersection([grid_mesh, reference_mesh])
        xor_volume = union.volume - intersection.volume
        total_volume = grid_mesh.volume
        assert xor_volume / total_volume < 0.001, (
            f"XOR volume {xor_volume:.4f} is {xor_volume / total_volume:.4%} of total "
            f"volume {total_volume:.4f}, exceeds 1% threshold"
        )


class TestSanityChecks:
    """Standalone sanity checks on the CadQuery geometry."""

    def test_grid_is_not_empty(self, grid):
        assert grid.val().Volume() > 0

    def test_bounding_box_dimensions(self, grid, grid_config):
        bb = grid.val().BoundingBox()
        extents = sorted([bb.xlen, bb.ylen, bb.zlen])
        expected_x = TILE_SIZE * grid_config["cols"]
        expected_y = TILE_SIZE * grid_config["rows"]
        expected = sorted([expected_x, expected_y, TILE_THICKNESS])
        for actual, exp in zip(extents, expected):
            assert actual == pytest.approx(exp, abs=0.005)
