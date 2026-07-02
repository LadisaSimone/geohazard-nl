"""Pre-generate company hazard narratives — run with: python scripts/generate_narratives.py

Standalone, local-only script. Reads ANTHROPIC_API_KEY from .env (via
src.narrative's load_dotenv()), loops over every company in
src/companies.py, fetches the live forecast, computes the six-window
hazard report, calls the Claude API once per company, and writes
everything to data/narratives.json.

The deployed Streamlit app reads that static file and never calls the
Claude API itself — no ANTHROPIC_API_KEY needed at deploy time. Re-run
this script locally whenever narratives need refreshing.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import companies, hazards, narrative, weather

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "narratives.json"


def main() -> None:
    result = {}

    for company in companies.COMPANIES:
        name = company["name"]
        print(f"Fetching forecast + generating narrative for {name}...")

        df = weather.fetch_forecast(company["lat"], company["lon"], forecast_days=7)
        windowed = hazards.aggregate_windows(df)
        report = hazards.full_window_report(windowed, company["thresholds"])
        hazard_table = [
            {"window": entry["window"], **hazard}
            for entry in report
            for hazard in entry["hazards"]
        ]

        text = narrative.generate_narrative(name, company["description"], hazard_table)

        result[name] = {
            "narrative": text,
            "hazard_windows": report,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, default=str))
    print(f"\nWrote {len(result)} companies to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
