from __future__ import annotations

import discord
from discord.ext import commands, tasks


class PresenceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.presence_loop.start()

    def cog_unload(self):
        self.presence_loop.cancel()

    @tasks.loop(minutes=5)
    async def presence_loop(self):
        await self._update_presence()

    @presence_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    async def _update_presence(self):
        guild_count = len(self.bot.guilds)
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"server count: {guild_count}")
        await self.bot.change_presence(status=discord.Status.online, activity=activity)

    @commands.Cog.listener()
    async def on_guild_join(self, _guild: discord.Guild):
        await self._update_presence()

    @commands.Cog.listener()
    async def on_guild_remove(self, _guild: discord.Guild):
        await self._update_presence()


async def setup(bot):
    await bot.add_cog(PresenceCog(bot))
