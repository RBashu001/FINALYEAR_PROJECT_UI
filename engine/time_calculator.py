"""
time_calculator.py
--------------------
Estimates activity durations from quantities and mason productivity rates.
Durations are rounded UP (ceil) since a partial day of work still consumes
a full working day on a schedule.
"""

import math
from dataclasses import dataclass

from engine.models import ProductivityRates


@dataclass
class TimeCalculationResult:
    brickwork_duration_days: int
    plaster_duration_days: int
    total_duration_days: int


def calculate_time(
    total_brick_volume_m3: float,
    total_plaster_area_m2: float,
    productivity: ProductivityRates,
) -> TimeCalculationResult:
    """
    Args:
        total_brick_volume_m3: Total wall volume to be built.
        total_plaster_area_m2: Total area to be plastered.
        productivity: Mason output rates (m3/day for brickwork, m2/day for plaster).

    Returns:
        TimeCalculationResult with per-activity and total durations (in days).
        Activities are assumed sequential (brickwork must finish before
        plaster starts on the same wall); adjust the total if the project
        allows parallel crews.
    """
    brickwork_days = (
        math.ceil(total_brick_volume_m3 / productivity.brickwork_m3_per_day)
        if productivity.brickwork_m3_per_day > 0
        else 0
    )
    plaster_days = (
        math.ceil(total_plaster_area_m2 / productivity.plaster_m2_per_day)
        if productivity.plaster_m2_per_day > 0
        else 0
    )

    return TimeCalculationResult(
        brickwork_duration_days=brickwork_days,
        plaster_duration_days=plaster_days,
        total_duration_days=brickwork_days + plaster_days,
    )
