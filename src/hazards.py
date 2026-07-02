"""Deterministic hazard threshold detection and time-window aggregation.

Plain Python thresholds only — no LLM involved, so every hazard traces
back to a data point + threshold.
"""

from __future__ import annotations

import pandas as pd

THRESHOLDS = {
    "wind_gusts_10m": {"unit": "km/h", "warning": 75, "severe": 90},
    "precipitation": {"unit": "mm/h", "warning": 10, "severe": 20},
    "visibility": {"unit": "m", "warning": 1000, "severe": 200},  # lower = worse
    "snowfall": {"unit": "cm/h", "warning": 1, "severe": 3},
}

# label -> (start_hour, end_hour), hour offsets from "now" (not from the
# start of the forecast DataFrame — Open-Meteo returns full calendar days
# from UTC midnight, so df.index[0] can be many hours in the past by the
# time the dashboard is loaded).
TIME_WINDOWS = {
    "0-6h": (0, 6),
    "6-12h": (6, 12),
    "12-24h": (12, 24),
    "24-48h": (24, 48),
    "2-4d": (48, 96),
    "4-7d": (96, 168),
}

_MAX_VARS = ["wind_speed_10m", "wind_gusts_10m", "snowfall"]
_SUM_VARS = ["precipitation"]
_MEAN_VARS = ["temperature_2m"]
_MIN_VARS = ["visibility"]

# Variables where a lower value is worse (inverts the > threshold comparison).
_LOWER_IS_WORSE = {"visibility"}


def aggregate_windows(df: pd.DataFrame, now: pd.Timestamp | None = None) -> pd.DataFrame:
    """Aggregate an hourly forecast DataFrame into the six TIME_WINDOWS.

    Window boundaries are actual UTC timestamps computed as offsets from
    `now` (defaults to pd.Timestamp.now(tz="UTC")), not positions in df,
    so a window always reflects the stated hours-from-now regardless of
    when the forecast was fetched.

    Returns a DataFrame indexed by window label, one column per variable:
    max for wind/gusts/snowfall, sum for precipitation, mean for
    temperature, min for visibility.
    """
    if now is None:
        now = pd.Timestamp.now(tz="UTC")

    rows = {}
    for label, (start_hour, end_hour) in TIME_WINDOWS.items():
        start_ts = now + pd.Timedelta(hours=start_hour)
        end_ts = now + pd.Timedelta(hours=end_hour)
        window = df.loc[(df.index >= start_ts) & (df.index < end_ts)]
        rows[label] = {
            **{var: window[var].max() for var in _MAX_VARS},
            **{var: window[var].sum() for var in _SUM_VARS},
            **{var: window[var].mean() for var in _MEAN_VARS},
            **{var: window[var].min() for var in _MIN_VARS},
        }

    columns = _MAX_VARS + _SUM_VARS + _MEAN_VARS + _MIN_VARS
    return pd.DataFrame.from_dict(rows, orient="index")[columns]


def _severity(variable: str, value: float, thresholds: dict) -> str | None:
    variable_thresholds = thresholds[variable]
    if variable in _LOWER_IS_WORSE:
        if value < variable_thresholds["severe"]:
            return "severe"
        if value < variable_thresholds["warning"]:
            return "warning"
        return None

    if value > variable_thresholds["severe"]:
        return "severe"
    if value > variable_thresholds["warning"]:
        return "warning"
    return None


def detect_hazards(windowed_df: pd.DataFrame) -> list[dict]:
    """Compare each window's aggregated values against THRESHOLDS.

    Returns a structured hazard table: a list of
    {window, variable, value, severity} dicts, one per exceeded threshold.
    Windows/variables that don't cross a threshold produce no record.
    """
    hazards = []
    for window_label, row in windowed_df.iterrows():
        for variable in THRESHOLDS:
            value = row[variable]
            severity = _severity(variable, value, THRESHOLDS)
            if severity is not None:
                hazards.append(
                    {
                        "window": window_label,
                        "variable": variable,
                        "value": value,
                        "severity": severity,
                    }
                )
    return hazards


_SEVERITY_RANK = {"clear": 0, "warning": 1, "severe": 2}


def full_window_report(windowed_df: pd.DataFrame, thresholds: dict) -> list[dict]:
    """Report every time window, always, whether or not a hazard triggered.

    Returns a list of {window, status, hazards} dicts, one per
    TIME_WINDOWS entry (six, always). `hazards` is the list of
    {variable, value, severity} that exceeded a threshold in that window
    (empty if none did). `status` is the worst severity present in the
    window, or "clear" if none.
    """
    report = []
    for window_label, row in windowed_df.iterrows():
        window_hazards = []
        for variable in thresholds:
            value = row[variable]
            severity = _severity(variable, value, thresholds)
            if severity is not None:
                window_hazards.append(
                    {"variable": variable, "value": value, "severity": severity}
                )

        status = "clear"
        for hazard in window_hazards:
            if _SEVERITY_RANK[hazard["severity"]] > _SEVERITY_RANK[status]:
                status = hazard["severity"]

        report.append({"window": window_label, "status": status, "hazards": window_hazards})
    return report
