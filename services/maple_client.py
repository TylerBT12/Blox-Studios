from __future__ import annotations

from services.base_api import BaseGameAPI


class MapleClient(BaseGameAPI):
    provider_name = "maple"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    async def status(self) -> dict:
        return {"provider": "Maple County", "supported": False, "message": "Status stub. Add real Maple integration here."}

    async def players(self) -> list[dict]:
        return []

    async def run_action(self, action: str, params: dict) -> dict:
        return {"ok": False, "message": f"Action '{action}' not supported by Maple stub client.", "params": params}
