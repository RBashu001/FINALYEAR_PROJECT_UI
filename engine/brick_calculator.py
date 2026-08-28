"""
brick_calculator.py
--------------------
Calculates how many bricks are needed for a given wall volume, plus the
resulting wet and dry mortar volumes, using the standard "brick with mortar
envelope" method:

    1. Each brick occupies a larger "effective" volume once the mortar
       joint around it is included (mortar_thickness added to each
       dimension of the brick).
    2. Number of bricks = wall volume / effective brick volume.
    3. Mortar (wet) volume = wall volume - (number of bricks x actual brick volume).
    4. Dry mortar volume = wet mortar volume x dry_volume_factor
       (accounts for the fact that dry, loose materials occupy more volume
       than the same materials once mixed with water and compacted).
"""

from dataclasses import dataclass

from engine.models import BrickSpec, VolumeConversionFactors


@dataclass
class BrickCalculationResult:
    brick_type: str
    num_bricks: int
    wet_mortar_volume_m3: float
    dry_mortar_volume_m3: float


def calculate_bricks(
    wall_volume_m3: float,
    brick_spec: BrickSpec,
    conversion_factors: VolumeConversionFactors,
) -> BrickCalculationResult:
    """
    Args:
        wall_volume_m3: Net volume of the wall (openings already deducted).
        brick_spec: Brick type, dimensions, and mortar joint thickness.
        conversion_factors: Holds the dry-volume bulking factor.

    Returns:
        BrickCalculationResult with brick count and mortar volumes.
    """
    if wall_volume_m3 <= 0:
        return BrickCalculationResult(
            brick_type=brick_spec.brick_type,
            num_bricks=0,
            wet_mortar_volume_m3=0.0,
            dry_mortar_volume_m3=0.0,
        )

    # Actual volume of a single brick (no mortar)
    actual_brick_volume = brick_spec.length * brick_spec.width * brick_spec.height

    # Effective volume occupied by one brick once its mortar joint is included
    effective_brick_volume = (
        (brick_spec.length + brick_spec.mortar_thickness)
        * (brick_spec.width + brick_spec.mortar_thickness)
        * (brick_spec.height + brick_spec.mortar_thickness)
    )

    # Number of bricks needed to fill the wall volume
    raw_brick_count = wall_volume_m3 / effective_brick_volume
    num_bricks = int(round(raw_brick_count))

    # Volume actually taken up by bricks (using the rounded brick count)
    volume_occupied_by_bricks = num_bricks * actual_brick_volume

    # Remaining volume is filled with mortar (wet / in-place volume)
    wet_mortar_volume = max(wall_volume_m3 - volume_occupied_by_bricks, 0.0)

    # Convert wet mortar volume to dry (procurement) volume
    dry_mortar_volume = wet_mortar_volume * conversion_factors.dry_volume_factor

    return BrickCalculationResult(
        brick_type=brick_spec.brick_type,
        num_bricks=num_bricks,
        wet_mortar_volume_m3=round(wet_mortar_volume, 4),
        dry_mortar_volume_m3=round(dry_mortar_volume, 4),
    )
