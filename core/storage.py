from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any


class JsonStore:
    def __init__(self, path: str | Path, default: dict[str, Any] | list[Any]):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.default = default
        self.lock = Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.path.exists():
            self.path.write_text(json.dumps(self.default, indent=2), encoding="utf-8")

    def read(self) -> Any:
        with self.lock:
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)

    def write(self, data: Any) -> None:
        with self.lock:
            self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def update(self, updater):
        with self.lock:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            new_data = updater(data)
            self.path.write_text(json.dumps(new_data, indent=2), encoding="utf-8")
            return new_data
