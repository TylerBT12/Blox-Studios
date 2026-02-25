from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.storage import JsonStore

PREMIUM_PLAN = "Premium"


class PremiumManager:
    def __init__(self):
        self.store = JsonStore("data/premium.json", {"guilds": {}, "licenses": {}, "controllers": {}})

    def get(self, guild_id: int) -> dict[str, Any]:
        data = self.store.read()
        return data["guilds"].get(str(guild_id), {"active": False, "tier": None, "expires_at": None})

    def list_guilds(self) -> dict[str, Any]:
        return self.store.read()["guilds"]

    def set_premium(self, guild_id: int, tier: str | None, expires_at: str | None, by: int | None = None) -> None:
        chosen = tier or PREMIUM_PLAN

        def updater(data):
            data["guilds"][str(guild_id)] = {
                "active": True,
                "tier": chosen,
                "expires_at": expires_at,
                "updated_by": by,
            }
            return data

        self.store.update(updater)

    def remove_premium(self, guild_id: int) -> None:
        def updater(data):
            data["guilds"][str(guild_id)] = {"active": False, "tier": None, "expires_at": None}
            return data

        self.store.update(updater)

    def is_active(self, guild_id: int) -> bool:
        p = self.get(guild_id)
        if not p.get("active"):
            return False
        expires_at = p.get("expires_at")
        if expires_at is None:
            return True
        return datetime.fromisoformat(expires_at) > datetime.now(timezone.utc)

    def expire_due(self) -> list[int]:
        data = self.store.read()
        now = datetime.now(timezone.utc)
        expired: list[int] = []
        for gid, info in data["guilds"].items():
            if info.get("active") and info.get("expires_at"):
                if datetime.fromisoformat(info["expires_at"]) <= now:
                    info["active"] = False
                    expired.append(int(gid))
        if expired:
            self.store.write(data)
        return expired

    def create_license(self, key: str, duration: str, uses: int = 1) -> None:
        def updater(data):
            data["licenses"][key] = {
                "tier": PREMIUM_PLAN,
                "duration": duration,
                "uses": uses,
                "redeemed": 0,
            }
            return data

        self.store.update(updater)

    def redeem(self, key: str, guild_id: int) -> dict[str, Any] | None:
        data = self.store.read()
        lic = data["licenses"].get(key)
        if not lic:
            return None
        if lic["redeemed"] >= lic["uses"]:
            return None
        lic["redeemed"] += 1
        data["licenses"][key] = lic
        self.store.write(data)
        return lic

    def list_controllers(self, guild_id: int) -> list[int]:
        data = self.store.read()
        return data.get("controllers", {}).get(str(guild_id), [])

    def add_controller(self, guild_id: int, user_id: int) -> list[int]:
        def updater(data):
            controllers = data.setdefault("controllers", {})
            arr = set(controllers.get(str(guild_id), []))
            arr.add(user_id)
            controllers[str(guild_id)] = sorted(arr)
            data["controllers"] = controllers
            return data

        new_data = self.store.update(updater)
        return new_data.get("controllers", {}).get(str(guild_id), [])

    def remove_controller(self, guild_id: int, user_id: int) -> list[int]:
        def updater(data):
            controllers = data.setdefault("controllers", {})
            arr = set(controllers.get(str(guild_id), []))
            arr.discard(user_id)
            controllers[str(guild_id)] = sorted(arr)
            data["controllers"] = controllers
            return data

        new_data = self.store.update(updater)
        return new_data.get("controllers", {}).get(str(guild_id), [])

    def can_control(self, guild_id: int, user_id: int, owner_ids: list[int]) -> bool:
        if user_id in owner_ids:
            return True
        return user_id in self.list_controllers(guild_id)
