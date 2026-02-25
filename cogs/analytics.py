from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core.embeds import send_embed


class AnalyticsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    analytics = app_commands.Group(name="analytics", description="Analytics commands")

    @analytics.command(name="global", description="Global command usage analytics")
    async def global_(self, interaction: discord.Interaction):
        if interaction.user.id not in self.bot.config.get("owner_ids", []):
            await send_embed(interaction, self.bot, "Owner Only", "This command is owner-only.", ephemeral=True)
            return
        data = self.bot.analytics_store.read()["commands"]
        top = sorted(data.items(), key=lambda kv: kv[1], reverse=True)[:20]
        out = "\n".join([f"{k}: {v}" for k, v in top]) or "No analytics yet."
        await send_embed(interaction, self.bot, "Global Analytics", out[:1900])

    @analytics.command(name="guild", description="Per-server analytics summary")
    async def guild(self, interaction: discord.Interaction):
        sessions = self.bot.session_store.read().get(str(interaction.guild_id), {})
        warns = self.bot.warn_store.read().get(str(interaction.guild_id), {})
        await send_embed(interaction, self.bot, "Guild Analytics", f"Sessions tracked: {len(sessions)}\nWarned users: {len(warns)}")

    @analytics.command(name="premium", description="Premium analytics for this server")
    async def premium(self, interaction: discord.Interaction):
        p = self.bot.premium.get(interaction.guild_id)
        await send_embed(interaction, self.bot, "Premium Analytics", f"Tier={p.get('tier')}\nActive={self.bot.premium.is_active(interaction.guild_id)}\nExpires={p.get('expires_at')}")

    @analytics.command(name="health", description="Simple bot health metrics")
    async def health(self, interaction: discord.Interaction):
        await send_embed(interaction, self.bot, "Bot Health", f"Latency={round(self.bot.latency*1000)}ms\nGuilds={len(self.bot.guilds)}\nUsers={sum(g.member_count or 0 for g in self.bot.guilds)}")

    @analytics.command(name="topcommands", description="Top used commands")
    async def topcommands(self, interaction: discord.Interaction):
        data = self.bot.analytics_store.read()["commands"]
        top = sorted(data.items(), key=lambda kv: kv[1], reverse=True)[:10]
        out = "\n".join([f"{k}: {v}" for k, v in top]) or "No command usage yet."
        await send_embed(interaction, self.bot, "Top Commands", out[:1900])

    @analytics.command(name="command", description="Show usage for one command key")
    async def command(self, interaction: discord.Interaction, key: str):
        data = self.bot.analytics_store.read()["commands"]
        await send_embed(interaction, self.bot, "Command Usage", f"{key}: {data.get(key, 0)} uses")


async def setup(bot):
    await bot.add_cog(AnalyticsCog(bot))
