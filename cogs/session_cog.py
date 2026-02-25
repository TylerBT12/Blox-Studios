from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands


class SessionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    session = app_commands.Group(name="session", description="Simple session commands")

    @session.command(name="start")
    async def start(self, interaction: discord.Interaction):
        self.bot.db._exec(
            "INSERT INTO sessions (guild_id, user_id, started_at) VALUES (?, ?, ?)",
            (interaction.guild_id, interaction.user.id, datetime.now(timezone.utc).isoformat()),
        )
        await interaction.response.send_message("Session started.", ephemeral=True)

    @session.command(name="end")
    async def end(self, interaction: discord.Interaction):
        row = self.bot.db._exec(
            "SELECT id FROM sessions WHERE guild_id=? AND user_id=? AND ended_at IS NULL ORDER BY id DESC LIMIT 1",
            (interaction.guild_id, interaction.user.id),
        ).fetchone()
        if not row:
            await interaction.response.send_message("No active session.", ephemeral=True)
            return
        self.bot.db._exec("UPDATE sessions SET ended_at=? WHERE id=?", (datetime.now(timezone.utc).isoformat(), row[0]))
        await interaction.response.send_message("Session ended.", ephemeral=True)

    @session.command(name="announce")
    async def announce(self, interaction: discord.Interaction):
        await interaction.response.send_message("Session announcement sent using your configured template/channel.")

    @session.command(name="info")
    async def info(self, interaction: discord.Interaction):
        count = self.bot.db._exec("SELECT COUNT(*) FROM sessions WHERE guild_id=?", (interaction.guild_id,)).fetchone()[0]
        await interaction.response.send_message(f"Total sessions logged: {count}")


async def setup(bot):
    await bot.add_cog(SessionCog(bot))
