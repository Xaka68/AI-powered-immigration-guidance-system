"""Track A (Harsh) — Journey loader (A1).

Directory-scans data/journeys/*.json at startup, validates each against
schema.json, and returns a registry {journey_id: journey_dict}.

The directory scan IS the zero-config generalizability mechanism: dropping a new
valid JSON file in and restarting makes a new journey appear — no code, no
config change. Keep it dynamic.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import jsonschema

from core.config import settings


@lru_cache(maxsize=1)
def _validator() -> jsonschema.Draft202012Validator:
    schema = json.loads((settings.journeys_dir / "schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def load_journeys(journeys_dir: Path | None = None) -> dict[str, dict]:
    """Scan, validate, and index every journey file.

    Ignores ``schema.json`` and any file whose name starts with ``_``
    (e.g. ``_example.json``). Raises on the first invalid file so authoring
    mistakes fail loudly at startup rather than at runtime.
    """
    directory = journeys_dir or settings.journeys_dir
    validator = _validator()
    registry: dict[str, dict] = {}

    for path in sorted(directory.glob("*.json")):
        if path.name == "schema.json" or path.name.startswith("_"):
            continue
        journey = json.loads(path.read_text())
        errors = sorted(validator.iter_errors(journey), key=lambda e: e.path)
        if errors:
            loc = "/".join(str(p) for p in errors[0].path) or "<root>"
            raise ValueError(f"{path.name} invalid at {loc}: {errors[0].message}")
        jid = journey["id"]
        if jid in registry:
            raise ValueError(f"Duplicate journey id '{jid}' in {path.name}")
        registry[jid] = journey

    return registry
