"""
plaster_calculator.py
-----------------------
Calculates plaster wet volume from wall area and thickness, converts it to
dry volume, and reuses `mortar_calculator` to split that dry volume into
cement and sand (plaster mortar uses the same cement:sand proportional
method as brick-laying mortar, just with its own mix ratio).
"""

from dataclasses import dataclass

from engine.models import MixRatio, VolumeConversionFactors
from engine.mortar_calculator import calculate_mortar, MortarCalculationResult


@dataclass
class PlasterCalculationResult:
    plaster_wet_volume_m3: float
    plaster_dry_volume_m3: float
    cement_bags: float
    sand_volume_m3: float


def calculate_plaster(
    wall_area_m2: float,
    plaster_thickness_m: float,
    mix_ratio: MixRatio,
    conversion_factors: VolumeConversionFactors,
) -> PlasterCalculationResult:
    """
    Args:
        wall_area_m2: Net wall area to be plastered (openings already deducted).
        plaster_thickness_m: Plaster coat thickness.
        mix_ratio: Cement:sand ratio for the plaster mix.
        conversion_factors: Holds the dry-volume bulking factor and bag volume.

    Returns:
        PlasterCalculationResult with volumes and material quantities.
    """
    if wall_area_m2 <= 0 or plaster_thickness_m <= 0:
        return PlasterCalculationResult(
            plaster_wet_volume_m3=0.0,
            plaster_dry_volume_m3=0.0,
            cement_bags=0.0,
            sand_volume_m3=0.0,
        )

    # Wet (in-place) plaster volume
    wet_volume = wall_area_m2 * plaster_thickness_m

    # Dry (procurement) plaster volume, accounting for bulking
    dry_volume = wet_volume * conversion_factors.dry_volume_factor

    mortar_result: MortarCalculationResult = calculate_mortar(
        dry_volume_m3=dry_volume,
        mix_ratio=mix_ratio,
        conversion_factors=conversion_factors,
    )

    return PlasterCalculationResult(
        plaster_wet_volume_m3=round(wet_volume, 4),
        plaster_dry_volume_m3=round(dry_volume, 4),
        cement_bags=mortar_result.cement_bags,
        sand_volume_m3=mortar_result.sand_volume_m3,
    )
