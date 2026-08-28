"""
cost_calculator.py
--------------------
Turns material/labor quantities into a cost breakdown and total, using
rates supplied by the caller. Kept generic (works on plain quantities)
so it can be reused for brickwork, plaster, or any future activity.
"""

from dataclasses import dataclass, field
from typing import Dict

from engine.models import MaterialRates


@dataclass
class CostBreakdown:
    cement_cost: float
    sand_cost: float
    brick_cost: float
    brickwork_labor_cost: float
    plaster_labor_cost: float
    total_cost: float
    breakdown: Dict[str, float] = field(default_factory=dict)


def calculate_cost(
    total_bricks: int,
    total_cement_bags: float,
    total_sand_m3: float,
    total_brick_volume_m3: float,
    total_plaster_area_m2: float,
    rates: MaterialRates,
) -> CostBreakdown:
    """
    Args:
        total_bricks: Total number of bricks required across the project.
        total_cement_bags: Total cement bags required (brickwork + plaster).
        total_sand_m3: Total sand volume required (brickwork + plaster).
        total_brick_volume_m3: Total wall volume being built (for labor costing).
        total_plaster_area_m2: Total area being plastered (for labor costing).
        rates: Unit rates for each material/labor item.

    Returns:
        CostBreakdown with itemized costs and the grand total.
    """
    cement_cost = total_cement_bags * rates.cement_rate_per_bag
    sand_cost = total_sand_m3 * rates.sand_rate_per_m3
    brick_cost = total_bricks * rates.brick_rate_per_unit
    brickwork_labor_cost = total_brick_volume_m3 * rates.labor_rate_brickwork_per_m3
    plaster_labor_cost = total_plaster_area_m2 * rates.labor_rate_plaster_per_m2

    total_cost = (
        cement_cost + sand_cost + brick_cost + brickwork_labor_cost + plaster_labor_cost
    )

    breakdown = {
        "cement": round(cement_cost, 2),
        "sand": round(sand_cost, 2),
        "bricks": round(brick_cost, 2),
        "brickwork_labor": round(brickwork_labor_cost, 2),
        "plaster_labor": round(plaster_labor_cost, 2),
    }

    return CostBreakdown(
        cement_cost=round(cement_cost, 2),
        sand_cost=round(sand_cost, 2),
        brick_cost=round(brick_cost, 2),
        brickwork_labor_cost=round(brickwork_labor_cost, 2),
        plaster_labor_cost=round(plaster_labor_cost, 2),
        total_cost=round(total_cost, 2),
        breakdown=breakdown,
    )
