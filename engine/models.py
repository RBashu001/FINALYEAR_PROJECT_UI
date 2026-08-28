"""
models.py
---------
Plain data structures used across the calculation engine.

Keeping these as dataclasses (instead of raw dicts) gives:
- IDE autocomplete / type checking
- A single, obvious place to see what a "Wall" or a "Config" looks like
- Easy conversion to/from dict when a UI needs to serialize them (JSON, forms, etc.)
"""

from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Geometry (comes from the BIM export / model_data.json)
# ---------------------------------------------------------------------------

@dataclass
class Wall:
    """A single wall element extracted from the BIM model export."""
    id: str
    level: str
    wall_type: str
    length: float          # m
    height: float          # m
    thickness: float       # m
    volume: float          # m3 (net of openings, as exported by BIM tool)
    gross_area: float      # m2 (already net of openings, per model export convention)
    openings_area: float   # m2 (area of doors/windows/etc. subtracted from gross)

    @property
    def net_plaster_area(self) -> float:
        """
        Area actually available for plastering.
        The model export already deducts openings from `gross_area`, but this
        property exists so that, if a project's export convention differs,
        only this one line needs to change.
        """
        return self.gross_area


# ---------------------------------------------------------------------------
# User-configurable inputs (NOTHING here is a hardcoded formula constant -
# these are parameters the calling code / UI must supply)
# ---------------------------------------------------------------------------

@dataclass
class BrickSpec:
    """Physical brick properties and the brick type used for classification."""
    brick_type: str         # "clay" | "fly_ash" | "concrete" (informational / for reporting)
    length: float            # m
    width: float             # m
    height: float            # m
    mortar_thickness: float  # m, applied on all sides of the brick in the wall


@dataclass
class MixRatio:
    """A cement:sand mix ratio, e.g. 1:4 -> cement_part=1, sand_part=4."""
    cement_part: float
    sand_part: float

    @property
    def total_parts(self) -> float:
        return self.cement_part + self.sand_part

    @classmethod
    def from_string(cls, ratio_str: str) -> "MixRatio":
        """Build a MixRatio from a string like '1:4' or '1:6'."""
        cement_str, sand_str = ratio_str.split(":")
        return cls(cement_part=float(cement_str), sand_part=float(sand_str))


@dataclass
class VolumeConversionFactors:
    """
    Conversion factors needed to go from wet (mixed, in-place) volume to
    dry (before-mixing, procurement) volume, and from cement volume to bags.
    These vary by project/specification, so they are supplied, not fixed.
    """
    dry_volume_factor: float      # e.g. 1.30-1.33 typical bulking allowance
    cement_bag_volume_m3: float   # volume of one cement bag in m3 (depends on bag weight & density)


@dataclass
class MaterialRates:
    """Unit rates used for costing. Currency-agnostic; caller decides the unit."""
    cement_rate_per_bag: float
    sand_rate_per_m3: float
    brick_rate_per_unit: float
    labor_rate_brickwork_per_m3: float
    labor_rate_plaster_per_m2: float


@dataclass
class ProductivityRates:
    """Mason output rates used for scheduling."""
    brickwork_m3_per_day: float
    plaster_m2_per_day: float


@dataclass
class EngineConfig:
    """
    Bundles all user-supplied parameters needed to run the engine end-to-end.
    A UI would typically build one of these from form inputs.
    """
    brick_spec: BrickSpec
    brick_mortar_mix: MixRatio
    plaster_mix: MixRatio
    plaster_thickness: float          # m
    conversion_factors: VolumeConversionFactors
    rates: MaterialRates
    productivity: ProductivityRates
