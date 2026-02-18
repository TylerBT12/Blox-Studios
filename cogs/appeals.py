from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands


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
        await interaction.response.send_message(f"Appeal #{self.appeal_id} marked {status}")

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
        await interaction.response.send_message(f"Appeal submitted with ID #{appeal_id}")

    @appeals.command(name="status", description="Check appeal status")
    async def status(self, interaction: discord.Interaction, appeal_id: int):
        item = self.bot.appeal_store.read()["items"].get(str(appeal_id))
        if not item:
            await interaction.response.send_message("Appeal not found.", ephemeral=True)
            return
        await interaction.response.send_message(f"Appeal #{appeal_id} status: {item['status']}")

    @appeals.command(name="review", description="Open appeal review controls")
    async def review(self, interaction: discord.Interaction, appeal_id: int):
        item = self.bot.appeal_store.read()["items"].get(str(appeal_id))
        if not item:
            await interaction.response.send_message("Appeal not found.", ephemeral=True)
            return
        view = AppealReviewView(self.bot, appeal_id)
        await interaction.response.send_message(f"Review appeal #{appeal_id} | case #{item['case_id']}", view=view)


async def setup(bot):
    cog = AppealsCog(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.appeals)
