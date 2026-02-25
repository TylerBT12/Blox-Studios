from __future__ import annotations

import json

import discord
from discord import app_commands
from discord.ext import commands

from utils.embed_templates import validate_discohook_json

TEMPLATE_NAMES = [
    "session_start", "session_end", "session_announce",
    "promotion", "demotion",
    "infraction_issue", "infraction_update",
    "appeal_submitted", "appeal_decision",
    "economy_balance", "economy_transfer", "economy_shop", "economy_admin",
    "api_action_result", "api_action_log",
]

PERM_GROUPS = [
    "session_host_roles", "staff_manage_roles", "infraction_roles",
    "appeal_review_roles", "economy_admin_roles", "api_action_roles", "config_admin_roles",
]


class KeyValueModal(discord.ui.Modal, title="Set Config Key"):
    key = discord.ui.TextInput(label="Key", placeholder="channels.session_announce_channel / variables.server_name")
    value = discord.ui.TextInput(label="Value", style=discord.TextStyle.paragraph, placeholder="channel id / text / true / false")

    def __init__(self, cog: "ConfigCog", guild_id: int):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        key = str(self.key).strip()
        value_text = str(self.value).strip()
        await self.cog.apply_key_value(interaction, self.guild_id, key, value_text)


class TemplateModal(discord.ui.Modal, title="Set Embed Template"):
    name = discord.ui.TextInput(label="Template Name", placeholder="session_start")
    json_payload = discord.ui.TextInput(label="Discohook JSON", style=discord.TextStyle.paragraph, max_length=3500)

    def __init__(self, cog: "ConfigCog", guild_id: int):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        name = str(self.name).strip()
        raw = str(self.json_payload)
        if name not in TEMPLATE_NAMES:
            await interaction.response.send_message(f"Template name not allowed. Use one of: {', '.join(TEMPLATE_NAMES)}", ephemeral=True)
            return
        try:
            validate_discohook_json(raw)
        except Exception as e:
            await interaction.response.send_message(f"Invalid Discohook JSON: {e}", ephemeral=True)
            return
        self.cog.bot.db.set_template(self.guild_id, name, raw)
        await interaction.response.send_message(f"Template `{name}` saved.", ephemeral=True)


