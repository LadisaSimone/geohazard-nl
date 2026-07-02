"""GeoHazard NL — Streamlit entrypoint.

Thin orchestration layer: loads the company registry, live forecasts,
and hazard windows from src/, then renders the map (all six companies)
and a single-company detail view driven by a dropdown. Narrative text
is NOT generated live — it's pre-generated locally by
scripts/generate_narratives.py and committed to data/narratives.json,
so the deployed app never needs an ANTHROPIC_API_KEY. Business logic
lives in src/.
"""

import json
from pathlib import Path

import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium

from src import companies, hazards, weather

CACHE_TTL_SECONDS = 1800
STATUS_COLORS = {"clear": "blue", "warning": "orange", "severe": "red"}
STATUS_BADGES = {"clear": "🟢 CLEAR", "warning": "🟠 WARNING", "severe": "🔴 SEVERE"}
_SEVERITY_RANK = {"clear": 0, "warning": 1, "severe": 2}

NARRATIVES_PATH = Path(__file__).resolve().parent / "data" / "narratives.json"

COMPANIES_BY_NAME = {company["name"]: company for company in companies.COMPANIES}

st.set_page_config(page_title="GeoHazard NL", layout="wide")
st.title("GeoHazard Intelligence Platform — NL")
st.caption("Company hazard monitoring across six fixed operating sites")


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_company_report(company_name: str) -> list[dict]:
    """Fetch the live forecast and compute the six-window hazard report for one company."""
    company = COMPANIES_BY_NAME[company_name]
    df = weather.fetch_forecast(company["lat"], company["lon"], forecast_days=7)
    windowed = hazards.aggregate_windows(df)
    return hazards.full_window_report(windowed, company["thresholds"])


@st.cache_data
def load_narratives() -> dict:
    """Load pre-generated narratives written by scripts/generate_narratives.py.

    Static data — no ANTHROPIC_API_KEY needed at deploy time. Missing
    file (e.g. before the script has ever been run) yields an empty
    dict, handled gracefully at the call site.
    """
    if not NARRATIVES_PATH.exists():
        return {}
    return json.loads(NARRATIVES_PATH.read_text())


def worst_status(report: list[dict]) -> str:
    worst = "clear"
    for entry in report:
        if _SEVERITY_RANK[entry["status"]] > _SEVERITY_RANK[worst]:
            worst = entry["status"]
    return worst


# --- Map: all six companies, colored by current worst status ---

company_statuses: dict[str, str] = {}
company_errors: dict[str, str] = {}

for company in companies.COMPANIES:
    try:
        report = get_company_report(company["name"])
        company_statuses[company["name"]] = worst_status(report)
    except Exception as exc:
        company_errors[company["name"]] = str(exc)

fmap = folium.Map()
for company in companies.COMPANIES:
    name = company["name"]
    status = company_statuses.get(name)
    color = STATUS_COLORS.get(status, "gray") if status else "gray"
    tooltip = f"{name} — {status or 'error fetching forecast'}"
    folium.Marker(
        location=[company["lat"], company["lon"]],
        popup=name,
        tooltip=tooltip,
        icon=folium.Icon(color=color),
    ).add_to(fmap)

fmap.fit_bounds([(c["lat"], c["lon"]) for c in companies.COMPANIES], padding=(30, 30))
st_folium(fmap, height=450, use_container_width=True, returned_objects=[])

# --- Single-company detail view ---

selected_name = st.selectbox("Select company", [c["name"] for c in companies.COMPANIES])
selected_company = COMPANIES_BY_NAME[selected_name]

st.subheader(selected_name)
st.caption(selected_company["description"])

if selected_name in company_errors:
    st.error(f"Could not fetch forecast for {selected_name}: {company_errors[selected_name]}")
    st.stop()

report = get_company_report(selected_name)

st.markdown("**Thresholds**")
threshold_rows = [
    {"variable": variable, "warning": limits["warning"], "severe": limits["severe"], "unit": limits["unit"]}
    for variable, limits in selected_company["thresholds"].items()
]
st.table(pd.DataFrame(threshold_rows))

st.markdown("**Forecast windows**")
for entry in report:
    st.markdown(f"**{entry['window']}** — {STATUS_BADGES[entry['status']]}")
    if entry["hazards"]:
        for hazard in entry["hazards"]:
            st.markdown(f"- {hazard['variable']}: {hazard['value']} ({hazard['severity']})")
    else:
        st.markdown("No hazard")

st.markdown("**Narrative**")
narratives = load_narratives()
narrative_entry = narratives.get(selected_name)
if narrative_entry:
    st.markdown(narrative_entry["narrative"])
    st.caption(f"Narrative generated: {narrative_entry['generated_at']}")
else:
    st.warning(
        f"No pre-generated narrative available for {selected_name}. "
        "Run scripts/generate_narratives.py locally to produce one."
    )
