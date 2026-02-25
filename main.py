from __future__ import annotations

import asyncio
import os

import discord
from discord.ext import commands

from services.erlc_client import ERLCClient
from services.maple_client import MapleClient
from utils.db import Database

COGS = [
    "cogs.config_cog",
    "cogs.session_cog",
    "cogs.staff_cog",
    "cogs.infraction_cog",
    "cogs.appeal_cog",
    "cogs.economy_cog",
    "cogs.api_cog",
    "cogs.owner_cog",
]


class AllInOneBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix=".", intents=intents)
        self.db = Database("data/bot.db")
        self.owner_ids = [int(x) for x in os.getenv("OWNER_IDS", "").split(",") if x.strip().isdigit()]
        self.erlc = ERLCClient(os.getenv("ERLC_API_KEY"))
        self.maple = MapleClient(os.getenv("MAPLE_API_KEY"))

    async def setup_hook(self):
        for ext in COGS:
            await self.load_extension(ext)
        await self.tree.sync()

    async def on_ready(self):
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(type=discord.ActivityType.watching, name=f"server count: {len(self.guilds)}"),
        )
        print(f"Logged in as {self.user} ({self.user.id})")


async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("Missing BOT_TOKEN in environment")
    bot = AllInOneBot()
    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
