from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core.embeds import build_embed, send_embed


class ConfigMenuSelect(discord.ui.Select):
    def __init__(self, cog: "ConfigCog", guild_id: int):
        self.cog = cog
        self.guild_id = guild_id
        options = [
            discord.SelectOption(label="Channels", value="channels", description="Log/appeal/session channels"),
            discord.SelectOption(label="Permissions", value="permissions", description="Allowed roles per key"),
            discord.SelectOption(label="Embed Branding", value="embed_branding", description="Author/footer/banner/thumbnail"),
            discord.SelectOption(label="Premium", value="premium_toggles", description="Premium feature toggles + access"),
            discord.SelectOption(label="Dashboard", value="dashboard", description="Dashboard template/style/widgets"),
            discord.SelectOption(label="Embed Templates", value="embed_templates", description="Title/description prefixes & suffixes"),
        ]
        super().__init__(placeholder="Choose a config category", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        await self.cog.render_category(interaction, self.guild_id, category)


class ConfigMenuView(discord.ui.View):
    def __init__(self, cog: "ConfigCog", guild_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.guild_id = guild_id
        self.add_item(ConfigMenuSelect(cog, guild_id))

    @discord.ui.button(label="Set Key/Value", style=discord.ButtonStyle.primary)
    async def set_value(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.send_modal(SetConfigModal(self.cog, self.guild_id))


class SetConfigModal(discord.ui.Modal, title="Set Config Value"):
    key = discord.ui.TextInput(label="Key", placeholder="example: channels.logs or premium_toggles.analytics", max_length=100)
    value = discord.ui.TextInput(label="Value", placeholder="text / ID / true / false", style=discord.TextStyle.paragraph, max_length=500)

    def __init__(self, cog: "ConfigCog", guild_id: int):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        key_path = str(self.key)
        value_text = str(self.value)

        if value_text.lower() in {"true", "false"}:
            parsed_value = value_text.lower() == "true"
        else:
            try:
                parsed_value = int(value_text)
            except ValueError:
                parsed_value = value_text

        parts = [p for p in key_path.split(".") if p]
        if not parts:
            await send_embed(interaction, self.cog.bot, "Config Error", "Invalid key path.", ephemeral=True)
            return

        def updater(data):
            g = data.get(str(self.guild_id), {})
            cur = g
            for part in parts[:-1]:
                nxt = cur.get(part)
                if not isinstance(nxt, dict):
                    nxt = {}
                    cur[part] = nxt
                cur = nxt
            cur[parts[-1]] = parsed_value
            data[str(self.guild_id)] = g
            return data

        self.cog.bot.guild_store.update(updater)
        await send_embed(interaction, self.cog.bot, "Config Updated", f"Updated `{key_path}` -> `{parsed_value}`", ephemeral=True)


class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cfg = app_commands.Group(name="config", description="All server configuration commands")

    async def render_category(self, interaction: discord.Interaction, guild_id: int, category: str):
        data = self.bot.guild_store.read().get(str(guild_id), {})
        if category == "dashboard":
            subset = {
                "dashboard_template": data.get("dashboard_template"),
                "embed_style": data.get("embed_style"),
                "widgets": data.get("widgets", {}),
                "dashboard_channel_id": data.get("dashboard_channel_id"),
            }
        else:
            subset = data.get(category, {})

        text = str(subset) if subset else "No values set yet."
        await send_embed(interaction, self.bot, f"Config Category: {category}", f"```py\n{text[:1800]}\n```", ephemeral=True)

    @app_commands.command(name="configmenu", description="Open clickable config menu")
    async def configmenu(self, interaction: discord.Interaction):
        view = ConfigMenuView(self, interaction.guild_id)
        e = build_embed(self.bot, interaction.guild, "Server Config Menu", "Use the dropdown to browse categories and the button to edit keys.")
        e.add_field(name="Quick Tip", value="Use `/config show` to view all config in one big embed.", inline=False)
        await interaction.response.send_message(embed=e, view=view, ephemeral=True)

    @app_commands.command(name="configset", description="Set any config key quickly")
    async def configset(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SetConfigModal(self, interaction.guild_id))

    @cfg.command(name="set_channel", description="Set a channel for a system (logs/appeals/sessions/etc)")
    async def set_channel(self, interaction: discord.Interaction, kind: str, channel: discord.TextChannel):
        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            channels = g.get("channels", {})
            channels[kind] = channel.id
            g["channels"] = channels
            data[str(interaction.guild_id)] = g
            return data

        self.bot.guild_store.update(updater)
        await send_embed(interaction, self.bot, "Config Saved", f"Set `{kind}` channel to {channel.mention}")

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
        await send_embed(interaction, self.bot, "Config Saved", f"Role {role.mention} allowed for `{permission_key}`")

    @cfg.command(name="embed_brand", description="Set default embed branding")
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
        await send_embed(interaction, self.bot, "Embed Branding Updated", "Branding has been saved for this server.")

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
        await send_embed(interaction, self.bot, "Premium Toggle", f"`{key}` = `{enabled}`")

    @cfg.command(name="embed_template_set", description="Set embed template key")
    async def embed_template_set(self, interaction: discord.Interaction, key: str, value: str):
        allowed = {"title_prefix", "title_suffix", "description_prefix", "description_suffix"}
        if key not in allowed:
            await send_embed(interaction, self.bot, "Config Error", f"Key must be one of {sorted(allowed)}", ephemeral=True)
            return

        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            t = g.get("embed_templates", {})
            t[key] = value
            g["embed_templates"] = t
            data[str(interaction.guild_id)] = g
            return data

        self.bot.guild_store.update(updater)
        await send_embed(interaction, self.bot, "Embed Template Updated", f"`{key}` updated.")

    @cfg.command(name="embed_template_view", description="View embed templates")
    async def embed_template_view(self, interaction: discord.Interaction):
        data = self.bot.guild_store.read().get(str(interaction.guild_id), {}).get("embed_templates", {})
        await send_embed(interaction, self.bot, "Embed Templates", str(data) if data else "No embed templates set.")

    @cfg.command(name="embed_template_reset", description="Reset embed templates")
    async def embed_template_reset(self, interaction: discord.Interaction):
        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            g["embed_templates"] = {}
            data[str(interaction.guild_id)] = g
            return data

        self.bot.guild_store.update(updater)
        await send_embed(interaction, self.bot, "Embed Templates", "Embed templates reset.")

    @cfg.command(name="show", description="Show all config in one big embed")
    async def show(self, interaction: discord.Interaction):
        data = self.bot.guild_store.read().get(str(interaction.guild_id), {})
        e = build_embed(self.bot, interaction.guild, "Server Config Overview", "All config categories scrunched into one view.")

        channels = data.get("channels", {})
        perms = data.get("permissions", {})
        brand = data.get("embed_branding", {})
        toggles = data.get("premium_toggles", {})
        dashboard = {
            "dashboard_template": data.get("dashboard_template"),
            "embed_style": data.get("embed_style"),
            "widgets": data.get("widgets", {}),
            "dashboard_channel_id": data.get("dashboard_channel_id"),
        }
        templates = data.get("embed_templates", {})

        e.add_field(name="Channels", value=f"```py\n{str(channels)[:800]}\n```", inline=False)
        e.add_field(name="Permissions", value=f"```py\n{str(perms)[:800]}\n```", inline=False)
        e.add_field(name="Embed Branding", value=f"```py\n{str(brand)[:800]}\n```", inline=False)
        e.add_field(name="Premium Toggles", value=f"```py\n{str(toggles)[:800]}\n```", inline=False)
        e.add_field(name="Dashboard", value=f"```py\n{str(dashboard)[:800]}\n```", inline=False)
        e.add_field(name="Embed Templates", value=f"```py\n{str(templates)[:800]}\n```", inline=False)
        e.add_field(
            name="Config Commands (Easy Guide)",
            value=(
                "`/config set_channel` • `/config allow_role` • `/config embed_brand`\n"
                "`/config premium_toggle` • `/config embed_template_set`\n"
                "`/config embed_template_view` • `/config embed_template_reset`\n"
                "`/configmenu` • `/configset`"
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=e)


async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
