"""
mortar_calculator.py
---------------------
Splits a dry mortar volume into cement and sand quantities based on a
mix ratio (e.g. 1:4, 1:6), using the standard proportional-parts method:

    cement_volume = dry_volume x (cement_part / total_parts)
    sand_volume   = dry_volume x (sand_part   / total_parts)
    cement_bags   = cement_volume / volume_of_one_bag
"""

from dataclasses import dataclass

from engine.models import MixRatio, VolumeConversionFactors


@dataclass
class MortarCalculationResult:
    cement_volume_m3: float
    cement_bags: float
    sand_volume_m3: float


def calculate_mortar(
    dry_volume_m3: float,
    mix_ratio: MixRatio,
    conversion_factors: VolumeConversionFactors,
) -> MortarCalculationResult:
    """
    Args:
        dry_volume_m3: Dry mortar volume to be split into materials.
        mix_ratio: Cement:sand ratio (e.g. 1:4).
        conversion_factors: Holds the volume of a single cement bag.

    Returns:
        MortarCalculationResult with cement (volume + bags) and sand volume.
    """
    if dry_volume_m3 <= 0:
        return MortarCalculationResult(cement_volume_m3=0.0, cement_bags=0.0, sand_volume_m3=0.0)

    total_parts = mix_ratio.total_parts

    cement_volume = dry_volume_m3 * (mix_ratio.cement_part / total_parts)
    sand_volume = dry_volume_m3 * (mix_ratio.sand_part / total_parts)

    cement_bags = cement_volume / conversion_factors.cement_bag_volume_m3

    return MortarCalculationResult(
        cement_volume_m3=round(cement_volume, 4),
        cement_bags=round(cement_bags, 2),
        sand_volume_m3=round(sand_volume, 4),
    )
