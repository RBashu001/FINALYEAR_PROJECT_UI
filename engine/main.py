# engine/main.py
from typing import Dict, Any, List
from engine.models import Wall, EngineConfig
from engine.input_loader import load_walls
from engine.brick_calculator import calculate_bricks
from engine.mortar_calculator import calculate_mortar
from engine.plaster_calculator import calculate_plaster
from engine.cost_calculator import calculate_cost
from engine.time_calculator import calculate_time


def process_wall(wall: Wall, config: EngineConfig) -> Dict[str, Any]:
    brick_result = calculate_bricks(
        wall_volume_m3=wall.volume,
        brick_spec=config.brick_spec,
        conversion_factors=config.conversion_factors,
    )

    brick_mortar_result = calculate_mortar(
        dry_volume_m3=brick_result.dry_mortar_volume_m3,
        mix_ratio=config.brick_mortar_mix,
        conversion_factors=config.conversion_factors,
    )

    plaster_result = calculate_plaster(
        wall_area_m2=wall.net_plaster_area,
        plaster_thickness_m=config.plaster_thickness,
        mix_ratio=config.plaster_mix,
        conversion_factors=config.conversion_factors,
    )

    return {
        "wall_id": wall.id,
        "level": wall.level,
        "wall_type": wall.wall_type,
        "volume_m3": wall.volume,
        "plaster_area_m2": wall.net_plaster_area,
        "num_bricks": brick_result.num_bricks,
        "brick_mortar_dry_m3": brick_result.dry_mortar_volume_m3,
        "brick_mortar_cement_bags": brick_mortar_result.cement_bags,
        "brick_mortar_sand_m3": brick_mortar_result.sand_volume_m3,
        "plaster_dry_volume_m3": plaster_result.plaster_dry_volume_m3,
        "plaster_cement_bags": plaster_result.cement_bags,
        "plaster_sand_m3": plaster_result.sand_volume_m3,
    }


def aggregate_wall_results(wall_results: List[Dict[str, Any]]) -> Dict[str, float]:
    totals = {
        "total_bricks": 0,
        "total_wall_volume_m3": 0.0,
        "total_plaster_area_m2": 0.0,
        "total_cement_bags": 0.0,
        "total_sand_m3": 0.0,
    }

    for row in wall_results:
        totals["total_bricks"] += row["num_bricks"]
        totals["total_wall_volume_m3"] += row["volume_m3"]
        totals["total_plaster_area_m2"] += row["plaster_area_m2"]
        totals["total_cement_bags"] += row["brick_mortar_cement_bags"] + row["plaster_cement_bags"]
        totals["total_sand_m3"] += row["brick_mortar_sand_m3"] + row["plaster_sand_m3"]

    return totals


def run_engine(model_json_path: str, config: EngineConfig) -> Dict[str, Any]:
    walls = load_walls(model_json_path)
    wall_results = [process_wall(wall, config) for wall in walls]
    totals = aggregate_wall_results(wall_results)

    cost_result = calculate_cost(
        total_bricks=totals["total_bricks"],
        total_cement_bags=totals["total_cement_bags"],
        total_sand_m3=totals["total_sand_m3"],
        total_brick_volume_m3=totals["total_wall_volume_m3"],
        total_plaster_area_m2=totals["total_plaster_area_m2"],
        rates=config.rates,
    )

    time_result = calculate_time(
        total_brick_volume_m3=totals["total_wall_volume_m3"],
        total_plaster_area_m2=totals["total_plaster_area_m2"],
        productivity=config.productivity,
    )

    summary = {
        "total_bricks": totals["total_bricks"],
        "cement_bags": round(totals["total_cement_bags"], 2),
        "sand": round(totals["total_sand_m3"], 4),
        "plaster_area": round(totals["total_plaster_area_m2"], 4),
        "cost": cost_result.total_cost,
        "time_days": time_result.total_duration_days,
    }

    return {
        "summary": summary,
        "cost_breakdown": cost_result.breakdown,
        "time_breakdown": {
            "brickwork_days": time_result.brickwork_duration_days,
            "plaster_days": time_result.plaster_duration_days,
        },
        "wall_count": len(walls),
        "wall_details": wall_results,
    }