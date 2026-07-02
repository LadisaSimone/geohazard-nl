"""Smoke test for src/hazards.py — run with: python tests/test_hazards.py

Feeds the real Zeeland forecast through aggregate_windows and
detect_hazards and prints both the windowed DataFrame and hazard table.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import geo, hazards, weather


def main() -> None:
    lat, lon = geo.get_centroid("Zeeland")
    print(f"fetching forecast for Zeeland ({lat:.4f}, {lon:.4f})...")
    df = weather.fetch_forecast(lat, lon, forecast_days=7)

    now = pd.Timestamp.now(tz="UTC")
    print(f"\nforecast first row: {df.index[0]}")
    print(f"now (UTC):          {now}")

    windowed = hazards.aggregate_windows(df, now=now)
    assert list(windowed.index) == list(hazards.TIME_WINDOWS.keys())
    assert set(windowed.columns) == set(weather.HOURLY_VARIABLES)

    pd.set_option("display.width", 120)
    pd.set_option("display.max_columns", None)
    print("\n=== windowed DataFrame ===")
    print(windowed)

    hazard_table = hazards.detect_hazards(windowed)
    for record in hazard_table:
        assert set(record.keys()) == {"window", "variable", "value", "severity"}
        assert record["severity"] in ("warning", "severe")
        assert record["variable"] in hazards.THRESHOLDS

    print("\n=== hazard table ===")
    if hazard_table:
        print(pd.DataFrame(hazard_table))
    else:
        print("(no hazards detected)")

    print("\nOK: src/hazards.py verified")


if __name__ == "__main__":
    main()
