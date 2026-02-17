"""Data types for the grid preparation phase."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

DEFAULT_SCREW_DIAMETER = 4.2
DEFAULT_SCREW_HEAD_DIAMETER = 8.0
DEFAULT_SCREW_HEAD_INSET = 1.0

LITE_DEFAULT_SCREW_DIAMETER = 4.1
LITE_DEFAULT_SCREW_HEAD_DIAMETER = 7.2
LITE_DEFAULT_SCREW_HEAD_INSET = 1.0


class ScrewSize(BaseModel):
    model_config = ConfigDict(frozen=True)

    diameter: float = DEFAULT_SCREW_DIAMETER
    head_diameter: float = DEFAULT_SCREW_HEAD_DIAMETER
    head_inset: float = DEFAULT_SCREW_HEAD_INSET


class SummitFeatures(BaseModel):
    """What to draw at a single summit (intersection of 4 cells)."""

    connector_angle: float | None = None  # None = no connector, float = Z-rotation degrees
    tile_chamfer: bool = False
    screw: bool = False


class GridPlan(BaseModel):
    """Exhaustive specification of what to draw."""

    tiles: list[list[bool]]  # rows x cols, True = place tile
    summits: list[list[SummitFeatures]]  # (rows+1) x (cols+1) features
    opengrid_type: Literal["full", "light"] = "full"
    screw_size: ScrewSize = ScrewSize()

    @model_validator(mode="after")
    def check_dimensions(self) -> "GridPlan":
        # Check tiles is rectangular
        if self.tiles:
            cols = len(self.tiles[0])
            for i, row in enumerate(self.tiles):
                if len(row) != cols:
                    raise ValueError(
                        f"tiles is not rectangular: row 0 has {cols} columns "
                        f"but row {i} has {len(row)}"
                    )
        else:
            cols = 0

        rows = len(self.tiles)

        # Check summits is rectangular
        if self.summits:
            summit_cols = len(self.summits[0])
            for i, row in enumerate(self.summits):
                if len(row) != summit_cols:
                    raise ValueError(
                        f"summits is not rectangular: row 0 has {summit_cols} columns "
                        f"but row {i} has {len(row)}"
                    )
        else:
            summit_cols = 0

        summit_rows = len(self.summits)

        # Check summits is (rows+1) x (cols+1)
        if summit_rows != rows + 1:
            raise ValueError(
                f"summits has {summit_rows} rows but expected {rows + 1} (tiles has {rows} rows)"
            )
        if summit_cols != cols + 1:
            raise ValueError(
                f"summits has {summit_cols} columns but expected {cols + 1} "
                f"(tiles has {cols} columns)"
            )

        return self
