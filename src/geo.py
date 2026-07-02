"""Load the Groningen and Zeeland province boundaries and extract centroids.

Source: PDOK "CBS Gebiedsindelingen" dataset, provincie_gegeneraliseerd layer.
https://api.pdok.nl/cbs/gebiedsindelingen/ogc/v1

The OGC API item endpoint has no server-side attribute filter (a `statnaam=`
query param is rejected with 400), and the collection only has 132 features
total (12 provinces x 11 years), so we fetch everything in one page
(limit=1000 comfortably covers it) and filter client-side.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import requests

PROVINCES = ["Groningen", "Zeeland"]

OGC_API_BASE = "https://api.pdok.nl/cbs/gebiedsindelingen/ogc/v1"
COLLECTION = "provincie_gegeneraliseerd"
ITEMS_URL = f"{OGC_API_BASE}/collections/{COLLECTION}/items"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_PATH = DATA_DIR / "provincies.gpkg"

REQUEST_TIMEOUT = 30


def fetch_provincie_boundaries(force_refresh: bool = False) -> gpd.GeoDataFrame:
    """Return province boundaries for Groningen and Zeeland as a GeoDataFrame in WGS84.

    Cached to data/provincies.gpkg on first run; subsequent calls load from
    the cache unless force_refresh is True.
    """
    if CACHE_PATH.exists() and not force_refresh:
        return gpd.read_file(CACHE_PATH)

    gdf = _fetch_from_pdok()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    gdf.to_file(CACHE_PATH, driver="GPKG")
    return gdf


def _fetch_from_pdok() -> gpd.GeoDataFrame:
    response = requests.get(
        ITEMS_URL,
        params={"f": "json", "limit": 1000},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    geojson = response.json()

    gdf = gpd.GeoDataFrame.from_features(geojson["features"], crs="EPSG:4326")
    gdf = gdf[gdf["statnaam"].isin(PROVINCES)]

    # Multiple yearly editions exist per province; keep the most recent one.
    gdf = gdf.sort_values("jaarcode").groupby("statnaam", as_index=False).tail(1)
    gdf = gdf.reset_index(drop=True)

    if set(gdf["statnaam"]) != set(PROVINCES):
        missing = set(PROVINCES) - set(gdf["statnaam"])
        raise ValueError(f"PDOK response missing expected provinces: {missing}")

    return gdf[["statnaam", "jaarcode", "geometry"]]


def get_centroid(province_name: str) -> tuple[float, float]:
    """Return (lat, lon) for the centroid of the given province.

    province_name must be one of PROVINCES ("Groningen", "Zeeland").
    """
    if province_name not in PROVINCES:
        raise ValueError(f"Unknown province {province_name!r}, expected one of {PROVINCES}")

    gdf = fetch_provincie_boundaries()
    row = gdf[gdf["statnaam"] == province_name]
    if row.empty:
        raise ValueError(f"No boundary found for {province_name!r} in cached data")

    # Centroid on an equal-area-ish projected CRS (EPSG:28992, RD New) for
    # accuracy, then reprojected back to WGS84 for lat/lon output.
    centroid = row.to_crs("EPSG:28992").geometry.centroid.to_crs("EPSG:4326").iloc[0]
    return (centroid.y, centroid.x)
