from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class AnalyticsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    analytics = app_commands.Group(name="analytics", description="Analytics commands")

    @analytics.command(name="global", description="Global command usage analytics")
    async def global_(self, interaction: discord.Interaction):
        if interaction.user.id not in self.bot.config.get("owner_ids", []):
            await interaction.response.send_message("Owner only.", ephemeral=True)
            return
        data = self.bot.analytics_store.read()["commands"]
        top = sorted(data.items(), key=lambda kv: kv[1], reverse=True)[:20]
        out = "\n".join([f"{k}: {v}" for k, v in top]) or "No analytics yet."
        await interaction.response.send_message(out[:1900])

    @analytics.command(name="guild", description="Per-server analytics summary")
    async def guild(self, interaction: discord.Interaction):
        sessions = self.bot.session_store.read().get(str(interaction.guild_id), {})
        warns = self.bot.warn_store.read().get(str(interaction.guild_id), {})
        await interaction.response.send_message(f"Sessions tracked: {len(sessions)} | Warned users: {len(warns)}")

    @analytics.command(name="premium", description="Premium analytics for this server")
    async def premium(self, interaction: discord.Interaction):
        p = self.bot.premium.get(interaction.guild_id)
        await interaction.response.send_message(f"Tier={p.get('tier')} | Active={self.bot.premium.is_active(interaction.guild_id)} | Expires={p.get('expires_at')}")

    @analytics.command(name="health", description="Simple bot health metrics")
    async def health(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Latency={round(self.bot.latency*1000)}ms | Guilds={len(self.bot.guilds)} | Users={sum(g.member_count or 0 for g in self.bot.guilds)}")


async def setup(bot):
    cog = AnalyticsCog(bot)
    await bot.add_cog(cog)
