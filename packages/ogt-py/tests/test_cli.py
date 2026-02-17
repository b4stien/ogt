"""Tests for the ogt CLI."""

import json

import trimesh
from click.testing import CliRunner

from ogt.cli import cli


def test_help():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "prepare" in result.output
    assert "draw" in result.output
    assert "generate" in result.output


def test_prepare_help():
    result = CliRunner().invoke(cli, ["prepare", "--help"])
    assert result.exit_code == 0
    assert "--size" in result.output


def test_prepare_creates_json(tmp_path):
    output = tmp_path / "plan.json"
    result = CliRunner().invoke(
        cli, ["prepare", "--size", "2x2", "--connectors", "-o", str(output)]
    )
    assert result.exit_code == 0, result.output
    assert output.exists()
    data = json.loads(output.read_text())
    assert len(data["tiles"]) == 2
    assert len(data["tiles"][0]) == 2


def test_prepare_auto_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["prepare", "--size", "3x4"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "opengrid-3x4.json").exists()


def test_prepare_with_all_options(tmp_path):
    output = tmp_path / "plan.json"
    result = CliRunner().invoke(
        cli,
        [
            "prepare",
            "--size",
            "2x3",
            "--type",
            "full",
            "--connectors",
            "--tile-chamfers",
            "--screws",
            "corners",
            "-o",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text())
    assert data["opengrid_type"] == "full"


def test_prepare_no_input():
    result = CliRunner().invoke(cli, ["prepare"])
    assert result.exit_code != 0
    assert "Provide a compact CODE or --size" in result.output


def test_compact_code_with_flags_errors():
    """Compact code + --size/--connectors/etc. is rejected."""
    result = CliRunner().invoke(cli, ["generate", "0.f.2.2.KlAK.8A._4A", "--connectors"])
    assert result.exit_code != 0
    assert "Cannot combine" in result.output
    assert "--connectors" in result.output


def test_compact_code_with_size_errors():
    result = CliRunner().invoke(
        cli, ["generate", "0.f.2.2.KlAK.8A._4A", "--size", "2x2"]
    )
    assert result.exit_code != 0
    assert "Cannot combine" in result.output
    assert "--size" in result.output


def test_draw_creates_stl(tmp_path):
    # First create a plan
    plan_path = tmp_path / "plan.json"
    prep = CliRunner().invoke(
        cli,
        ["prepare", "--size", "2x2", "--connectors", "--tile-chamfers", "-o", str(plan_path)],
    )
    assert prep.exit_code == 0, prep.output

    # Then draw it
    output = tmp_path / "grid.stl"
    result = CliRunner().invoke(cli, ["draw", str(plan_path), "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert output.exists()
    assert output.stat().st_size > 0


def test_draw_auto_name(tmp_path):
    plan_path = tmp_path / "opengrid-2x2.json"
    prep = CliRunner().invoke(cli, ["prepare", "--size", "2x2", "-o", str(plan_path)])
    assert prep.exit_code == 0, prep.output

    result = CliRunner().invoke(cli, ["draw", str(plan_path)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "opengrid-2x2.step").exists()


def test_draw_stl_format(tmp_path):
    plan_path = tmp_path / "plan.json"
    prep = CliRunner().invoke(cli, ["prepare", "--size", "2x2", "-o", str(plan_path)])
    assert prep.exit_code == 0, prep.output

    output = tmp_path / "grid.stl"
    result = CliRunner().invoke(
        cli, ["draw", str(plan_path), "--format", "stl", "-o", str(output)]
    )
    assert result.exit_code == 0, result.output
    assert output.exists()


def test_draw_missing_file():
    result = CliRunner().invoke(cli, ["draw", "nonexistent.json"])
    assert result.exit_code != 0


def test_generate_creates_stl(tmp_path):
    output = tmp_path / "grid.stl"
    result = CliRunner().invoke(
        cli,
        ["generate", "--size", "2x2", "--connectors", "--tile-chamfers", "-o", str(output)],
    )
    assert result.exit_code == 0, result.output
    assert output.exists()
    assert output.stat().st_size > 0


def test_generate_auto_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["generate", "--size", "2x2"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "opengrid-2x2.step").exists()


def test_generate_stl_format(tmp_path):
    output = tmp_path / "grid.stl"
    result = CliRunner().invoke(
        cli, ["generate", "--size", "2x2", "--format", "stl", "-o", str(output)]
    )
    assert result.exit_code == 0, result.output
    assert output.exists()


def test_generate_compact_format(tmp_path):
    """generate with a compact code produces a valid STL."""
    output = tmp_path / "grid.stl"
    result = CliRunner().invoke(
        cli, ["generate", "0.f.2.2.KlAK.8A._4A", "--format", "stl", "-o", str(output)]
    )
    assert result.exit_code == 0, result.output
    assert output.exists()
    mesh = trimesh.load(str(output))
    assert isinstance(mesh, trimesh.Trimesh)
    assert mesh.volume > 0


def test_prepare_compact_format(tmp_path):
    """prepare with a compact code produces valid JSON."""
    output = tmp_path / "plan.json"
    result = CliRunner().invoke(cli, ["prepare", "0.f.2.2.KlAK.8A._4A", "-o", str(output)])
    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text())
    assert len(data["tiles"]) == 2
    assert len(data["tiles"][0]) == 2


def test_roundtrip(tmp_path):
    """prepare → draw should produce the same result as generate."""
    plan_path = tmp_path / "plan.json"
    stl_via_draw = tmp_path / "via_draw.stl"
    stl_via_generate = tmp_path / "via_generate.stl"

    prep = CliRunner().invoke(cli, ["prepare", "--size", "2x2", "--connectors", "-o", str(plan_path)])
    assert prep.exit_code == 0, prep.output
    draw = CliRunner().invoke(
        cli, ["draw", str(plan_path), "--format", "stl", "-o", str(stl_via_draw)]
    )
    assert draw.exit_code == 0, draw.output
    gen = CliRunner().invoke(
        cli,
        ["generate", "--size", "2x2", "--connectors", "--format", "stl", "-o", str(stl_via_generate)],
    )
    assert gen.exit_code == 0, gen.output

    # Both files should exist and have content
    assert stl_via_draw.exists()
    assert stl_via_generate.exists()
    # Geometric equivalence (byte-level equality is not guaranteed by OCCT)
    mesh_draw = trimesh.load(str(stl_via_draw))
    mesh_generate = trimesh.load(str(stl_via_generate))
    assert isinstance(mesh_draw, trimesh.Trimesh)
    assert isinstance(mesh_generate, trimesh.Trimesh)
    assert mesh_draw.volume == mesh_generate.volume
    assert (mesh_draw.bounding_box.extents == mesh_generate.bounding_box.extents).all()
