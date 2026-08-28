"""
input_loader.py
----------------
Responsible for ONE thing: reading the BIM export (model_data.json) and
turning it into a clean list of Wall objects that the rest of the engine
can work with, without needing to know anything about JSON or file paths.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from engine.models import Wall


def load_raw_model(json_path: str) -> Dict[str, Any]:
    """Read the raw JSON file from disk and return it as a Python dict."""
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Model data file not found: {json_path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_walls(raw_model: Dict[str, Any]) -> List[Wall]:
    """
    Convert the raw 'elements' list from the BIM export into Wall objects.
    Only elements with category == "Wall" are kept; everything else
    (e.g. future categories like "Slab" or "Column") is ignored here but
    still available in raw_model for other parsers to use later.
    """
    walls: List[Wall] = []

    for element in raw_model.get("elements", []):
        if element.get("category") != "Wall":
            continue

        walls.append(
            Wall(
                id=element["id"],
                level=element.get("level", "Unknown"),
                wall_type=element.get("type", "Unknown"),
                length=float(element["length"]),
                height=float(element["height"]),
                thickness=float(element["thickness"]),
                volume=float(element["volume"]),
                gross_area=float(element["area"]),
                openings_area=float(element.get("openings_area", 0.0)),
            )
        )

    return walls


def load_walls(json_path: str) -> List[Wall]:
    """Convenience wrapper: load the file and parse walls in one call."""
    raw_model = load_raw_model(json_path)
    return parse_walls(raw_model)
