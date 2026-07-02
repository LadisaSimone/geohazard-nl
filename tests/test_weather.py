"""Smoke test for src/weather.py — run with: python tests/test_weather.py

Verifies the Open-Meteo fetch works end to end and the returned DataFrame
has the expected shape, using the real province centroids from src/geo.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import geo, weather


def main() -> None:
    for province in geo.PROVINCES:
        lat, lon = geo.get_centroid(province)
        print(f"fetching forecast for {province} ({lat:.4f}, {lon:.4f})...")

        df = weather.fetch_forecast(lat, lon, forecast_days=7)

        assert list(df.columns) == weather.HOURLY_VARIABLES, df.columns.tolist()
        assert df.index.is_monotonic_increasing
        assert df.index.name == "time"

        expected_hours = 24 * 7
        assert len(df) in (expected_hours, expected_hours + 1), len(df)

        assert not df.isnull().all().any(), "found an all-null column"

        print(f"  {len(df)} hourly rows, span {df.index[0]} -> {df.index[-1]}")
        print(f"  sample row:\n{df.iloc[0]}")

    print("OK: src/weather.py verified")


if __name__ == "__main__":
    main()
