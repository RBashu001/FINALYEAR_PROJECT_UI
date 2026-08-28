import os
import sys
import json
import traceback
import pandas as pd
import plotly.express as px
import streamlit as st

# Force UTF-8 and directory resolution
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from engine.models import (
    BrickSpec,
    MixRatio,
    VolumeConversionFactors,
    MaterialRates,
    ProductivityRates,
    EngineConfig,
)
from engine.main import run_engine

DATA_PATH = os.path.join(ROOT_DIR, "data", "model_data.json")
COMMAND_PATH = os.path.join(ROOT_DIR, "data", "revit_command.json")

# --- Helper: Safe File Dispatcher ---
def send_revit_command(action_type: str, data_payload: dict):
    os.makedirs(os.path.dirname(COMMAND_PATH), exist_ok=True)
    command = {"action": action_type, "data": data_payload}
    with open(COMMAND_PATH, "w", encoding="utf-8") as f:
        json.dump(command, f, indent=2)
        f.flush()
        os.fsync(f.fileno())


def compute_cost_color(val: float, min_val: float, max_val: float) -> list:
    """Returns RGB [R, G, B] from Green (low cost) to Red (high cost)."""
    if max_val <= min_val:
        return [0, 255, 0]
    norm = max(0.0, min(1.0, (val - min_val) / (max_val - min_val)))
    r = int(255 * norm)
    g = int(255 * (1.0 - norm))
    return [r, g, 0]


st.set_page_config(page_title="BIM Cost Estimator & Revit Controller", layout="wide")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("⚙️ Project Controls")
    
    brick_type = st.selectbox("Brick Type", ["Clay Brick", "Fly Ash Brick", "Concrete Block"])
    b_len = st.number_input("Brick Length (mm)", value=190.0)
    b_wid = st.number_input("Brick Width (mm)", value=90.0)
    b_hgt = st.number_input("Brick Height (mm)", value=90.0)
    mortar_joint = st.number_input("Mortar Joint (mm)", value=10.0)
    
    st.markdown("---")
    st.subheader("💰 Material Rates (₹)")
    rate_brick = st.number_input("Brick Rate (₹/unit)", value=8.0)
    rate_cement = st.number_input("Cement Rate (₹/bag)", value=350.0)
    rate_sand = st.number_input("Sand Rate (₹/m³)", value=1800.0)
    rate_labor_brick = st.number_input("Masonry Labor (₹/m³)", value=500.0)
    rate_labor_plaster = st.number_input("Plaster Labor (₹/m²)", value=120.0)

    st.markdown("---")
    st.subheader("🕹️ Revit Remote Controls")
    col_r1, col_r2 = st.columns(2)
    btn_heatmap = col_r1.button("🔥 3D Heatmap")
    btn_reset = col_r2.button("🧹 Clear Overrides")
    btn_push_params = st.button("📝 Push Quantities to Wall Parameters")

# --- Data Verification & Engine Run ---
if not os.path.exists(DATA_PATH):
    st.error(f"❌ Cannot find `{DATA_PATH}`. Please click 'Export Model Data' in Revit to generate the file.")
