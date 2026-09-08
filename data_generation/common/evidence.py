"""Append-only provenance log. Every step that pulls a fact from an external source
or derives one via web research logs a row here; 08_evidence.py consolidates the log
into the Evidence sheet."""

import json
from datetime import datetime, timezone
from pathlib import Path

EVIDENCE_LOG_PATH = Path(__file__).resolve().parents[2] / "data" / "evidence_log.jsonl"


def log_evidence(agent: str, place_id: str, variable: str, evidence_text: str, source: str, source_url: str) -> None:
    EVIDENCE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "agent": agent,
        "place_id": place_id,
        "variable": variable,
        "evidence_text": evidence_text,
        "source": source,
        "source_url": source_url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(EVIDENCE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def read_all() -> list[dict]:
    if not EVIDENCE_LOG_PATH.exists():
        return []
    with open(EVIDENCE_LOG_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
