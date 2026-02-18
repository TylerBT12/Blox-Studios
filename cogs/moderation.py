from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from core.embeds import build_embed


class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    mod = app_commands.Group(name="moderation", description="Moderation commands")

    def _new_case(self, guild_id: int, action: str, target_id: int, actor_id: int, reason: str) -> int:
        def updater(data):
            cid = data["next"]
            data["next"] += 1
            data["items"][str(cid)] = {
                "guild_id": guild_id,
                "action": action,
                "target_id": target_id,
                "actor_id": actor_id,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            return data

        new_data = self.bot.case_store.update(updater)
        return new_data["next"] - 1

    @mod.command(name="warn", description="Warn a member")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            user_warnings = g.get(str(member.id), [])
            user_warnings.append({"reason": reason, "by": interaction.user.id, "at": datetime.now(timezone.utc).isoformat()})
            g[str(member.id)] = user_warnings
            data[str(interaction.guild_id)] = g
            return data

        self.bot.warn_store.update(updater)
        case_id = self._new_case(interaction.guild_id, "warn", member.id, interaction.user.id, reason)
        await interaction.response.send_message(f"Warned {member.mention}. Case #{case_id}")

    @mod.command(name="warnings", description="View member warnings")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        data = self.bot.warn_store.read().get(str(interaction.guild_id), {}).get(str(member.id), [])
        if not data:
            await interaction.response.send_message("No warnings found.")
            return
        lines = [f"{i+1}. {w['reason']} (by {w['by']})" for i, w in enumerate(data[-20:])]
        await interaction.response.send_message("\n".join(lines))

    @mod.command(name="removewarn", description="Remove a warning by index")
    async def removewarn(self, interaction: discord.Interaction, member: discord.Member, index: app_commands.Range[int, 1, 100]):
        def updater(data):
            guild_map = data.get(str(interaction.guild_id), {})
            warns = guild_map.get(str(member.id), [])
            if 0 <= index - 1 < len(warns):
                warns.pop(index - 1)
            guild_map[str(member.id)] = warns
            data[str(interaction.guild_id)] = guild_map
            return data

        self.bot.warn_store.update(updater)
        await interaction.response.send_message("Warning removed if it existed.")

    @mod.command(name="kick", description="Kick member")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        case_id = self._new_case(interaction.guild_id, "kick", member.id, interaction.user.id, reason)
        await member.kick(reason=reason)
        await interaction.response.send_message(f"Kicked {member}. Case #{case_id}")

    @mod.command(name="ban", description="Ban member")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        case_id = self._new_case(interaction.guild_id, "ban", member.id, interaction.user.id, reason)
        await interaction.guild.ban(member, reason=reason)
        await interaction.response.send_message(f"Banned {member}. Case #{case_id}")

    @mod.command(name="case", description="View case by ID")
    async def case(self, interaction: discord.Interaction, case_id: int):
        case = self.bot.case_store.read()["items"].get(str(case_id))
        if not case:
            await interaction.response.send_message("Case not found.", ephemeral=True)
            return
        e = build_embed(self.bot, interaction.guild, f"Case #{case_id}", "\n".join([f"**{k}**: {v}" for k, v in case.items()]))
        await interaction.response.send_message(embed=e)


async def setup(bot):
    cog = ModerationCog(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.mod)