else:
    try:
        config = EngineConfig(
            brick_spec=BrickSpec(
                brick_type=brick_type.lower().replace(" ", "_"),
                length=b_len / 1000.0,
                width=b_wid / 1000.0,
                height=b_hgt / 1000.0,
                mortar_thickness=mortar_joint / 1000.0,
            ),
            brick_mortar_mix=MixRatio.from_string("1:6"),
            plaster_mix=MixRatio.from_string("1:4"),
            plaster_thickness=0.012,
            conversion_factors=VolumeConversionFactors(dry_volume_factor=1.33, cement_bag_volume_m3=0.0347),
            rates=MaterialRates(
                cement_rate_per_bag=rate_cement,
                sand_rate_per_m3=rate_sand,
                brick_rate_per_unit=rate_brick,
                labor_rate_brickwork_per_m3=rate_labor_brick,
                labor_rate_plaster_per_m2=rate_labor_plaster,
            ),
            productivity=ProductivityRates(brickwork_m3_per_day=1.5, plaster_m2_per_day=15.0),
        )

        results = run_engine(DATA_PATH, config)
        summary = results.get("summary", {})
        wall_details = results.get("wall_details", [])

        # Robust wall cost calculation with key fallbacks
        processed_walls = []
        for w in wall_details:
            w_id = str(w.get("wall_id") or w.get("id") or "")
            vol = float(w.get("volume_m3") or w.get("volume") or 0.0)
            p_area = float(w.get("plaster_area_m2") or w.get("area") or 0.0)
            n_bricks = int(w.get("num_bricks") or w.get("total_bricks") or 0)
            
            # Extract cement & sand safely
            c_bags = float(w.get("brick_mortar_cement_bags", 0)) + float(w.get("plaster_cement_bags", 0))
            if c_bags == 0 and "cement_bags" in w:
                c_bags = float(w["cement_bags"])
                
            s_m3 = float(w.get("brick_mortar_sand_m3", 0)) + float(w.get("plaster_sand_m3", 0))
            if s_m3 == 0 and "sand_m3" in w:
                s_m3 = float(w["sand_m3"])

            # Compute wall cost if not already in result
            wall_cost = float(w.get("total_wall_cost") or w.get("cost") or (
                (n_bricks * rate_brick) +
                (c_bags * rate_cement) +
                (s_m3 * rate_sand) +
                (vol * rate_labor_brick) +
                (p_area * rate_labor_plaster)
            ))

            processed_walls.append({
                "wall_id": w_id,
                "volume_m3": round(vol, 3),
                "plaster_area_m2": round(p_area, 2),
                "num_bricks": n_bricks,
                "total_wall_cost": round(wall_cost, 2),
            })

        # --- Handle Remote Revit Actions ---
        if btn_heatmap:
            if processed_walls:
                all_costs = [pw["total_wall_cost"] for pw in processed_walls]
                min_c, max_c = min(all_costs), max(all_costs)
                
                overrides = [
                    {
                        "wall_id": pw["wall_id"],
                        "rgb": compute_cost_color(pw["total_wall_cost"], min_c, max_c)
                    }
                    for pw in processed_walls
                ]
                send_revit_command("HEATMAP", {"wall_overrides": overrides})
                st.sidebar.success(f"🚀 Heatmap written! ({len(overrides)} walls)")

        if btn_reset:
            all_ids = [pw["wall_id"] for pw in processed_walls]
            send_revit_command("RESET_VIEW", {"wall_ids": all_ids})
            st.sidebar.info("🧹 Reset command sent to Revit!")

        if btn_push_params:
            records = [
                {
                    "wall_id": pw["wall_id"],
                    "cost": pw["total_wall_cost"],
                    "num_bricks": pw["num_bricks"],
                    "plaster_m2": pw["plaster_area_m2"]
                }
                for pw in processed_walls
            ]
            send_revit_command("WRITE_PARAMETERS", {"wall_records": records})
            st.sidebar.success(f"📝 Parameters queued for {len(records)} walls!")

        # --- Main Dashboard Visuals ---
        st.title("🏗️ BIM Real-Time Estimator & Revit Controller")

        tot_cost = summary.get("cost") or summary.get("total_cost", 0.0)
        tot_time = summary.get("time_days") or summary.get("total_days", 0)
        tot_bricks = summary.get("total_bricks") or summary.get("num_bricks", 0)
        tot_cement = summary.get("cement_bags") or summary.get("total_cement_bags", 0.0)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Cost", f"₹{tot_cost:,.2f}")
        c2.metric("Total Duration", f"{tot_time} Days")
        c3.metric("Total Bricks", f"{tot_bricks:,} units")
        c4.metric("Cement Required", f"{tot_cement:,.1f} Bags")

        st.markdown("---")

        st.subheader("Wall Cost Audit Table")
        df_display = pd.DataFrame(processed_walls)
        st.dataframe(df_display, use_container_width=True)

    except Exception as err:
        st.error(f"⚠️ Calculation Engine Error: {err}")
        st.code(traceback.format_exc())
