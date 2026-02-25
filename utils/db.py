from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: str = "data/bot.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _exec(self, q: str, args: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(q, args)
        self.conn.commit()
        return cur

    def _init_schema(self):
        self._exec("""
        CREATE TABLE IF NOT EXISTS guild_config (
          guild_id INTEGER PRIMARY KEY,
          channels_json TEXT NOT NULL DEFAULT '{}',
          module_enabled_json TEXT NOT NULL DEFAULT '{}',
          admins_bypass INTEGER NOT NULL DEFAULT 1,
          provider_mode TEXT NOT NULL DEFAULT 'both',
          api_actions_enabled INTEGER NOT NULL DEFAULT 1,
          require_action_confirmation INTEGER NOT NULL DEFAULT 1,
          log_all_actions INTEGER NOT NULL DEFAULT 1,
          webhook_settings_json TEXT NOT NULL DEFAULT '{}',
          economy_settings_json TEXT NOT NULL DEFAULT '{}'
        )
        """)
        self._exec("CREATE TABLE IF NOT EXISTS guild_variables (guild_id INTEGER, key TEXT, value TEXT, PRIMARY KEY (guild_id, key))")
        self._exec("CREATE TABLE IF NOT EXISTS guild_permissions (guild_id INTEGER, group_name TEXT, role_id INTEGER, PRIMARY KEY (guild_id, group_name, role_id))")
        self._exec("CREATE TABLE IF NOT EXISTS embed_templates (guild_id INTEGER, name TEXT, json_payload TEXT, PRIMARY KEY (guild_id, name))")
        self._exec("CREATE TABLE IF NOT EXISTS premium (guild_id INTEGER PRIMARY KEY, expires_at TEXT)")
        self._exec("CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, started_at TEXT, ended_at TEXT)")
        self._exec("CREATE TABLE IF NOT EXISTS staff_events (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, actor_id INTEGER, event_type TEXT, details_json TEXT, created_at TEXT)")
        self._exec("CREATE TABLE IF NOT EXISTS infractions (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, actor_id INTEGER, reason TEXT, created_at TEXT)")
        self._exec("CREATE TABLE IF NOT EXISTS appeals (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, status TEXT, reason TEXT, evidence TEXT, created_at TEXT)")
        self._exec("""
        CREATE TABLE IF NOT EXISTS economy_users (
          guild_id INTEGER, user_id INTEGER, balance INTEGER NOT NULL DEFAULT 0,
          daily_at TEXT, work_at TEXT, PRIMARY KEY (guild_id, user_id)
        )
        """)
        self._exec("CREATE TABLE IF NOT EXISTS economy_shop_items (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, name TEXT, price INTEGER, description TEXT, image_url TEXT, role_reward_id INTEGER, consumable INTEGER DEFAULT 0, category TEXT DEFAULT 'General', sale_percent INTEGER DEFAULT 0)")
        self._exec("CREATE TABLE IF NOT EXISTS economy_inventory (guild_id INTEGER, user_id INTEGER, item_id INTEGER, qty INTEGER, PRIMARY KEY (guild_id, user_id, item_id))")
        self._exec("CREATE TABLE IF NOT EXISTS api_action_audit (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, actor_id INTEGER, provider TEXT, action_key TEXT, target TEXT, result_json TEXT, created_at TEXT)")

    # ----- config -----
    def ensure_guild(self, guild_id: int):
        self._exec("INSERT OR IGNORE INTO guild_config (guild_id) VALUES (?)", (guild_id,))

    def get_guild_config(self, guild_id: int) -> dict:
        self.ensure_guild(guild_id)
        row = self._exec("SELECT * FROM guild_config WHERE guild_id=?", (guild_id,)).fetchone()
        return {
            "channels": json.loads(row["channels_json"]),
            "module_enabled": {**{"sessions": True, "staff": True, "infractions": True, "appeals": True, "api": True, "economy": True}, **json.loads(row["module_enabled_json"] or "{}")},
            "admins_bypass": bool(row["admins_bypass"]),
            "provider_mode": row["provider_mode"],
            "api_actions_enabled": bool(row["api_actions_enabled"]),
            "require_action_confirmation": bool(row["require_action_confirmation"]),
            "log_all_actions": bool(row["log_all_actions"]),
            **json.loads(row["webhook_settings_json"] or "{}"),
            "economy_settings": {**{"currency_name": "Credits", "starting_balance": 1000, "daily_amount": 300, "work_min": 50, "work_max": 220, "daily_cooldown_h": 24, "work_cooldown_m": 30, "transfer_max": 50000, "transfer_tax_percent": 0}, **json.loads(row["economy_settings_json"] or "{}")},
        }

    def update_guild_config(self, guild_id: int, key: str, value):
        cfg = self.get_guild_config(guild_id)
        if key == "channels":
            self._exec("UPDATE guild_config SET channels_json=? WHERE guild_id=?", (json.dumps(value), guild_id))
        elif key == "module_enabled":
            self._exec("UPDATE guild_config SET module_enabled_json=? WHERE guild_id=?", (json.dumps(value), guild_id))
        elif key == "admins_bypass":
            self._exec("UPDATE guild_config SET admins_bypass=? WHERE guild_id=?", (1 if value else 0, guild_id))
        elif key == "provider_mode":
            self._exec("UPDATE guild_config SET provider_mode=? WHERE guild_id=?", (value, guild_id))
        elif key == "api_actions_enabled":
            self._exec("UPDATE guild_config SET api_actions_enabled=? WHERE guild_id=?", (1 if value else 0, guild_id))
        elif key == "require_action_confirmation":
            self._exec("UPDATE guild_config SET require_action_confirmation=? WHERE guild_id=?", (1 if value else 0, guild_id))
        elif key == "log_all_actions":
            self._exec("UPDATE guild_config SET log_all_actions=? WHERE guild_id=?", (1 if value else 0, guild_id))
        elif key == "economy_settings":
            self._exec("UPDATE guild_config SET economy_settings_json=? WHERE guild_id=?", (json.dumps(value), guild_id))
        else:
            # webhook settings bucket
            cfg[key] = value
            webhook_data = {
                "webhook_modules": cfg.get("webhook_modules", {}),
                "webhook_name": cfg.get("webhook_name"),
                "webhook_avatar_url": cfg.get("webhook_avatar_url"),
                "webhook_overrides": cfg.get("webhook_overrides", {}),
                "allowed_actions": cfg.get("allowed_actions", []),
            }
            self._exec("UPDATE guild_config SET webhook_settings_json=? WHERE guild_id=?", (json.dumps(webhook_data), guild_id))

    def get_permission_roles(self, guild_id: int, group_name: str) -> list[int]:
        rows = self._exec("SELECT role_id FROM guild_permissions WHERE guild_id=? AND group_name=?", (guild_id, group_name)).fetchall()
        return [r[0] for r in rows]

    def set_permission_roles(self, guild_id: int, group_name: str, role_ids: list[int]):
        self._exec("DELETE FROM guild_permissions WHERE guild_id=? AND group_name=?", (guild_id, group_name))
        for rid in role_ids:
            self._exec("INSERT OR IGNORE INTO guild_permissions (guild_id, group_name, role_id) VALUES (?, ?, ?)", (guild_id, group_name, rid))

    def set_variable(self, guild_id: int, key: str, value: str):
        self._exec("INSERT OR REPLACE INTO guild_variables (guild_id, key, value) VALUES (?, ?, ?)", (guild_id, key, value))

    def get_variables(self, guild_id: int) -> dict[str, str]:
        rows = self._exec("SELECT key, value FROM guild_variables WHERE guild_id=?", (guild_id,)).fetchall()
        return {r[0]: r[1] for r in rows}

    def set_template(self, guild_id: int, name: str, payload_json: str):
        self._exec("INSERT OR REPLACE INTO embed_templates (guild_id, name, json_payload) VALUES (?, ?, ?)", (guild_id, name, payload_json))

    def get_template(self, guild_id: int, name: str) -> str | None:
        row = self._exec("SELECT json_payload FROM embed_templates WHERE guild_id=? AND name=?", (guild_id, name)).fetchone()
        return row[0] if row else None

    # ----- premium -----
    def set_premium(self, guild_id: int, expires_at: str):
        self._exec("INSERT OR REPLACE INTO premium (guild_id, expires_at) VALUES (?, ?)", (guild_id, expires_at))

    def revoke_premium(self, guild_id: int):
        self._exec("DELETE FROM premium WHERE guild_id=?", (guild_id,))

    def get_premium(self, guild_id: int) -> str | None:
        row = self._exec("SELECT expires_at FROM premium WHERE guild_id=?", (guild_id,)).fetchone()
        return row[0] if row else None

    # ----- economy -----
    def ensure_economy_user(self, guild_id: int, user_id: int):
        cfg = self.get_guild_config(guild_id)["economy_settings"]
        self._exec("INSERT OR IGNORE INTO economy_users (guild_id, user_id, balance) VALUES (?, ?, ?)", (guild_id, user_id, cfg["starting_balance"]))

    def get_balance(self, guild_id: int, user_id: int) -> int:
        self.ensure_economy_user(guild_id, user_id)
        row = self._exec("SELECT balance FROM economy_users WHERE guild_id=? AND user_id=?", (guild_id, user_id)).fetchone()
        return int(row[0])

    def change_balance(self, guild_id: int, user_id: int, delta: int):
        self.ensure_economy_user(guild_id, user_id)
        self._exec("UPDATE economy_users SET balance = balance + ? WHERE guild_id=? AND user_id=?", (delta, guild_id, user_id))

    def set_cooldown(self, guild_id: int, user_id: int, field: str, iso: str):
        assert field in {"daily_at", "work_at"}
        self.ensure_economy_user(guild_id, user_id)
        self._exec(f"UPDATE economy_users SET {field}=? WHERE guild_id=? AND user_id=?", (iso, guild_id, user_id))

    def get_cooldowns(self, guild_id: int, user_id: int) -> dict:
        self.ensure_economy_user(guild_id, user_id)
        row = self._exec("SELECT daily_at, work_at FROM economy_users WHERE guild_id=? AND user_id=?", (guild_id, user_id)).fetchone()
        return {"daily_at": row[0], "work_at": row[1]}

    def top_balances(self, guild_id: int, limit: int = 10):
        return self._exec("SELECT user_id, balance FROM economy_users WHERE guild_id=? ORDER BY balance DESC LIMIT ?", (guild_id, limit)).fetchall()

    def add_shop_item(self, guild_id: int, name: str, price: int, description: str, image_url: str | None = None, category: str = "General"):
        self._exec("INSERT INTO economy_shop_items (guild_id, name, price, description, image_url, category) VALUES (?, ?, ?, ?, ?, ?)", (guild_id, name, price, description, image_url, category))

    def list_shop_items(self, guild_id: int):
        return self._exec("SELECT * FROM economy_shop_items WHERE guild_id=? ORDER BY id DESC", (guild_id,)).fetchall()

    def add_inventory(self, guild_id: int, user_id: int, item_id: int, qty: int = 1):
        row = self._exec("SELECT qty FROM economy_inventory WHERE guild_id=? AND user_id=? AND item_id=?", (guild_id, user_id, item_id)).fetchone()
        if row:
            self._exec("UPDATE economy_inventory SET qty = qty + ? WHERE guild_id=? AND user_id=? AND item_id=?", (qty, guild_id, user_id, item_id))
        else:
            self._exec("INSERT INTO economy_inventory (guild_id, user_id, item_id, qty) VALUES (?, ?, ?, ?)", (guild_id, user_id, item_id, qty))

    def list_inventory(self, guild_id: int, user_id: int):
        return self._exec("SELECT i.item_id, i.qty, s.name FROM economy_inventory i LEFT JOIN economy_shop_items s ON s.id=i.item_id WHERE i.guild_id=? AND i.user_id=?", (guild_id, user_id)).fetchall()

    # ----- audit -----
    def log_api_action(self, guild_id: int, actor_id: int, provider: str, action_key: str, target: str, result_json: str, created_at: str):
        self._exec("INSERT INTO api_action_audit (guild_id, actor_id, provider, action_key, target, result_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (guild_id, actor_id, provider, action_key, target, result_json, created_at))
