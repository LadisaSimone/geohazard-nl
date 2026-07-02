"""Smoke test for src/geo.py — run with: python tests/test_geo.py

Verifies the PDOK fetch + cache + centroid extraction actually work end to end.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import geo

# Rough Netherlands bounding box (WGS84) to sanity-check centroid values.
NL_LAT_RANGE = (50.5, 53.6)
NL_LON_RANGE = (3.0, 7.3)


def main() -> None:
    if geo.CACHE_PATH.exists():
        geo.CACHE_PATH.unlink()
        print(f"removed stale cache at {geo.CACHE_PATH}")

    print("fetching province boundaries from PDOK...")
    gdf = geo.fetch_provincie_boundaries()
    assert set(gdf["statnaam"]) == set(geo.PROVINCES), gdf["statnaam"].tolist()
    print(f"fetched {len(gdf)} provinces: {sorted(gdf['statnaam'])}")

    assert geo.CACHE_PATH.exists(), "expected cache file to be written"
    print(f"cache written to {geo.CACHE_PATH}")

    print("re-loading from cache (should not hit network)...")
    cached_gdf = geo.fetch_provincie_boundaries()
    assert len(cached_gdf) == len(gdf)

    for province in geo.PROVINCES:
        lat, lon = geo.get_centroid(province)
        print(f"{province}: lat={lat:.4f}, lon={lon:.4f}")
        assert NL_LAT_RANGE[0] < lat < NL_LAT_RANGE[1], f"{province} lat out of range: {lat}"
        assert NL_LON_RANGE[0] < lon < NL_LON_RANGE[1], f"{province} lon out of range: {lon}"

    try:
        geo.get_centroid("Limburg")
    except ValueError:
        print("get_centroid correctly rejects a province outside PROVINCES")
    else:
        raise AssertionError("expected ValueError for unsupported province")

    print("OK: src/geo.py verified")


if __name__ == "__main__":
    main()
