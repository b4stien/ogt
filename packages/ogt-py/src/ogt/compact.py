"""Compact encoding/decoding for GridPlan.

Format specification v0
=======================

**Form**: ``0.{TYPE}.{R}.{C}.{SCREW}.{TILES}.{FEATURES}``

+-----------+-------------------------------------------------------------+---------+
| Field     | Description                                                 | Example |
+-----------+-------------------------------------------------------------+---------+
| ``0``     | Version of the format                                       | ``0``   |
| ``TYPE``  | ``f`` = full, ``l`` = lite                                  | ``f``   |
| ``R``     | Number of rows (decimal)                                    | ``2``   |
| ``C``     | Number of columns (decimal)                                 | ``3``   |
| ``SCREW`` | 3 uint8 in 0.1 mm: [diameter, head_diameter, head_inset]    | ``KlAK``|
|           | → base64url                                                 |         |
| ``TILES`` | R×C bits (1=tile, 0=hole), MSB first, packed in bytes       | ``8A``  |
|           | → base64url                                                 |         |
|``FEATURES``| (R+1)×(C+1) bits (1=feature active, 0=off), MSB first,    | ``_4A`` |
|           | packed in bytes → base64url                                 |         |
+-----------+-------------------------------------------------------------+---------+

R and C are both stored because bits are packed into bytes (multiples of 8),
so the exact number of significant bits is lost.  R alone is not enough to
derive C.

Screw encoding
--------------
3 bytes for [diameter, head_diameter, head_inset], each in units of 0.1 mm
(uint8, range 0–25.5 mm):

- Default: 4.2 mm, 8.0 mm, 1.0 mm → [42, 80, 10] → ``[0x2A, 0x50, 0x0A]``
  → base64url ``KlAK``

Tile encoding
-------------
R×C bits, row-major (1=tile, 0=hole).  Packed MSB first into
``ceil(R×C / 8)`` bytes, last byte right-padded with 0.  Base64url without
``=``.

Feature encoding
----------------
(R+1)×(C+1) bits, row-major.  1 = activate the eligible feature at that
summit, 0 = off.  Same packing as tiles.

The eligible feature is determined by the tile layout (mutually exclusive):

- 1 tile neighbor → chamfer
- 2 neighbors in H/V split → connector (angle recomputed by the decoder)
- 4 tile neighbors → screw
- Otherwise → bit ignored

Example
-------
2×2 grid, all tiles, all features active, type full, default screws::

    0.f.2.2.KlAK.8A._4A
"""

import base64
import math

from ogt.prepare.connectors import (
    _connector_direction,
    compute_eligible_connector_positions,
)
from ogt.prepare.screws import compute_eligible_screw_positions
from ogt.prepare.tile_chamfers import compute_eligible_tile_chamfer_positions
from ogt.prepare.types import GridPlan, ScrewSize, SummitFeatures
from ogt.slot import Hole, Tile


