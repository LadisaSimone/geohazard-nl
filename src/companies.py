"""Company registry — each company pinned to a fixed location.

Replaces the two-hardcoded-province model with a list of operating sites.
Every company currently points at the same THRESHOLDS dict from
src.hazards; a future per-company override is just pointing a company's
`thresholds` field at a different dict, not a schema change.
"""

from __future__ import annotations

from .hazards import THRESHOLDS

COMPANIES = [
    {
        "name": "Noordkust Logistics",
        "lat": 53.4396,
        "lon": 6.8375,
        "description": "Eemshaven port, north coast — wind exposure",
        "thresholds": THRESHOLDS,
    },
    {
        "name": "Delta Maritime Services",
        "lat": 51.4426,
        "lon": 3.5736,
        "description": "Vlissingen port, southwest coast — storm surge exposure",
        "thresholds": THRESHOLDS,
    },
    {
        "name": "Maasvlakte Freight Terminal",
        "lat": 51.9667,
        "lon": 4.0333,
        "description": "Rotterdam port — major shipping hub",
        "thresholds": THRESHOLDS,
    },
    {
        "name": "Schiphol Air Cargo Hub",
        "lat": 52.3105,
        "lon": 4.7683,
        "description": "Amsterdam/Schiphol — aviation, visibility-sensitive",
        "thresholds": THRESHOLDS,
    },
    {
        "name": "Zuid-Limburg Distribution",
        "lat": 50.8514,
        "lon": 5.6910,
        "description": "Maastricht — inland, hilly southeast",
        "thresholds": THRESHOLDS,
    },
    {
        "name": "Twente Agri Cooperative",
        "lat": 52.2215,
        "lon": 6.8937,
        "description": "Enschede — inland east, agriculture",
        "thresholds": THRESHOLDS,
    },
]
