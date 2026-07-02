# GeoHazard NL

A weather hazard intelligence dashboard for two fixed Dutch provinces —
Groningen (north coast) and Zeeland (southwest coast) — built as a public,
portfolio-scale rebuild of a shapefile → forecast → hazard-detection →
LLM-narrative pipeline.

Public data only: [PDOK](https://www.pdok.nl/) CBS province boundaries,
[Open-Meteo](https://open-meteo.com/) forecasts, and the Claude API for
narrative generation. Pure Python + Streamlit — no Kubernetes, no cloud
infra required.

## Pipeline

Shapefile centroid → Open-Meteo hourly forecast → hazard detection →
six forecast time windows → Claude API narrative → Streamlit dashboard
(map + two reports + PDF export).

See `CLAUDE.md` for the full architecture brief.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
streamlit run app.py
```

## Project structure

```
geohazard-nl/
├── data/           # cached province shapefile/geopackage
├── src/
│   ├── geo.py          # shapefile loading + centroid extraction
│   ├── weather.py       # Open-Meteo client
│   ├── hazards.py       # threshold detection + time window aggregation
│   ├── narrative.py     # Claude API prompt + call
│   └── pdf.py            # PDF report builder
├── app.py           # Streamlit entrypoint
└── requirements.txt
```
