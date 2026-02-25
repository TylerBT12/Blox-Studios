from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands


class StaffCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    staff = app_commands.Group(name="staff", description="Simple staff commands")

    @staff.command(name="promote")
    async def promote(self, interaction: discord.Interaction, user: discord.Member):
        self.bot.db._exec(
            "INSERT INTO staff_events (guild_id, user_id, actor_id, event_type, details_json, created_at) VALUES (?, ?, ?, 'promotion', ?, ?)",
            (interaction.guild_id, user.id, interaction.user.id, "{}", datetime.now(timezone.utc).isoformat()),
        )
        await interaction.response.send_message(f"Promoted {user.mention}.")

    @staff.command(name="demote")
    async def demote(self, interaction: discord.Interaction, user: discord.Member):
        self.bot.db._exec(
            "INSERT INTO staff_events (guild_id, user_id, actor_id, event_type, details_json, created_at) VALUES (?, ?, ?, 'demotion', ?, ?)",
            (interaction.guild_id, user.id, interaction.user.id, "{}", datetime.now(timezone.utc).isoformat()),
        )
        await interaction.response.send_message(f"Demoted {user.mention}.")

    @staff.command(name="history")
    async def history(self, interaction: discord.Interaction, user: discord.Member):
        rows = self.bot.db._exec(
            "SELECT event_type, created_at FROM staff_events WHERE guild_id=? AND user_id=? ORDER BY id DESC LIMIT 10",
            (interaction.guild_id, user.id),
        ).fetchall()
        if not rows:
            await interaction.response.send_message("No history.")
            return
        await interaction.response.send_message("\n".join(f"{r['event_type']} @ {r['created_at']}" for r in rows))


async def setup(bot):
    await bot.add_cog(StaffCog(bot))
