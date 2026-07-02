"""Claude API narrative generation for company hazard reports.

One call per company. The model receives the structured hazard table as
facts only — it phrases what's already been computed, never invents
hazard data. Narratives are cached on disk (data/narrative_cache.json)
keyed on a hash of the company name + hazard table, so identical hazard
data doesn't trigger a new API call.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "You are a professional meteorological report writer producing short "
    "hazard briefings for a company operating at a fixed site in the "
    "Netherlands. Write in concise, factual, English-only prose suitable "
    "for a public dashboard. You will be given a structured table of "
    "hazards already detected by a deterministic threshold system, plus "
    "the company name and a short description of its location and "
    "operational exposure. Base your report strictly on the data provided "
    "— never invent, exaggerate, or infer hazards that aren't in the "
    "table. If the hazard table is empty, write a brief note that no "
    "significant hazards are expected in the forecast window and "
    "conditions look normal/quiet."
)

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "narrative_cache.json"


def build_prompt(name: str, description: str, hazard_table: list[dict]) -> str:
    """Build the user-turn prompt: name + description context + hazard table as JSON."""
    hazards_json = json.dumps(hazard_table, indent=2, sort_keys=True, default=str)

    return (
        f"Name: {name}\n"
        f"Geographic/operational context: {description}\n\n"
        f"Detected hazards (JSON, empty list means no thresholds were exceeded):\n"
        f"{hazards_json}\n\n"
        "Write a concise hazard report for this location's forecast period, "
        "based only on the data above.\n\n"
        "Formatting: do not include a top-level title or heading — this report "
        "is displayed under a page heading that already shows the name, so "
        "starting with another title would be redundant. Start directly with "
        "the forecast overview content. If you break the report into sections "
        "(e.g. Active hazards, Summary), use at most one level of subheading, "
        "formatted consistently as bold text (e.g. **Active hazards**), not "
        "Markdown '#' headings."
    )


def _cache_key(name: str, hazard_table: list[dict]) -> str:
    payload = json.dumps(
        {"name": name, "hazards": hazard_table}, sort_keys=True, default=str
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def generate_narrative(
    name: str,
    description: str,
    hazard_table: list[dict],
    client: anthropic.Anthropic | None = None,
) -> str:
    """Generate (or return a cached) narrative for a company's hazard table."""
    cache_key = _cache_key(name, hazard_table)
    cache = _load_cache()
    if cache_key in cache:
        return cache[cache_key]

    if client is None:
        client = anthropic.Anthropic()

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(name, description, hazard_table)}],
    )
    narrative = next(block.text for block in response.content if block.type == "text")

    cache[cache_key] = narrative
    _save_cache(cache)
    return narrative
