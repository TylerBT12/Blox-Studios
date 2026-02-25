from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ActionDef:
    key: str
    display: str
    risky: bool
    param_names: list[str]


ACTIONS: dict[str, ActionDef] = {
    "announce": ActionDef("announce", "Announce / Message", False, ["message"]),
    "kick": ActionDef("kick", "Kick Player", True, ["player_name", "reason"]),
    "ban": ActionDef("ban", "Ban Player", True, ["player_name", "reason"]),
    "unban": ActionDef("unban", "Unban Player", True, ["player_name"]),
    "whitelist_add": ActionDef("whitelist_add", "Whitelist Add", True, ["player_name"]),
    "whitelist_remove": ActionDef("whitelist_remove", "Whitelist Remove", True, ["player_name"]),
    "server_lock": ActionDef("server_lock", "Server Lock", True, []),
    "server_unlock": ActionDef("server_unlock", "Server Unlock", True, []),
    "server_status": ActionDef("server_status", "Set Server Status", False, ["status_text"]),
}


def allowed_actions_for_guild(cfg: dict) -> list[ActionDef]:
    enabled = cfg.get("allowed_actions", list(ACTIONS.keys()))
    return [ACTIONS[a] for a in enabled if a in ACTIONS]
