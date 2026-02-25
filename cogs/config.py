from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class ConfigMenuSelect(discord.ui.Select):
    def __init__(self, cog: "ConfigCog", guild_id: int):
        self.cog = cog
        self.guild_id = guild_id
        options = [
            discord.SelectOption(label="Channels", value="channels", description="Log/appeal/session channels"),
            discord.SelectOption(label="Permissions", value="permissions", description="Allowed roles per key"),
            discord.SelectOption(label="Embed Branding", value="embed_branding", description="Author/footer/banner/thumbnail"),
            discord.SelectOption(label="Premium Toggles", value="premium_toggles", description="Feature toggles by key"),
            discord.SelectOption(label="Dashboard", value="dashboard", description="Dashboard template/style/widgets"),
            discord.SelectOption(label="Embed Templates", value="embed_templates", description="Global embed title/description styles"),
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
    value = discord.ui.TextInput(label="Value", placeholder="use text/ID/true/false", style=discord.TextStyle.paragraph, max_length=500)

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
            await interaction.response.send_message("Invalid key path.", ephemeral=True)
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
        await interaction.response.send_message(f"Updated `{key_path}` -> `{parsed_value}`", ephemeral=True)


class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cfg = app_commands.Group(name="config", description="Guild configuration")

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
        await interaction.response.send_message(f"**{category}**\n```py\n{text[:1600]}\n```", ephemeral=True)

    @app_commands.command(name="configmenu", description="Open interactive config menu")
    async def configmenu(self, interaction: discord.Interaction):
        view = ConfigMenuView(self, interaction.guild_id)
        await interaction.response.send_message(
            "Config Menu\n- Pick a category from dropdown\n- Use button to set key/value",
            view=view,
            ephemeral=True,
        )

    @app_commands.command(name="configset", description="Set any config key path quickly")
    async def configset(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SetConfigModal(self, interaction.guild_id))

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


    @cfg.command(name="embed_template_set", description="Set a global embed template key")
    async def embed_template_set(self, interaction: discord.Interaction, key: str, value: str):
        allowed = {"title_prefix", "title_suffix", "description_prefix", "description_suffix"}
        if key not in allowed:
            await interaction.response.send_message(f"Key must be one of {sorted(allowed)}", ephemeral=True)
            return

        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            t = g.get("embed_templates", {})
            t[key] = value
            g["embed_templates"] = t
            data[str(interaction.guild_id)] = g
            return data

        self.bot.guild_store.update(updater)
        await interaction.response.send_message(f"Embed template `{key}` updated.")

    @cfg.command(name="embed_template_view", description="View current embed templates")
    async def embed_template_view(self, interaction: discord.Interaction):
        data = self.bot.guild_store.read().get(str(interaction.guild_id), {}).get("embed_templates", {})
        await interaction.response.send_message(str(data) if data else "No embed templates set.")

    @cfg.command(name="embed_template_reset", description="Reset embed templates")
    async def embed_template_reset(self, interaction: discord.Interaction):
        def updater(data):
            g = data.get(str(interaction.guild_id), {})
            g["embed_templates"] = {}
            data[str(interaction.guild_id)] = g
            return data

        self.bot.guild_store.update(updater)
        await interaction.response.send_message("Embed templates reset.")

    @cfg.command(name="show", description="Show current guild config")
    async def show(self, interaction: discord.Interaction):
        data = self.bot.guild_store.read().get(str(interaction.guild_id), {})
        pretty = str(data)
        await interaction.response.send_message(pretty[:1900] or "No config yet")


async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
