from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

from core.embeds import apply_variables, build_embed


class DashboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop.start()

    def cog_unload(self):
        self.loop.cancel()

    dash = app_commands.Group(name="dashboard", description="Dashboard system")

    @dash.command(name="post", description="Post live dashboard embed")
    async def post(self, interaction: discord.Interaction):
        conf = self.bot.guild_store.read().get(str(interaction.guild_id), {})
        status = "Premium" if self.bot.premium.is_active(interaction.guild_id) else "Free"
        desc = conf.get("dashboard_template", "Server: {guild_name}\nMembers: {member_count}\nSession: {session_status}\nPremium: {premium_status}\nUpdated: {timestamp}")
        desc = apply_variables(desc, interaction.guild, interaction.user, {
            "session_status": "Online",
            "premium_status": status,
        })
        e = build_embed(self.bot, interaction.guild, "Live Dashboard", desc)
        msg = await interaction.channel.send(embed=e)

        def updater(data):
            gc = data.get(str(interaction.guild_id), {})
            gc["dashboard_message_id"] = msg.id
            gc["dashboard_channel_id"] = interaction.channel_id
            data[str(interaction.guild_id)] = gc
            return data

        self.bot.guild_store.update(updater)
        await interaction.response.send_message("Dashboard posted and linked.", ephemeral=True)

    @dash.command(name="template", description="Set dashboard template")
    async def template(self, interaction: discord.Interaction, template: str):
        def updater(data):
            gc = data.get(str(interaction.guild_id), {})
            gc["dashboard_template"] = template
            data[str(interaction.guild_id)] = gc
            return data

        self.bot.guild_store.update(updater)
        await interaction.response.send_message("Dashboard template updated.")

    @dash.command(name="toggle_widget", description="Toggle dashboard widgets")
    async def toggle_widget(self, interaction: discord.Interaction, widget: str, enabled: bool):
        def updater(data):
            gc = data.get(str(interaction.guild_id), {})
            widgets = gc.get("widgets", {})
            widgets[widget] = enabled
            gc["widgets"] = widgets
            data[str(interaction.guild_id)] = gc
            return data

        self.bot.guild_store.update(updater)
        await interaction.response.send_message(f"Widget `{widget}` set to {enabled}")

    @dash.command(name="embed_style", description="Customize dashboard embed style")
    async def embed_style(self, interaction: discord.Interaction, color: str, footer: str = "", author: str = ""):
        color_int = int(color.replace("#", ""), 16)

        def updater(data):
            gc = data.get(str(interaction.guild_id), {})
            gc["embed_style"] = {"color": color_int, "footer": footer, "author": author}
            data[str(interaction.guild_id)] = gc
            return data

        self.bot.guild_store.update(updater)
        await interaction.response.send_message("Style updated.")

    @dash.command(name="reset", description="Reset dashboard settings")
    async def reset(self, interaction: discord.Interaction):
        def updater(data):
            data[str(interaction.guild_id)] = {}
            return data

        self.bot.guild_store.update(updater)
        await interaction.response.send_message("Dashboard settings reset.")

    @dash.command(name="preview", description="Preview dashboard embed without posting")
    async def preview(self, interaction: discord.Interaction):
        conf = self.bot.guild_store.read().get(str(interaction.guild_id), {})
        status = "Premium" if self.bot.premium.is_active(interaction.guild_id) else "Free"
        desc = conf.get("dashboard_template", "Server: {guild_name}\nMembers: {member_count}\nSession: {session_status}\nPremium: {premium_status}\nUpdated: {timestamp}")
        desc = apply_variables(desc, interaction.guild, interaction.user, {"session_status": "Online", "premium_status": status})
        e = build_embed(self.bot, interaction.guild, "Dashboard Preview", desc)
        await interaction.response.send_message(embed=e, ephemeral=True)

    @dash.command(name="refresh_now", description="Force refresh the linked dashboard message")
    async def refresh_now(self, interaction: discord.Interaction):
        conf = self.bot.guild_store.read().get(str(interaction.guild_id), {})
        message_id = conf.get("dashboard_message_id")
        channel_id = conf.get("dashboard_channel_id")
        if not message_id or not channel_id:
            await interaction.response.send_message("No linked dashboard message found.", ephemeral=True)
            return
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message("Configured dashboard channel not found.", ephemeral=True)
            return
        try:
            msg = await channel.fetch_message(message_id)
        except discord.NotFound:
            await interaction.response.send_message("Dashboard message no longer exists.", ephemeral=True)
            return
        status = "Premium" if self.bot.premium.is_active(interaction.guild_id) else "Free"
        desc = conf.get("dashboard_template", "Server: {guild_name}\nMembers: {member_count}\nSession: {session_status}\nPremium: {premium_status}\nUpdated: {timestamp}")
        desc = apply_variables(desc, interaction.guild, interaction.user, {"session_status": "Online", "premium_status": status})
        await msg.edit(embed=build_embed(self.bot, interaction.guild, "Live Dashboard", desc))
        await interaction.response.send_message("Dashboard refreshed.", ephemeral=True)

    @tasks.loop(seconds=120)
    async def loop(self):
        guild_data = self.bot.guild_store.read()
        for guild_id, conf in guild_data.items():
            message_id = conf.get("dashboard_message_id")
            channel_id = conf.get("dashboard_channel_id")
            if not message_id or not channel_id:
                continue
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue
            channel = guild.get_channel(channel_id)
            if not channel:
                continue
            try:
                msg = await channel.fetch_message(message_id)
            except discord.NotFound:
                continue
            desc = conf.get("dashboard_template", "Server: {guild_name}\nMembers: {member_count}\nPremium: {premium_status}\nUpdated: {timestamp}")
            desc = apply_variables(desc, guild, guild.me, {
                "session_status": "Online",
                "premium_status": "Premium" if self.bot.premium.is_active(int(guild_id)) else "Free",
            })
            e = build_embed(self.bot, guild, "Live Dashboard", desc)
            e.timestamp = datetime.now(timezone.utc)
            try:
                await msg.edit(embed=e)
            except discord.Forbidden:
                pass


async def setup(bot):
    cog = DashboardCog(bot)
    await bot.add_cog(cog)
