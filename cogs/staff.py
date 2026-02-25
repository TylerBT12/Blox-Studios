from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from core.embeds import send_embed
from core.storage import JsonStore


class StaffCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.store = JsonStore("data/staff.json", {})

    staff = app_commands.Group(name="staff", description="Staff management")

    @staff.command(name="promote", description="Promote staff member")
    async def promote(self, interaction: discord.Interaction, member: discord.Member, rank: str):
        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            record = g.get(str(member.id), {"history": []})
            record["rank"] = rank
            record["history"].append({"action": "promote", "to": rank, "by": interaction.user.id, "at": datetime.now(timezone.utc).isoformat()})
            g[str(member.id)] = record
            data[str(interaction.guild_id)] = g
            return data

        self.store.update(updater)
        await send_embed(interaction, self.bot, "Staff Promotion", f"Promoted {member.mention} to **{rank}**")

    @staff.command(name="demote", description="Demote staff member")
    async def demote(self, interaction: discord.Interaction, member: discord.Member, rank: str, appealable: bool = True):
        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            record = g.get(str(member.id), {"history": []})
            record["rank"] = rank
            record["history"].append({"action": "demote", "to": rank, "appealable": appealable, "by": interaction.user.id, "at": datetime.now(timezone.utc).isoformat()})
            g[str(member.id)] = record
            data[str(interaction.guild_id)] = g
            return data

        self.store.update(updater)
        await send_embed(interaction, self.bot, "Staff Demotion", f"Demoted {member.mention} to **{rank}**\nAppealable: **{appealable}**")

    @staff.command(name="infraction", description="Log staff infraction")
    async def infraction(self, interaction: discord.Interaction, member: discord.Member, reason: str, points: app_commands.Range[int, 1, 50] = 1):
        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            record = g.get(str(member.id), {"history": [], "infractions": []})
            infra = record.get("infractions", [])
            infra.append({"reason": reason, "points": points, "by": interaction.user.id, "at": datetime.now(timezone.utc).isoformat()})
            record["infractions"] = infra
            g[str(member.id)] = record
            data[str(interaction.guild_id)] = g
            return data

        self.store.update(updater)
        await send_embed(interaction, self.bot, "Staff Infraction", f"Infraction added to {member.mention}\nReason: {reason}\nPoints: {points}")

    @staff.command(name="profile", description="View staff profile")
    async def profile(self, interaction: discord.Interaction, member: discord.Member):
        record = self.store.read().get(str(interaction.guild_id), {}).get(str(member.id))
        if not record:
            await send_embed(interaction, self.bot, "Staff Profile", "No staff profile found.")
            return
        inf = len(record.get("infractions", []))
        await send_embed(interaction, self.bot, "Staff Profile", f"Member: {member.mention}\nRank: {record.get('rank', 'N/A')}\nInfractions: {inf}\nHistory entries: {len(record.get('history', []))}")


async def setup(bot):
    await bot.add_cog(StaffCog(bot))
