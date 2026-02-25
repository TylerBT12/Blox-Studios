from __future__ import annotations

from datetime import datetime, timedelta, timezone


def parse_duration(spec: str) -> datetime:
    spec = spec.strip().lower()
    if len(spec) < 2:
        raise ValueError("Invalid duration")
    unit = spec[-1]
    value = int(spec[:-1])
    now = datetime.now(timezone.utc)
    if unit == "d":
        return now + timedelta(days=value)
    if unit == "h":
        return now + timedelta(hours=value)
    if unit == "m":
        return now + timedelta(minutes=value)
    raise ValueError("Use 30d / 12h / 15m")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
