from __future__ import annotations

from datetime import datetime, timedelta, timezone


def parse_duration(spec: str) -> datetime | None:
    spec = spec.strip().lower()
    if spec in {"unlimited", "forever", "perm", "permanent"}:
        return None

    unit = spec[-1]
    amount = int(spec[:-1])

    now = datetime.now(timezone.utc)
    if unit == "d":
        return now + timedelta(days=amount)
    if unit == "h":
        return now + timedelta(hours=amount)
    if unit == "m":
        return now + timedelta(minutes=amount)
    if unit == "y":
        return now + timedelta(days=365 * amount)
    raise ValueError("Invalid duration. Use formats like 30d, 12h, 1y, unlimited")


def format_dt(dt_iso: str | None) -> str:
    if dt_iso is None:
        return "Unlimited"
    dt = datetime.fromisoformat(dt_iso)
    return dt.strftime("%Y-%m-%d %H:%M UTC")
