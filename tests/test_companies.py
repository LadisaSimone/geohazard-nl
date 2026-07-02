"""Smoke test for src/companies.py — run with: python tests/test_companies.py

Loops over all six companies, fetches their forecast, aggregates windows,
and prints the full_window_report() for each — all six windows always
listed, including the "clear" ones.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import companies, hazards, weather


def main() -> None:
    assert len(companies.COMPANIES) == 6

    for company in companies.COMPANIES:
        name = company["name"]
        lat, lon = company["lat"], company["lon"]
        print(f"\n=== {name} ({lat}, {lon}) — {company['description']} ===")

        df = weather.fetch_forecast(lat, lon, forecast_days=7)
        windowed = hazards.aggregate_windows(df)
        report = hazards.full_window_report(windowed, company["thresholds"])

        assert len(report) == 6, f"expected 6 windows, got {len(report)}"
        assert [r["window"] for r in report] == list(hazards.TIME_WINDOWS.keys())
        assert all(r["status"] in ("clear", "warning", "severe") for r in report)

        for entry in report:
            print(f"  {entry['window']:>6}  status={entry['status']:<7}  hazards={entry['hazards']}")

    print("\nOK: src/companies.py + full_window_report verified")


if __name__ == "__main__":
    main()
