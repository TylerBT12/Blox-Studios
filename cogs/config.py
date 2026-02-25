from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core.embeds import build_embed


class ConfigEditModal(discord.ui.Modal, title="Edit Server Config"):
    key = discord.ui.TextInput(label="Key Path", placeholder="channels.logs | permissions.mod | embed_templates.title_prefix", max_length=120)
    value = discord.ui.TextInput(label="Value", placeholder="text / id / true / false", style=discord.TextStyle.paragraph, max_length=600)

    def __init__(self, cog: "ConfigCog", guild_id: int):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        key_path = str(self.key).strip()
        value_text = str(self.value).strip()

        if not key_path:
            await interaction.response.send_message("Invalid key path.", ephemeral=True)
            return

        if value_text.lower() in {"true", "false"}:
            parsed: object = value_text.lower() == "true"
        else:
            try:
                parsed = int(value_text)
            except ValueError:
                parsed = value_text

        parts = [p for p in key_path.split(".") if p]

        def updater(data):
            g = data.get(str(self.guild_id), {})
            cur = g
            for part in parts[:-1]:
                nxt = cur.get(part)
                if not isinstance(nxt, dict):
                    nxt = {}
                    cur[part] = nxt
                cur = nxt
            cur[parts[-1]] = parsed
            data[str(self.guild_id)] = g
            return data

        self.cog.bot.guild_store.update(updater)
        embed = self.cog.make_config_embed(self.guild_id)
        await interaction.response.send_message(f"Updated `{key_path}`.", embed=embed, ephemeral=True)


class ConfigView(discord.ui.View):
    def __init__(self, cog: "ConfigCog", guild_id: int):
        super().__init__(timeout=600)
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.select(
        placeholder="Browse config category",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Channels", value="channels"),
            discord.SelectOption(label="Permissions", value="permissions"),
            discord.SelectOption(label="Embed Branding", value="embed_branding"),
            discord.SelectOption(label="Premium", value="premium_toggles"),
            discord.SelectOption(label="Dashboard", value="dashboard"),
            discord.SelectOption(label="Embed Templates", value="embed_templates"),
        ],
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        cat = select.values[0]
        data = self.cog.bot.guild_store.read().get(str(self.guild_id), {})
        if cat == "dashboard":
            subset = {
                "dashboard_template": data.get("dashboard_template"),
                "embed_style": data.get("embed_style"),
                "widgets": data.get("widgets", {}),
                "dashboard_channel_id": data.get("dashboard_channel_id"),
            }
        else:
            subset = data.get(cat, {})
        e = build_embed(self.cog.bot, interaction.guild, f"Config Category: {cat}", f"```py\n{str(subset)[:3500]}\n```")
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="Edit Key", style=discord.ButtonStyle.primary)
    async def edit_key(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.send_modal(ConfigEditModal(self.cog, self.guild_id))

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.secondary)
    async def refresh(self, interaction: discord.Interaction, _button: discord.ui.Button):
        e = self.cog.make_config_embed(self.guild_id)
        await interaction.response.edit_message(embed=e, view=self)


class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def make_config_embed(self, guild_id: int):
        data = self.bot.guild_store.read().get(str(guild_id), {})
        guild = self.bot.get_guild(guild_id)
        e = build_embed(self.bot, guild, "Server Config", "All config is managed from this single command.")
        e.add_field(name="Channels", value=f"```py\n{str(data.get('channels', {}))[:900]}\n```", inline=False)
        e.add_field(name="Permissions", value=f"```py\n{str(data.get('permissions', {}))[:900]}\n```", inline=False)
        e.add_field(name="Embed Branding", value=f"```py\n{str(data.get('embed_branding', {}))[:900]}\n```", inline=False)
        e.add_field(name="Premium", value=f"```py\n{str(data.get('premium_toggles', {}))[:900]}\n```", inline=False)
        e.add_field(name="Dashboard", value=f"```py\n{str({'dashboard_template': data.get('dashboard_template'), 'embed_style': data.get('embed_style'), 'widgets': data.get('widgets', {}), 'dashboard_channel_id': data.get('dashboard_channel_id')})[:900]}\n```", inline=False)
        e.add_field(name="Embed Templates", value=f"```py\n{str(data.get('embed_templates', {}))[:900]}\n```", inline=False)
        e.add_field(name="How to edit", value="Use the dropdown to inspect categories, and **Edit Key** to update any value path.", inline=False)
        return e

    @app_commands.command(name="config", description="Open the single server config embed/menu")
    async def config(self, interaction: discord.Interaction):
        e = self.make_config_embed(interaction.guild_id)
        await interaction.response.send_message(embed=e, view=ConfigView(self, interaction.guild_id), ephemeral=True)


async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
