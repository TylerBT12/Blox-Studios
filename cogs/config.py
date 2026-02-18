from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cfg = app_commands.Group(name="config", description="Guild configuration")

    @cfg.command(name="set_channel", description="Set system channel")
    async def set_channel(self, interaction: discord.Interaction, kind: str, channel: discord.TextChannel):
        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            channels = g.get("channels", {})
            channels[kind] = channel.id
            g["channels"] = channels
            data[str(interaction.guild_id)] = g
            return data

        self.bot.guild_store.update(updater)
        await interaction.response.send_message(f"Set {kind} channel to {channel.mention}")

    @cfg.command(name="allow_role", description="Allow role for a permission key")
    async def allow_role(self, interaction: discord.Interaction, permission_key: str, role: discord.Role):
        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            perms = g.get("permissions", {})
            arr = set(perms.get(permission_key, []))
            arr.add(role.id)
            perms[permission_key] = list(arr)
            g["permissions"] = perms
            data[str(interaction.guild_id)] = g
            return data

        self.bot.guild_store.update(updater)
        await interaction.response.send_message(f"Role {role.mention} allowed for `{permission_key}`")

    @cfg.command(name="embed_brand", description="Set guild embed branding")
    async def embed_brand(self, interaction: discord.Interaction, footer: str = "", author: str = "", banner_url: str = "", thumbnail_url: str = ""):
        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            g["embed_branding"] = {
                "footer": footer,
                "author": author,
                "banner_url": banner_url,
                "thumbnail_url": thumbnail_url,
            }
            data[str(interaction.guild_id)] = g
            return data

        self.bot.guild_store.update(updater)
        await interaction.response.send_message("Embed branding updated.")

    @cfg.command(name="premium_toggle", description="Toggle premium feature by key")
    async def premium_toggle(self, interaction: discord.Interaction, key: str, enabled: bool):
        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            toggles = g.get("premium_toggles", {})
            toggles[key] = enabled
            g["premium_toggles"] = toggles
            data[str(interaction.guild_id)] = g
            return data

        self.bot.guild_store.update(updater)
        await interaction.response.send_message(f"Premium toggle `{key}`={enabled}")

    @cfg.command(name="show", description="Show current guild config")
    async def show(self, interaction: discord.Interaction):
        data = self.bot.guild_store.read().get(str(interaction.guild_id), {})
        pretty = str(data)
        await interaction.response.send_message(pretty[:1900] or "No config yet")


async def setup(bot):
    cog = ConfigCog(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.cfg)
