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
    assert "LAYOUT" in result.output


def test_prepare_creates_json(tmp_path):
    output = tmp_path / "plan.json"
    result = CliRunner().invoke(cli, ["prepare", "2x2", "--connectors", "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert output.exists()
    data = json.loads(output.read_text())
    assert len(data["tiles"]) == 2
    assert len(data["tiles"][0]) == 2


def test_prepare_auto_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["prepare", "3x4"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "opengrid-3x4.json").exists()


def test_prepare_with_all_options(tmp_path):
    output = tmp_path / "plan.json"
    result = CliRunner().invoke(
        cli,
        [
            "prepare",
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


def test_prepare_invalid_layout():
    result = CliRunner().invoke(cli, ["prepare", "abc"])
    assert result.exit_code != 0
    assert "ROWSxCOLS" in result.output


def test_draw_creates_stl(tmp_path):
    # First create a plan
    plan_path = tmp_path / "plan.json"
    CliRunner().invoke(
        cli, ["prepare", "2x2", "--connectors", "--tile-chamfers", "-o", str(plan_path)]
    )

    # Then draw it
    output = tmp_path / "grid.stl"
    result = CliRunner().invoke(cli, ["draw", str(plan_path), "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert output.exists()
    assert output.stat().st_size > 0


def test_draw_auto_name(tmp_path):
    plan_path = tmp_path / "opengrid-2x2.json"
    CliRunner().invoke(cli, ["prepare", "2x2", "-o", str(plan_path)])

    result = CliRunner().invoke(cli, ["draw", str(plan_path)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "opengrid-2x2.stl").exists()


def test_draw_step_format(tmp_path):
    plan_path = tmp_path / "plan.json"
    CliRunner().invoke(cli, ["prepare", "2x2", "-o", str(plan_path)])

    output = tmp_path / "grid.step"
    result = CliRunner().invoke(
        cli, ["draw", str(plan_path), "--format", "step", "-o", str(output)]
    )
    assert result.exit_code == 0, result.output
    assert output.exists()


def test_draw_missing_file():
    result = CliRunner().invoke(cli, ["draw", "nonexistent.json"])
    assert result.exit_code != 0


def test_generate_creates_stl(tmp_path):
    output = tmp_path / "grid.stl"
    result = CliRunner().invoke(
        cli, ["generate", "2x2", "--connectors", "--tile-chamfers", "-o", str(output)]
    )
    assert result.exit_code == 0, result.output
    assert output.exists()
    assert output.stat().st_size > 0


def test_generate_auto_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["generate", "2x2"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "opengrid-2x2.stl").exists()


def test_generate_step_format(tmp_path):
    output = tmp_path / "grid.step"
    result = CliRunner().invoke(cli, ["generate", "2x2", "--format", "step", "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert output.exists()


def test_roundtrip(tmp_path):
    """prepare → draw should produce the same result as generate."""
    plan_path = tmp_path / "plan.json"
    stl_via_draw = tmp_path / "via_draw.stl"
    stl_via_generate = tmp_path / "via_generate.stl"

    CliRunner().invoke(cli, ["prepare", "2x2", "--connectors", "-o", str(plan_path)])
    CliRunner().invoke(cli, ["draw", str(plan_path), "-o", str(stl_via_draw)])
    CliRunner().invoke(cli, ["generate", "2x2", "--connectors", "-o", str(stl_via_generate)])

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
