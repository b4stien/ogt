"""Tests for the compact GridPlan encoding/decoding."""

import pytest

from ogt.compact import decode, encode
from ogt.prepare import prepare_grid
from ogt.prepare.types import GridPlan, ScrewSize, SummitFeatures
from ogt.slot import Hole, Tile


def _plans_equal(a: GridPlan, b: GridPlan) -> None:
    """Assert two GridPlans are equivalent."""
    assert a.opengrid_type == b.opengrid_type
    assert a.screw_size == b.screw_size
    assert a.tiles == b.tiles
    assert len(a.summits) == len(b.summits)
    for i, (row_a, row_b) in enumerate(zip(a.summits, b.summits)):
        assert len(row_a) == len(row_b), f"summit row {i} length mismatch"
        for j, (sa, sb) in enumerate(zip(row_a, row_b)):
            assert sa.connector_angle == sb.connector_angle, f"summit ({i},{j}) connector_angle"
            assert sa.tile_chamfer == sb.tile_chamfer, f"summit ({i},{j}) tile_chamfer"
            assert sa.screw == sb.screw, f"summit ({i},{j}) screw"


# --- Known value ---


def test_known_value_2x2_full():
    """The canonical example from the spec."""
    code = "0.f.2.2.KlAK.8A._4A"
    plan = decode(code)

    assert plan.opengrid_type == "full"
    assert plan.screw_size.diameter == 4.2
    assert plan.screw_size.head_diameter == 8.0
    assert plan.screw_size.head_inset == 1.0
    assert plan.tiles == [[True, True], [True, True]]

    # 4 chamfers (corners), 4 connectors (edges), 1 screw (center)
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for i, j in corners:
        assert plan.summits[i][j].tile_chamfer, f"({i},{j}) should be chamfer"

    assert plan.summits[1][1].screw, "center should be screw"

    connectors = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for i, j in connectors:
        assert plan.summits[i][j].connector_angle is not None, f"({i},{j}) should be connector"


def test_known_value_encode():
    """Encoding the canonical 2x2 plan produces the known code."""
    plan = decode("0.f.2.2.KlAK.8A._4A")
    assert encode(plan) == "0.f.2.2.KlAK.8A._4A"


# --- Roundtrip encode→decode ---


def test_roundtrip_1x1():
    plan = GridPlan(
        tiles=[[True]],
        summits=[[SummitFeatures(tile_chamfer=True)] * 2] * 2,
        opengrid_type="full",
        screw_size=ScrewSize(),
    )
    _plans_equal(decode(encode(plan)), plan)


def test_roundtrip_2x3_with_holes():
    tiles = [[True, False, True], [False, True, True]]
    layout = [[Tile() if t else Hole() for t in row] for row in tiles]
    plan = prepare_grid(layout, connectors=True, tile_chamfers=True)
    _plans_equal(decode(encode(plan)), plan)


def test_roundtrip_light_type():
    layout = [[Tile(), Tile()], [Tile(), Tile()]]
    plan = prepare_grid(layout, opengrid_type="lite", connectors=True)
    decoded = decode(encode(plan))
    assert decoded.opengrid_type == "lite"
    _plans_equal(decoded, plan)


def test_roundtrip_l_shape():
    """L-shaped grid: top-right hole."""
    tiles = [[True, False], [True, True]]
    layout = [[Tile() if t else Hole() for t in row] for row in tiles]
    plan = prepare_grid(layout, connectors=True, tile_chamfers=True)
    _plans_equal(decode(encode(plan)), plan)


def test_roundtrip_no_features():
    """Grid with no features active."""
    plan = GridPlan(
        tiles=[[True, True], [True, True]],
        summits=[[SummitFeatures()] * 3 for _ in range(3)],
    )
    _plans_equal(decode(encode(plan)), plan)


def test_roundtrip_screws_all():
    layout = [[Tile()] * 3 for _ in range(3)]
    plan = prepare_grid(layout, screws="all", tile_chamfers=True)
    _plans_equal(decode(encode(plan)), plan)


def test_roundtrip_screws_corners():
    layout = [[Tile()] * 4 for _ in range(4)]
    plan = prepare_grid(layout, connectors=True, screws="corners", tile_chamfers=True)
    _plans_equal(decode(encode(plan)), plan)


def test_roundtrip_custom_screw_size():
    plan = GridPlan(
        tiles=[[True]],
        summits=[[SummitFeatures()] * 2 for _ in range(2)],
        screw_size=ScrewSize(diameter=3.0, head_diameter=6.5, head_inset=0.5),
    )
    decoded = decode(encode(plan))
    assert decoded.screw_size.diameter == 3.0
    assert decoded.screw_size.head_diameter == 6.5
    assert decoded.screw_size.head_inset == 0.5


# --- Error cases ---


def test_bad_version():
    with pytest.raises(ValueError, match="Unsupported version"):
        decode("1.f.2.2.KlAK.8A._4A")


def test_wrong_part_count():
    with pytest.raises(ValueError, match="7 dot-separated parts"):
        decode("0.f.2.2.KlAK.8A")


def test_invalid_type():
    with pytest.raises(ValueError, match="Invalid type"):
        decode("0.x.2.2.KlAK.8A._4A")


def test_invalid_dimensions():
    with pytest.raises(ValueError, match="Invalid dimensions"):
        decode("0.f.a.2.KlAK.8A._4A")


def test_zero_dimensions():
    with pytest.raises(ValueError, match="must be >= 1"):
        decode("0.f.0.2.KlAK.8A._4A")


def test_bad_screw_data():
    with pytest.raises(ValueError, match="Screw data must be 3 bytes"):
        decode("0.f.2.2.AA.8A._4A")


def test_insufficient_tile_data():
    with pytest.raises(ValueError, match="Insufficient tile data"):
        # 2x2 needs 4 bits = 1 byte, but AA decodes to 1 byte (0x00)
        # which is enough. Use empty string which decodes to 0 bytes.
        decode("0.f.2.2.KlAK.._4A")


def test_insufficient_feature_data():
    with pytest.raises(ValueError, match="Insufficient feature data"):
        decode("0.f.2.2.KlAK.8A.")


# --- Roundtrip from prepare_grid ---


@pytest.mark.parametrize(
    "rows,cols,kwargs",
    [
        (1, 1, {}),
        (2, 2, {"connectors": True}),
        (2, 3, {"connectors": True, "tile_chamfers": True}),
        (3, 3, {"screws": "all"}),
        (4, 2, {"connectors": True, "screws": "corners", "tile_chamfers": True}),
    ],
)
def test_roundtrip_prepare_grid(rows, cols, kwargs):
    layout = [[Tile()] * cols for _ in range(rows)]
    plan = prepare_grid(layout, **kwargs)
    _plans_equal(decode(encode(plan)), plan)
