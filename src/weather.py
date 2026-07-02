"""Open-Meteo forecast client.

GET https://api.open-meteo.com/v1/forecast
No API key required for non-commercial use.
"""

from __future__ import annotations

from typing import Protocol

import pandas as pd
import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

HOURLY_VARIABLES = [
    "wind_speed_10m",
    "wind_gusts_10m",
    "snowfall",
    "precipitation",
    "temperature_2m",
    "visibility",
]

REQUEST_TIMEOUT = 30


class ForecastClient(Protocol):
    """Minimal interface fetch_forecast depends on, so it's mockable in tests."""

    def get(self, url: str, params: dict, timeout: int) -> requests.Response: ...


def fetch_forecast(
    lat: float,
    lon: float,
    forecast_days: int = 7,
    client: ForecastClient = requests,
) -> pd.DataFrame:
    """Fetch an hourly forecast for (lat, lon) and return a tidy DataFrame.

    The DataFrame is indexed by timestamp (UTC) with one column per variable
    in HOURLY_VARIABLES.
    """
    response = client.get(
        FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(HOURLY_VARIABLES),
            "forecast_days": forecast_days,
            "timezone": "UTC",
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()

    hourly = payload["hourly"]
    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.set_index("time").sort_index()

    return df[HOURLY_VARIABLES]
