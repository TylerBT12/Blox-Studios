from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path("config.json")
DEFAULT_CONFIG: dict[str, Any] = {
    "token": "PUT_TOKEN_HERE",
    "prefix": ".",
    "owner_ids": [],
    "default_embed_color": 3447003,
    "dashboard_refresh_seconds": 120,
    "branding": {
        "author_name": "Blox Studios",
        "footer_text": "Blox Studios Bot",
        "thumbnail_url": "",
        "banner_url": "",
    },
}


def ensure_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        return DEFAULT_CONFIG.copy()

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False
    for key, value in DEFAULT_CONFIG.items():
        if key not in data:
            data[key] = value
            changed = True

    if changed:
        CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return data


def save_config(data: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
