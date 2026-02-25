from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from core.embeds import build_embed, send_embed


class AppealReviewView(discord.ui.View):
    def __init__(self, bot, appeal_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.appeal_id = appeal_id

    async def _update(self, interaction: discord.Interaction, status: str):
        def updater(data):
            item = data["items"].get(str(self.appeal_id))
            if item:
                item["status"] = status
                item["reviewed_by"] = interaction.user.id
                item["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            return data

        self.bot.appeal_store.update(updater)
        await send_embed(interaction, self.bot, "Appeal Updated", f"Appeal #{self.appeal_id} marked **{status}**")

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._update(interaction, "accepted")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._update(interaction, "denied")


class AppealsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    appeals = app_commands.Group(name="appeals", description="Appeal system")

    @appeals.command(name="submit", description="Submit an appeal")
    async def submit(self, interaction: discord.Interaction, case_id: int, reason: str):
        def updater(data):
            aid = data["next"]
            data["next"] += 1
            data["items"][str(aid)] = {
                "guild_id": interaction.guild_id,
                "case_id": case_id,
                "user_id": interaction.user.id,
                "reason": reason,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            return data

        out = self.bot.appeal_store.update(updater)
        appeal_id = out["next"] - 1
        await send_embed(interaction, self.bot, "Appeal Submitted", f"Appeal submitted with ID **#{appeal_id}**")

    @appeals.command(name="status", description="Check appeal status")
    async def status(self, interaction: discord.Interaction, appeal_id: int):
        item = self.bot.appeal_store.read()["items"].get(str(appeal_id))
        if not item:
            await send_embed(interaction, self.bot, "Appeal Status", "Appeal not found.", ephemeral=True)
            return
        await send_embed(interaction, self.bot, "Appeal Status", f"Appeal #{appeal_id} status: **{item['status']}**")

    @appeals.command(name="review", description="Open appeal review controls")
    async def review(self, interaction: discord.Interaction, appeal_id: int):
        item = self.bot.appeal_store.read()["items"].get(str(appeal_id))
        if not item:
            await send_embed(interaction, self.bot, "Appeal Review", "Appeal not found.", ephemeral=True)
            return
        view = AppealReviewView(self.bot, appeal_id)
        await interaction.response.send_message(embed=build_embed(self.bot, interaction.guild, "Appeal Review", f"Review appeal #{appeal_id} | case #{item['case_id']}"), view=view)


async def setup(bot):
    await bot.add_cog(AppealsCog(bot))
