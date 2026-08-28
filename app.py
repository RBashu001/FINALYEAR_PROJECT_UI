import os
import sys
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# Ensure root folder is always in sys.path
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

# --- Page Layout Configuration ---
st.set_page_config(
    page_title="BIM Estimation & Decision Tool",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = os.path.join(ROOT_DIR, "data", "model_data.json")

# --- Preset Configurations ---
BRICK_PRESETS = {
    "Modular Clay Brick": {"length": 190.0, "width": 90.0, "height": 90.0, "rate": 8.0},
    "Fly Ash Brick": {"length": 230.0, "width": 110.0, "height": 70.0, "rate": 6.5},
    "Concrete Block": {"length": 390.0, "width": 190.0, "height": 190.0, "rate": 38.0},
    "Custom Brick / Block": {"length": 230.0, "width": 115.0, "height": 75.0, "rate": 9.0},
}

# --- Sidebar: Dynamic Input Panel ---
with st.sidebar:
    st.header("⚙️ Model & Material Controls")

    # Model Synchronization Inspector
    st.subheader("1. BIM Model Sync")
    uploaded_file = st.file_uploader("Upload model_data.json (Override)", type=["json"])
    
    active_json_path = None
    if uploaded_file is not None:
        active_json_path = os.path.join(ROOT_DIR, "data", "temp_uploaded.json")
        with open(active_json_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("⚡ Using uploaded JSON file.")
    elif os.path.exists(DATA_PATH):
        active_json_path = DATA_PATH
        last_modified = datetime.fromtimestamp(os.path.getmtime(DATA_PATH)).strftime("%Y-%m-%d %H:%M:%S")
        st.caption(f"📁 Linked: `data/model_data.json`\n\n🕒 Exported: `{last_modified}`")
    else:
        st.error("No `model_data.json` found in `data/` folder.")

    st.markdown("---")

    # Brick Specifications
    st.subheader("2. Brick Specification")
    brick_type_label = st.selectbox("Brick Type", list(BRICK_PRESETS.keys()), index=0)
    preset = BRICK_PRESETS[brick_type_label]

    col_l, col_w, col_h = st.columns(3)
    b_len_mm = col_l.number_input("Length (mm)", value=preset["length"], step=5.0)
    b_wid_mm = col_w.number_input("Width (mm)", value=preset["width"], step=5.0)
    b_hgt_mm = col_h.number_input("Height (mm)", value=preset["height"], step=5.0)

    mortar_joint_mm = st.number_input("Mortar Joint (mm)", min_value=4.0, max_value=25.0, value=10.0, step=1.0)
    brick_mortar_ratio = st.selectbox("Masonry Mortar Mix", ["1:3", "1:4", "1:5", "1:6"], index=3)

    st.markdown("---")

    # Plaster Specifications
    st.subheader("3. Plaster Specification")
    plaster_thick_mm = st.number_input("Plaster Thickness (mm)", min_value=6.0, max_value=30.0, value=12.0, step=1.0)
    plaster_mix_ratio = st.selectbox("Plaster Mortar Mix", ["1:3", "1:4", "1:5", "1:6"], index=1)

    st.markdown("---")

    # Cost Rates
    st.subheader("4. Material & Labor Rates (₹)")
    rate_brick = st.number_input("Brick Unit Rate (₹/unit)", min_value=1.0, value=float(preset["rate"]), step=0.5)
    rate_cement = st.number_input("Cement Rate (₹/50kg bag)", min_value=100.0, value=350.0, step=10.0)
    rate_sand = st.number_input("Sand Rate (₹/m³)", min_value=100.0, value=1800.0, step=50.0)
    rate_labor_brickwork = st.number_input("Masonry Labor Rate (₹/m³)", min_value=50.0, value=500.0, step=25.0)
    rate_labor_plaster = st.number_input("Plaster Labor Rate (₹/m²)", min_value=10.0, value=120.0, step=10.0)

    st.markdown("---")

    # Productivity Rates
    st.subheader("5. Productivity & Bulking")
    prod_brickwork = st.number_input("Brickwork Output (m³/day)", min_value=0.2, value=1.5, step=0.1)
    prod_plaster = st.number_input("Plastering Output (m²/day)", min_value=1.0, value=15.0, step=1.0)
    bulking_factor = st.number_input("Dry Volume Bulking Factor", min_value=1.1, max_value=1.6, value=1.33, step=0.01)


# --- Calculation & View Execution ---
if active_json_path:
    # Build EngineConfig strictly using dataclass definitions
    config = EngineConfig(
        brick_spec=BrickSpec(
            brick_type=brick_type_label.lower().replace(" ", "_"),
            length=b_len_mm / 1000.0,
            width=b_wid_mm / 1000.0,
            height=b_hgt_mm / 1000.0,
            mortar_thickness=mortar_joint_mm / 1000.0,
        ),
        brick_mortar_mix=MixRatio.from_string(brick_mortar_ratio),
        plaster_mix=MixRatio.from_string(plaster_mix_ratio),
        plaster_thickness=plaster_thick_mm / 1000.0,
        conversion_factors=VolumeConversionFactors(
            dry_volume_factor=bulking_factor,
            cement_bag_volume_m3=0.0347,
        ),
        rates=MaterialRates(
            cement_rate_per_bag=rate_cement,
            sand_rate_per_m3=rate_sand,
            brick_rate_per_unit=rate_brick,
            labor_rate_brickwork_per_m3=rate_labor_brickwork,
            labor_rate_plaster_per_m2=rate_labor_plaster,
        ),
        productivity=ProductivityRates(
            brickwork_m3_per_day=prod_brickwork,
            plaster_m2_per_day=prod_plaster,
        ),
    )

    try:
        results = run_engine(active_json_path, config)
        summary = results["summary"]
        cost_bd = results["cost_breakdown"]
        time_bd = results["time_breakdown"]
        wall_details = results["wall_details"]
    except Exception as e:
        st.error(f"Calculation Error: {e}")
        st.stop()

    # --- Main Dashboard Header ---
    st.title("🏗️ BIM Real-Time Quantity & Cost Estimator")
    st.markdown(f"**Extracted Walls:** `{results['wall_count']} Elements` | **Calculations synced with latest Revit export**")

    # Top KPI Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Estimated Cost", f"₹{summary['cost']:,.2f}")
    m2.metric("Total Duration", f"{summary['time_days']} Days", f"Masonry: {time_bd['brickwork_days']}d | Plaster: {time_bd['plaster_days']}d")
    m3.metric("Total Bricks / Blocks", f"{summary['total_bricks']:,} units")
    m4.metric("Cement Required", f"{summary['cement_bags']:,.1f} Bags")

    st.markdown("---")

    # Charts Section
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("💰 Cost Breakdown")
        df_cost = pd.DataFrame([
            {"Category": "Bricks", "Cost (₹)": cost_bd["bricks"]},
            {"Category": "Cement", "Cost (₹)": cost_bd["cement"]},
            {"Category": "Sand", "Cost (₹)": cost_bd["sand"]},
            {"Category": "Masonry Labor", "Cost (₹)": cost_bd["brickwork_labor"]},
            {"Category": "Plaster Labor", "Cost (₹)": cost_bd["plaster_labor"]},
        ])
        fig_cost = px.pie(
            df_cost,
            names="Category",
            values="Cost (₹)",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_cost.update_traces(textposition="inside", textinfo="percent+label")
        fig_cost.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(fig_cost, use_container_width=True)

    with col_chart2:
        st.subheader("📦 Procurement & Area Quantities")
        df_qty = pd.DataFrame([
            {"Material": "Sand (m³)", "Quantity": summary["sand"]},
            {"Material": "Plaster Area (m²)", "Quantity": summary["plaster_area"]},
        ])
        fig_qty = px.bar(
            df_qty,
            x="Material",
            y="Quantity",
            text="Quantity",
            color="Material",
            color_discrete_sequence=["#2ca02c", "#1f77b4"],
        )
        fig_qty.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
        fig_qty.update_layout(margin=dict(t=20, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(fig_qty, use_container_width=True)

    st.markdown("---")

    # Bill of Quantities (BOQ) Table
    st.subheader("📋 Bill of Quantities (BOQ)")

    boq_items = [
        {
            "Category": "Masonry Units",
            "Description": f"{brick_type_label} ({int(b_len_mm)}x{int(b_wid_mm)}x{int(b_hgt_mm)} mm)",
            "Quantity": summary["total_bricks"],
            "Unit": "Nos",
            "Rate (₹)": rate_brick,
            "Total Cost (₹)": cost_bd["bricks"],
        },
        {
            "Category": "Binder",
            "Description": "Portland Cement (50kg bags)",
            "Quantity": summary["cement_bags"],
            "Unit": "Bags",
            "Rate (₹)": rate_cement,
            "Total Cost (₹)": cost_bd["cement"],
        },
        {
            "Category": "Fine Aggregate",
            "Description": "Sand / River Aggregate",
            "Quantity": summary["sand"],
            "Unit": "m³",
            "Rate (₹)": rate_sand,
            "Total Cost (₹)": cost_bd["sand"],
        },
        {
            "Category": "Labor",
            "Description": "Masonry Construction Labor",
            "Quantity": sum(w["volume_m3"] for w in wall_details),
            "Unit": "m³",
            "Rate (₹)": rate_labor_brickwork,
            "Total Cost (₹)": cost_bd["brickwork_labor"],
        },
        {
            "Category": "Labor",
            "Description": "Wall Surface Plastering Labor",
            "Quantity": summary["plaster_area"],
            "Unit": "m²",
            "Rate (₹)": rate_labor_plaster,
            "Total Cost (₹)": cost_bd["plaster_labor"],
        },
    ]

    df_boq = pd.DataFrame(boq_items)
    st.dataframe(
        df_boq.style.format({
            "Quantity": "{:,.2f}",
            "Rate (₹)": "₹{:,.2f}",
            "Total Cost (₹)": "₹{:,.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Detailed Wall Breakdown
    with st.expander("🔍 Wall-by-Wall Audit Schedule"):
        df_walls = pd.DataFrame(wall_details)
        st.dataframe(
            df_walls.style.format({
                "volume_m3": "{:,.2f}",
                "plaster_area_m2": "{:,.2f}",
                "num_bricks": "{:,}",
                "brick_mortar_dry_m3": "{:,.3f}",
                "brick_mortar_cement_bags": "{:,.2f}",
                "brick_mortar_sand_m3": "{:,.3f}",
                "plaster_dry_volume_m3": "{:,.3f}",
                "plaster_cement_bags": "{:,.2f}",
                "plaster_sand_m3": "{:,.3f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

else:
    st.warning("Awaiting `model_data.json` inside the `data/` folder...")