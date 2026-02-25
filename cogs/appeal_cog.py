from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands


class AppealModal(discord.ui.Modal, title="Submit Appeal"):
    reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.paragraph)
    evidence = discord.ui.TextInput(label="Evidence", style=discord.TextStyle.paragraph, required=False)

    def __init__(self, bot, guild_id: int, user_id: int):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        self.bot.db._exec(
            "INSERT INTO appeals (guild_id, user_id, status, reason, evidence, created_at) VALUES (?, ?, 'pending', ?, ?, ?)",
            (self.guild_id, self.user_id, str(self.reason), str(self.evidence), datetime.now(timezone.utc).isoformat()),
        )
        aid = self.bot.db._exec("SELECT last_insert_rowid()").fetchone()[0]
        await interaction.response.send_message(f"Appeal submitted. appeal_id={aid}", ephemeral=True)


class AppealCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    appeal = app_commands.Group(name="appeal", description="Appeal commands")

    @appeal.command(name="submit")
    async def submit(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AppealModal(self.bot, interaction.guild_id, interaction.user.id))

    @appeal.command(name="view")
    async def view(self, interaction: discord.Interaction, appeal_id: int):
        row = self.bot.db._exec("SELECT * FROM appeals WHERE id=? AND guild_id=?", (appeal_id, interaction.guild_id)).fetchone()
        if not row:
            await interaction.response.send_message("Appeal not found.", ephemeral=True)
            return
        await interaction.response.send_message(f"Appeal #{row['id']} status={row['status']} reason={row['reason']}")

    @appeal.command(name="list")
    async def list_(self, interaction: discord.Interaction):
        rows = self.bot.db._exec("SELECT id, user_id, status FROM appeals WHERE guild_id=? ORDER BY id DESC LIMIT 20", (interaction.guild_id,)).fetchall()
        await interaction.response.send_message("\n".join([f"#{r['id']} user={r['user_id']} status={r['status']}" for r in rows]) or "No appeals")


async def setup(bot):
    await bot.add_cog(AppealCog(bot))
