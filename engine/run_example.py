"""
run_example.py
----------------
Example of how to configure and run the engine end-to-end.

All project-specific numbers (brick size, mix ratios, rates, productivity)
live HERE as plain parameters - not hardcoded inside the calculators.
A UI would replace this file with form inputs feeding the same EngineConfig.
"""

import json

from models import (
    BrickSpec,
    MixRatio,
    VolumeConversionFactors,
    MaterialRates,
    ProductivityRates,
    EngineConfig,
)
from main import run_engine


def build_config() -> EngineConfig:
    """Example configuration - replace values with real project inputs / UI form data."""

    brick_spec = BrickSpec(
        brick_type="clay",          # "clay" | "fly_ash" | "concrete"
        length=0.19,                 # m (e.g. 190mm standard clay brick)
        width=0.09,                  # m
        height=0.09,                 # m
        mortar_thickness=0.01,       # m (10mm mortar joint)
    )

    brick_mortar_mix = MixRatio.from_string("1:6")   # cement:sand for brickwork mortar
    plaster_mix = MixRatio.from_string("1:4")        # cement:sand for plaster
    plaster_thickness = 0.012                         # m (12mm plaster coat)

    conversion_factors = VolumeConversionFactors(
        dry_volume_factor=1.33,        # dry material bulking allowance
        cement_bag_volume_m3=0.0347,   # volume of a 50kg cement bag at 1440 kg/m3
    )

    rates = MaterialRates(
        cement_rate_per_bag=350.0,
        sand_rate_per_m3=1800.0,
        brick_rate_per_unit=8.0,
        labor_rate_brickwork_per_m3=500.0,
        labor_rate_plaster_per_m2=120.0,
    )

    productivity = ProductivityRates(
        brickwork_m3_per_day=1.5,
        plaster_m2_per_day=15.0,
    )

    return EngineConfig(
        brick_spec=brick_spec,
        brick_mortar_mix=brick_mortar_mix,
        plaster_mix=plaster_mix,
        plaster_thickness=plaster_thickness,
        conversion_factors=conversion_factors,
        rates=rates,
        productivity=productivity,
    )


if __name__ == "__main__":
    config = build_config()
    result = run_engine("model_data.json", config)

    print(json.dumps(result["summary"], indent=2))
    print("\nCost breakdown:", json.dumps(result["cost_breakdown"], indent=2))
    print("\nTime breakdown:", json.dumps(result["time_breakdown"], indent=2))
    print(f"\nProcessed {result['wall_count']} walls.")
