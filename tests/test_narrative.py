"""Smoke test for src/narrative.py — run with: python tests/test_narrative.py

Calls generate_narrative with the real Zeeland hazard table (recomputed
live from geo + weather + hazards), prints the generated narrative, then
calls it again with the same hazard_table and confirms the cache is hit
(no new API call) by mocking the client and asserting it's never invoked.
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import geo, hazards, narrative, weather

ZEELAND_DESCRIPTION = "Southwest coast of the Netherlands, with North Sea and Delta exposure."


def main() -> None:
    if narrative.CACHE_PATH.exists():
        narrative.CACHE_PATH.unlink()
        print(f"removed stale cache at {narrative.CACHE_PATH}")

    lat, lon = geo.get_centroid("Zeeland")
    df = weather.fetch_forecast(lat, lon, forecast_days=7)
    windowed = hazards.aggregate_windows(df)
    hazard_table = hazards.detect_hazards(windowed)
    print(f"hazard_table for Zeeland ({len(hazard_table)} records):")
    for record in hazard_table:
        print(f"  {record}")

    print("\n=== calling generate_narrative (first call, real API) ===")
    start = time.monotonic()
    text = narrative.generate_narrative("Zeeland", ZEELAND_DESCRIPTION, hazard_table)
    first_elapsed = time.monotonic() - start
    assert isinstance(text, str) and text.strip(), "expected non-empty narrative text"
    print(f"\n--- generated narrative ({first_elapsed:.2f}s) ---\n{text}\n---")

    cache = narrative._load_cache()
    cache_key = narrative._cache_key("Zeeland", hazard_table)
    assert cache_key in cache, "expected narrative to be written to disk cache"
    assert cache[cache_key] == text
    print(f"cache file has {len(cache)} entr{'y' if len(cache) == 1 else 'ies'}")

    print("\n=== calling generate_narrative again with a mocked client ===")
    mock_client = MagicMock()
    second_text = narrative.generate_narrative(
        "Zeeland", ZEELAND_DESCRIPTION, hazard_table, client=mock_client
    )
    mock_client.messages.create.assert_not_called()
    assert second_text == text, "expected cached narrative to match the first call"
    print("OK: second call hit the cache — mock client's messages.create was never invoked")

    print("\nOK: src/narrative.py verified")


if __name__ == "__main__":
    main()