def _bits_to_bytes(bits: list[bool]) -> bytes:
    """Pack bools into bytes, MSB first, right-padded with 0s."""
    n_bytes = math.ceil(len(bits) / 8)
    result = bytearray(n_bytes)
    for i, bit in enumerate(bits):
        if bit:
            result[i // 8] |= 1 << (7 - i % 8)
    return bytes(result)


def _bytes_to_bits(data: bytes, n_bits: int) -> list[bool]:
    """Unpack *n_bits* from *data*, MSB first."""
    bits: list[bool] = []
    for i in range(n_bits):
        byte_idx = i // 8
        bit_idx = 7 - i % 8
        bits.append(bool(data[byte_idx] & (1 << bit_idx)))
    return bits


def _b64url_encode(data: bytes) -> str:
    """Base64url encode without ``=`` padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Base64url decode, re-adding ``=`` padding."""
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def encode(plan: GridPlan) -> str:
    """Encode a :class:`GridPlan` into a compact string."""
    rows = len(plan.tiles)
    cols = len(plan.tiles[0])

    # Type
    type_char = "f" if plan.opengrid_type == "full" else "l"

    # Screw → 3 bytes (0.1 mm units)
    screw_bytes = bytes(
        [
            round(plan.screw_size.diameter * 10),
            round(plan.screw_size.head_diameter * 10),
            round(plan.screw_size.head_inset * 10),
        ]
    )
    screw_str = _b64url_encode(screw_bytes)

    # Tiles → R×C bits row-major
    tile_bits = [plan.tiles[r][c] for r in range(rows) for c in range(cols)]
    tiles_str = _b64url_encode(_bits_to_bytes(tile_bits))

    # Features → (R+1)×(C+1) bits row-major
    feature_bits: list[bool] = []
    for i in range(rows + 1):
        for j in range(cols + 1):
            s = plan.summits[i][j]
            active = s.connector_angle is not None or s.tile_chamfer or s.screw
            feature_bits.append(active)
    features_str = _b64url_encode(_bits_to_bytes(feature_bits))

    return f"0.{type_char}.{rows}.{cols}.{screw_str}.{tiles_str}.{features_str}"


def decode(code: str) -> GridPlan:
    """Decode a compact string into a :class:`GridPlan`."""
    parts = code.split(".")
    if len(parts) != 7:
        raise ValueError(f"Expected 7 dot-separated parts, got {len(parts)}")

    version, type_char, r_str, c_str, screw_str, tiles_str, features_str = parts

    if version != "0":
        raise ValueError(f"Unsupported version: {version!r}")

    if type_char not in ("f", "l"):
        raise ValueError(f"Invalid type: {type_char!r}")
    opengrid_type: str = "full" if type_char == "f" else "lite"

    try:
        rows = int(r_str)
        cols = int(c_str)
    except ValueError:
        raise ValueError(f"Invalid dimensions: {r_str!r} x {c_str!r}")
    if rows < 1 or cols < 1:
        raise ValueError(f"Dimensions must be >= 1, got {rows}x{cols}")

    # Screw
    screw_data = _b64url_decode(screw_str)
    if len(screw_data) != 3:
        raise ValueError(f"Screw data must be 3 bytes, got {len(screw_data)}")
    screw_size = ScrewSize(
        diameter=screw_data[0] / 10,
        head_diameter=screw_data[1] / 10,
        head_inset=screw_data[2] / 10,
    )

    # Tiles
    tiles_data = _b64url_decode(tiles_str)
    n_tile_bits = rows * cols
    if len(tiles_data) < math.ceil(n_tile_bits / 8):
        raise ValueError("Insufficient tile data")
    tile_bits = _bytes_to_bits(tiles_data, n_tile_bits)
    tiles: list[list[bool]] = []
    for r in range(rows):
        tiles.append([tile_bits[r * cols + c] for c in range(cols)])

    # Build layout for eligibility functions
    layout = [[Tile() if t else Hole() for t in row] for row in tiles]

    # Compute eligibility
    connector_eligible = compute_eligible_connector_positions(layout)
    chamfer_eligible = compute_eligible_tile_chamfer_positions(layout)
    screw_eligible = compute_eligible_screw_positions(layout)

    # Features
    features_data = _b64url_decode(features_str)
    n_feature_bits = (rows + 1) * (cols + 1)
    if len(features_data) < math.ceil(n_feature_bits / 8):
        raise ValueError("Insufficient feature data")
    feature_bits = _bytes_to_bits(features_data, n_feature_bits)

    # Build summits
    summits: list[list[SummitFeatures]] = []
    for i in range(rows + 1):
        row: list[SummitFeatures] = []
        for j in range(cols + 1):
            bit = feature_bits[i * (cols + 1) + j]
            sf = SummitFeatures()
            if bit:
                if connector_eligible[i][j]:
                    sf.connector_angle = _connector_direction(layout, i, j)
                elif chamfer_eligible[i][j]:
                    sf.tile_chamfer = True
                elif screw_eligible[i][j]:
                    sf.screw = True
            row.append(sf)
        summits.append(row)

    return GridPlan(
        tiles=tiles,
        summits=summits,
        opengrid_type=opengrid_type,
        screw_size=screw_size,
    )
