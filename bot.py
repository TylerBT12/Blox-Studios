from __future__ import annotations

import asyncio
from pathlib import Path

import discord
from discord.ext import commands

from core.config import ensure_config
from core.premium import PremiumManager
from core.storage import JsonStore

COGS = [
    "cogs.owner_panel",
    "cogs.premium",
    "cogs.dashboard",
    "cogs.moderation",
    "cogs.appeals",
    "cogs.sessions",
    "cogs.staff",
    "cogs.config",
    "cogs.analytics",
    "cogs.command_menu",
]


class BloxBot(commands.Bot):
    def __init__(self):
        self.config = ensure_config()
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix=self.config.get("prefix", "."), intents=intents)

        self.premium = PremiumManager()
        self.guild_store = JsonStore("data/guilds.json", {})
        self.warn_store = JsonStore("data/warnings.json", {})
        self.case_store = JsonStore("data/cases.json", {"next": 1, "items": {}})
        self.session_store = JsonStore("data/sessions.json", {})
        self.appeal_store = JsonStore("data/appeals.json", {"next": 1, "items": {}})
        self.analytics_store = JsonStore("data/analytics.json", {"commands": {}, "events": {}})

    async def setup_hook(self):
        for cog in COGS:
            await self.load_extension(cog)
        await self.tree.sync()

    async def on_command_completion(self, ctx: commands.Context):
        def updater(data):
            key = f"prefix:{ctx.command.qualified_name}"
            data["commands"][key] = data["commands"].get(key, 0) + 1
            return data

        self.analytics_store.update(updater)

    async def on_app_command_completion(self, interaction: discord.Interaction, command: discord.app_commands.Command):
        def updater(data):
            key = f"slash:{command.qualified_name}"
            data["commands"][key] = data["commands"].get(key, 0) + 1
            return data

        self.analytics_store.update(updater)


async def main() -> None:
    Path("data").mkdir(parents=True, exist_ok=True)
    bot = BloxBot()
    token = bot.config.get("token")
    if not token or token == "PUT_TOKEN_HERE":
        raise SystemExit("Set your Discord bot token in config.json (field: token) and restart.")
    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
