from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from utils.ui_embeds import themed_embed


class InfractionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    infraction = app_commands.Group(name="infraction", description="Simple infraction commands")

    @infraction.command(name="issue")
    async def issue(self, interaction: discord.Interaction, user: discord.Member):
        self.bot.db._exec(
            "INSERT INTO infractions (guild_id, user_id, actor_id, reason, created_at) VALUES (?, ?, ?, ?, ?)",
            (interaction.guild_id, user.id, interaction.user.id, "Configured default reason", datetime.now(timezone.utc).isoformat()),
        )
        cid = self.bot.db._exec("SELECT last_insert_rowid()").fetchone()[0]
        await interaction.response.send_message(embed=themed_embed("Infraction Issued", f"case_id={cid}"))

    @infraction.command(name="view")
    async def view(self, interaction: discord.Interaction, case_id: int):
        row = self.bot.db._exec("SELECT * FROM infractions WHERE id=? AND guild_id=?", (case_id, interaction.guild_id)).fetchone()
        if not row:
            await interaction.response.send_message(embed=themed_embed("Infraction View", "Case not found.", success=False), ephemeral=True)
            return
        await interaction.response.send_message(embed=themed_embed("Infraction Case", f"Case #{row['id']}\nUser={row['user_id']}\nReason={row['reason']}\nAt={row['created_at']}"))

    @infraction.command(name="history")
    async def history(self, interaction: discord.Interaction, user: discord.Member):
        rows = self.bot.db._exec("SELECT id, reason, created_at FROM infractions WHERE guild_id=? AND user_id=? ORDER BY id DESC LIMIT 10", (interaction.guild_id, user.id)).fetchall()
        await interaction.response.send_message(embed=themed_embed("Infraction History", "\n".join([f"#{r['id']} {r['reason']}" for r in rows]) or "No infractions"))


async def setup(bot):
    await bot.add_cog(InfractionCog(bot))
