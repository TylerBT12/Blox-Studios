from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from core.embeds import send_embed


class SessionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    session = app_commands.Group(name="session", description="Staff session tracking")

    @session.command(name="start", description="Start your staff session")
    async def start(self, interaction: discord.Interaction):
        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            g[str(interaction.user.id)] = {
                "active": True,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "total_seconds": g.get(str(interaction.user.id), {}).get("total_seconds", 0),
                "history": g.get(str(interaction.user.id), {}).get("history", []),
            }
            data[str(interaction.guild_id)] = g
            return data

        self.bot.session_store.update(updater)
        await send_embed(interaction, self.bot, "Session Started", "Your staff session is now active.")

    @session.command(name="end", description="End your staff session")
    async def end(self, interaction: discord.Interaction):
        now = datetime.now(timezone.utc)

        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            info = g.get(str(interaction.user.id))
            if not info or not info.get("active"):
                return data
            started = datetime.fromisoformat(info["started_at"])
            delta = int((now - started).total_seconds())
            info["active"] = False
            info["total_seconds"] = info.get("total_seconds", 0) + delta
            history = info.get("history", [])
            history.append({"start": info["started_at"], "end": now.isoformat(), "seconds": delta})
            info["history"] = history[-100:]
            g[str(interaction.user.id)] = info
            data[str(interaction.guild_id)] = g
            return data

        self.bot.session_store.update(updater)
        await send_embed(interaction, self.bot, "Session Ended", "Your staff session has ended.")

    @session.command(name="status", description="Check a member session status")
    async def status(self, interaction: discord.Interaction, member: discord.Member | None = None):
        member = member or interaction.user
        info = self.bot.session_store.read().get(str(interaction.guild_id), {}).get(str(member.id), {})
        await send_embed(interaction, self.bot, "Session Status", f"Member: {member.mention}\nActive={info.get('active', False)}\nTotal hours={info.get('total_seconds', 0)/3600:.2f}")

    @session.command(name="leaderboard", description="Top staff by session hours")
    async def leaderboard(self, interaction: discord.Interaction):
        data = self.bot.session_store.read().get(str(interaction.guild_id), {})
        ranking = sorted(data.items(), key=lambda kv: kv[1].get("total_seconds", 0), reverse=True)[:10]
        lines = []
        for uid, info in ranking:
            member = interaction.guild.get_member(int(uid))
            name = member.display_name if member else uid
            lines.append(f"{name}: {info.get('total_seconds', 0)/3600:.2f}h")
        await send_embed(interaction, self.bot, "Session Leaderboard", "\n".join(lines) if lines else "No session data")

    @session.command(name="history", description="View recent session history")
    async def history(self, interaction: discord.Interaction, member: discord.Member | None = None):
        member = member or interaction.user
        info = self.bot.session_store.read().get(str(interaction.guild_id), {}).get(str(member.id), {})
        history = info.get("history", [])[-10:]
        if not history:
            await send_embed(interaction, self.bot, "Session History", "No session history found.")
            return
        lines = [f"{i+1}. {h['start']} -> {h['end']} ({h['seconds']/3600:.2f}h)" for i, h in enumerate(history)]
        await send_embed(interaction, self.bot, "Session History", "\n".join(lines))


async def setup(bot):
    await bot.add_cog(SessionsCog(bot))
