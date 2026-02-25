from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from core.embeds import build_embed, send_embed


class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.started_at = datetime.now(timezone.utc)

    util = app_commands.Group(name="utility", description="Utility and information commands")

    @util.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        await send_embed(interaction, self.bot, "Pong", f"Latency: `{round(self.bot.latency * 1000)}ms`")

    @util.command(name="uptime", description="Show bot uptime")
    async def uptime(self, interaction: discord.Interaction):
        delta = datetime.now(timezone.utc) - self.started_at
        await send_embed(interaction, self.bot, "Uptime", f"Uptime: `{str(delta).split('.')[0]}`")

    @util.command(name="serverinfo", description="Show server info")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        desc = (
            f"ID: `{guild.id}`\n"
            f"Members: `{guild.member_count}`\n"
            f"Channels: `{len(guild.channels)}`\n"
            f"Roles: `{len(guild.roles)}`"
        )
        await interaction.response.send_message(embed=build_embed(self.bot, guild, "Server Info", desc))

    @util.command(name="userinfo", description="Show user info")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member | None = None):
        member = member or interaction.user
        desc = (
            f"User: {member.mention}\n"
            f"ID: `{member.id}`\n"
            f"Joined: `{member.joined_at}`\n"
            f"Created: `{member.created_at}`"
        )
        await interaction.response.send_message(embed=build_embed(self.bot, interaction.guild, "User Info", desc))

    @util.command(name="avatar", description="Show member avatar")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member | None = None):
        member = member or interaction.user
        e = build_embed(self.bot, interaction.guild, "Avatar", member.display_name)
        e.set_image(url=member.display_avatar.url)
        await interaction.response.send_message(embed=e)

    @util.command(name="membercount", description="Show member count")
    async def membercount(self, interaction: discord.Interaction):
        await send_embed(interaction, self.bot, "Member Count", f"Member count: `{interaction.guild.member_count}`")

    @util.command(name="premiuminfo", description="Quick premium status summary")
    async def premiuminfo(self, interaction: discord.Interaction):
        p = self.bot.premium.get(interaction.guild_id)
        await send_embed(interaction, self.bot, "Premium Info", f"Active: `{self.bot.premium.is_active(interaction.guild_id)}`\nTier: `{p.get('tier')}`\nExpires: `{p.get('expires_at')}`")


async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
