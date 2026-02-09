"""CLI for openGrid CadQuery — generate openGrid models from the command line."""

import functools
import json
from pathlib import Path

import click


def parse_layout(ctx, param, value):
    """Parse a ``ROWSxCOLS`` string into a list[list[Tile]]."""
    try:
        parts = value.lower().split("x")
        if len(parts) != 2:
            raise ValueError
        rows, cols = int(parts[0]), int(parts[1])
        if rows < 1 or cols < 1:
            raise ValueError
    except ValueError:
        raise click.BadParameter(f"Expected ROWSxCOLS (e.g. 2x4), got {value!r}")

    from ogt.slot import Tile

    return [[Tile()] * cols for _ in range(rows)]


def auto_name(layout_str, ext):
    return f"opengrid-{layout_str.lower()}.{ext}"


def derive_output(plan_path, fmt):
    return Path(plan_path).with_suffix(f".{fmt}")


def export_geometry(workplane, path, fmt):
    import cadquery as cq

    cq.exporters.export(workplane, str(path), fmt.upper())


def prepare_options(fn):
    """Shared options for prepare and generate commands."""

    @click.argument("layout", callback=parse_layout)
    @click.option(
        "--type",
        "opengrid_type",
        type=click.Choice(["full", "light"]),
        default="full",
        help="Tile variant.",
    )
    @click.option("--connectors", is_flag=True, help="Add connector cutouts.")
    @click.option("--tile-chamfers", is_flag=True, help="Add tile chamfer cutouts.")
    @click.option(
        "--screws",
        type=click.Choice(["corners", "all"]),
        default=None,
        help="Screw placement mode.",
    )
    @click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


@click.group()
def cli():
    """ogt — openGrid CadQuery CLI."""


@cli.command()
@prepare_options
def prepare(layout, opengrid_type, connectors, tile_chamfers, screws, output):
    """Prepare a grid plan (JSON) from a LAYOUT spec (e.g. 2x4)."""
    from ogt.prepare import prepare_grid

    plan = prepare_grid(layout, opengrid_type, connectors, tile_chamfers, screws)

    if output is None:
        rows, cols = len(layout), len(layout[0])
        output = auto_name(f"{rows}x{cols}", "json")

    Path(output).write_text(plan.model_dump_json(indent=2))
    click.echo(f"Plan written to {output}")


@cli.command()
@click.argument("plan_file", type=click.Path(exists=True))
@click.option(
    "--format", "fmt", type=click.Choice(["stl", "step"]), default="stl", help="Output format."
)
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
def draw(plan_file, fmt, output):
    """Draw geometry from a PLAN_FILE (JSON) and export."""
    from pydantic import ValidationError

    from ogt.draw import draw_grid
    from ogt.prepare.types import GridPlan

    try:
        data = json.loads(Path(plan_file).read_text())
        plan = GridPlan(**data)
    except ValidationError as e:
        raise click.ClickException(f"Invalid plan file: {e}")

    result = draw_grid(plan)

    if output is None:
        output = str(derive_output(plan_file, fmt))

    export_geometry(result, output, fmt)
    click.echo(f"Exported to {output}")


@cli.command()
@prepare_options
@click.option(
    "--format", "fmt", type=click.Choice(["stl", "step"]), default="stl", help="Output format."
)
def generate(layout, opengrid_type, connectors, tile_chamfers, screws, output, fmt):
    """Prepare and draw in one step — from LAYOUT to exported geometry."""
    from ogt.draw import draw_grid
    from ogt.prepare import prepare_grid

    plan = prepare_grid(layout, opengrid_type, connectors, tile_chamfers, screws)
    result = draw_grid(plan)

    if output is None:
        rows, cols = len(layout), len(layout[0])
        output = auto_name(f"{rows}x{cols}", fmt)

    export_geometry(result, output, fmt)
    click.echo(f"Exported to {output}")