class ConfigView(discord.ui.View):
    def __init__(self, cog: "ConfigCog", guild_id: int):
        super().__init__(timeout=900)
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(label="Set Any Key", style=discord.ButtonStyle.primary)
    async def set_key(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.send_modal(KeyValueModal(self.cog, self.guild_id))

    @discord.ui.button(label="Set Template JSON", style=discord.ButtonStyle.secondary)
    async def set_template(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.send_modal(TemplateModal(self.cog, self.guild_id))

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.success)
    async def refresh(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.cog.build_config_embed(self.guild_id), view=self)


class ConfigCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def apply_key_value(self, interaction: discord.Interaction, guild_id: int, key: str, value_text: str):
        cfg = self.bot.db.get_guild_config(guild_id)

        def parse_value(v: str):
            if v.lower() in {"true", "false"}:
                return v.lower() == "true"
            try:
                return int(v)
            except ValueError:
                pass
            if v.startswith("[") or v.startswith("{"):
                try:
                    return json.loads(v)
                except Exception:
                    return v
            return v

        v = parse_value(value_text)

        if key.startswith("channels."):
            k = key.split(".", 1)[1]
            ch = cfg["channels"]
            ch[k] = v
            self.bot.db.update_guild_config(guild_id, "channels", ch)
        elif key.startswith("module_enabled."):
            k = key.split(".", 1)[1]
            me = cfg["module_enabled"]
            me[k] = bool(v)
            self.bot.db.update_guild_config(guild_id, "module_enabled", me)
        elif key == "admins_bypass":
            self.bot.db.update_guild_config(guild_id, "admins_bypass", bool(v))
        elif key.startswith("variables."):
            k = key.split(".", 1)[1]
            self.bot.db.set_variable(guild_id, k, str(v))
        elif key.startswith("permissions."):
            # value expects [role_id,...]
            group = key.split(".", 1)[1]
            if group not in PERM_GROUPS:
                await interaction.response.send_message(f"Unknown permission group: {group}", ephemeral=True)
                return
            if not isinstance(v, list):
                await interaction.response.send_message("For permissions.*, value must be JSON list of role IDs, e.g. [123,456]", ephemeral=True)
                return
            self.bot.db.set_permission_roles(guild_id, group, [int(x) for x in v])
        elif key.startswith("economy."):
            k = key.split(".", 1)[1]
            eco = cfg["economy_settings"]
            eco[k] = v
            self.bot.db.update_guild_config(guild_id, "economy_settings", eco)
        elif key in {"provider_mode", "api_actions_enabled", "require_action_confirmation", "log_all_actions"}:
            self.bot.db.update_guild_config(guild_id, key, v)
        elif key.startswith("webhook."):
            sub = key.split(".", 1)[1]
            if sub == "name":
                self.bot.db.update_guild_config(guild_id, "webhook_name", str(v))
            elif sub == "avatar_url":
                self.bot.db.update_guild_config(guild_id, "webhook_avatar_url", str(v))
            elif sub.startswith("module_"):
                c = self.bot.db.get_guild_config(guild_id)
                wm = c.get("webhook_modules", {})
                wm[sub.replace("module_", "")] = bool(v)
                self.bot.db.update_guild_config(guild_id, "webhook_modules", wm)
            else:
                await interaction.response.send_message("Unknown webhook key.", ephemeral=True)
                return
        elif key == "allowed_actions":
            if not isinstance(v, list):
                await interaction.response.send_message("allowed_actions must be JSON list", ephemeral=True)
                return
            self.bot.db.update_guild_config(guild_id, "allowed_actions", v)
        else:
            await interaction.response.send_message("Unknown key path.", ephemeral=True)
            return

        await interaction.response.send_message("Config updated.", embed=self.build_config_embed(guild_id), ephemeral=True)

    def build_config_embed(self, guild_id: int) -> discord.Embed:
        cfg = self.bot.db.get_guild_config(guild_id)
        vars_map = self.bot.db.get_variables(guild_id)

        e = discord.Embed(title="/config (single control panel)", description="All bot behavior/customization is controlled here.", color=0x5865F2)
        e.add_field(name="Channels", value=f"```py\n{cfg['channels']}\n```", inline=False)
        e.add_field(name="Modules + Bypass", value=f"```py\n{cfg['module_enabled']}\nadmins_bypass={cfg['admins_bypass']}\n```", inline=False)
        perm_preview = {g: self.bot.db.get_permission_roles(guild_id, g) for g in PERM_GROUPS}
        e.add_field(name="Permission Groups", value=f"```py\n{perm_preview}\n```", inline=False)
        e.add_field(name="Variables", value=f"```py\n{vars_map}\n```", inline=False)
        e.add_field(name="Provider/API", value=f"```py\nprovider_mode={cfg['provider_mode']}\napi_actions_enabled={cfg['api_actions_enabled']}\nrequire_action_confirmation={cfg['require_action_confirmation']}\nlog_all_actions={cfg['log_all_actions']}\nallowed_actions={cfg.get('allowed_actions', [])}\n```", inline=False)
        e.add_field(name="Webhook (Premium)", value=f"```py\nname={cfg.get('webhook_name')}\navatar={cfg.get('webhook_avatar_url')}\nmodules={cfg.get('webhook_modules', {})}\n```", inline=False)
        e.add_field(name="Economy", value=f"```py\n{cfg['economy_settings']}\n```", inline=False)
        e.add_field(name="Template Slots", value=", ".join(TEMPLATE_NAMES), inline=False)
        return e

    config = app_commands.Group(name="config", description="GUI config panel")

    @config.command(name="open", description="Open the main config GUI")
    async def open(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.build_config_embed(interaction.guild_id), view=ConfigView(self, interaction.guild_id), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigCog(bot))
