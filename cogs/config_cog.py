from __future__ import annotations

import json

import discord
from discord import app_commands
from discord.ext import commands

from utils.embed_templates import validate_discohook_json
from utils.ui_embeds import config_home_embed, themed_embed

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

MODULE_KEYS = {
    "Default Settings": "default",
    "Infraction Module": "infractions",
    "Review Module": "appeals",
    "Orders Module": "economy",
    "Staff Management Module": "staff",
    "API Actions Module": "api",
    "Session Module": "sessions",
}


class KeyValueModal(discord.ui.Modal, title="Set Config Key"):
    key = discord.ui.TextInput(label="Key", placeholder="channels.staff_logs_channel / variables.server_name")
    value = discord.ui.TextInput(label="Value", style=discord.TextStyle.paragraph, placeholder="channel_id / true/false / text / [json,list]")

    def __init__(self, cog: "ConfigCog", guild_id: int):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.apply_key_value(interaction, self.guild_id, str(self.key).strip(), str(self.value).strip())


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
            await interaction.response.send_message(embed=themed_embed("Invalid Template Name", f"Use one of:\n`{', '.join(TEMPLATE_NAMES)}`", success=False), ephemeral=True)
            return
        try:
            validate_discohook_json(raw)
        except Exception as e:
            await interaction.response.send_message(embed=themed_embed("Invalid Discohook JSON", str(e), success=False), ephemeral=True)
            return
        self.cog.bot.db.set_template(self.guild_id, name, raw)
        await interaction.response.send_message(embed=themed_embed("Template Saved", f"Template `{name}` has been saved."), ephemeral=True)


class ModuleSelect(discord.ui.Select):
    def __init__(self, view: "ConfigView"):
        options = [discord.SelectOption(label=k, value=v, description=f"Configure {k.lower()}") for k, v in MODULE_KEYS.items()]
        super().__init__(placeholder="Select a module to configure", min_values=1, max_values=1, options=options)
        self.cfg_view = view

    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        embed = self.cfg_view.cog.build_module_embed(self.cfg_view.guild_id, key)
        await interaction.response.edit_message(embed=embed, view=self.cfg_view)


class ConfigView(discord.ui.View):
    def __init__(self, cog: "ConfigCog", guild_id: int):
        super().__init__(timeout=900)
        self.cog = cog
        self.guild_id = guild_id
        self.add_item(ModuleSelect(self))

    @discord.ui.button(label="Set Any Key", style=discord.ButtonStyle.primary)
    async def set_key(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.send_modal(KeyValueModal(self.cog, self.guild_id))

    @discord.ui.button(label="Set Template JSON", style=discord.ButtonStyle.secondary)
    async def set_template(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.send_modal(TemplateModal(self.cog, self.guild_id))

    @discord.ui.button(label="Back", style=discord.ButtonStyle.success)
    async def back(self, interaction: discord.Interaction, _button: discord.ui.Button):
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
            self.bot.db.set_variable(guild_id, key.split(".", 1)[1], str(v))
        elif key.startswith("permissions."):
            group = key.split(".", 1)[1]
            if group not in PERM_GROUPS or not isinstance(v, list):
                await interaction.response.send_message(embed=themed_embed("Permission Error", "Use `permissions.<group>` with JSON list of role IDs, e.g. [123,456]", success=False), ephemeral=True)
                return
            self.bot.db.set_permission_roles(guild_id, group, [int(x) for x in v])
        elif key.startswith("economy."):
            eco = cfg["economy_settings"]
            eco[key.split(".", 1)[1]] = v
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
                await interaction.response.send_message(embed=themed_embed("Webhook Error", "Unknown webhook key path.", success=False), ephemeral=True)
                return
        elif key == "allowed_actions":
            if not isinstance(v, list):
                await interaction.response.send_message(embed=themed_embed("Config Error", "allowed_actions must be JSON list", success=False), ephemeral=True)
                return
            self.bot.db.update_guild_config(guild_id, "allowed_actions", v)
        else:
            await interaction.response.send_message(embed=themed_embed("Unknown Key", "Unknown key path. Use channels./permissions./variables./economy./webhook./module_enabled.", success=False), ephemeral=True)
            return

        await interaction.response.send_message(embed=themed_embed("Config Updated", f"Saved `{key}` successfully."), ephemeral=True)

    def build_config_embed(self, guild_id: int) -> discord.Embed:
        cfg = self.bot.db.get_guild_config(guild_id)
        module_states = {
            "default": True,
            "infractions": cfg["module_enabled"].get("infractions", True),
            "appeals": cfg["module_enabled"].get("appeals", True),
            "economy": cfg["module_enabled"].get("economy", True),
            "staff": cfg["module_enabled"].get("staff", True),
            "api": cfg["module_enabled"].get("api", True),
            "sessions": cfg["module_enabled"].get("sessions", True),
        }
        return config_home_embed(module_states)

    def build_module_embed(self, guild_id: int, module_key: str) -> discord.Embed:
        cfg = self.bot.db.get_guild_config(guild_id)
        vars_map = self.bot.db.get_variables(guild_id)
        if module_key == "infractions":
            body = f"module_enabled.infractions = {cfg['module_enabled'].get('infractions', True)}\ninfraction_roles = {self.bot.db.get_permission_roles(guild_id, 'infraction_roles')}\ninfraction_logs_channel = {cfg['channels'].get('infraction_logs_channel')}"
            return themed_embed("Infraction Module", f"```py\n{body}\n```")
        if module_key == "appeals":
            body = f"module_enabled.appeals = {cfg['module_enabled'].get('appeals', True)}\nappeal_review_roles = {self.bot.db.get_permission_roles(guild_id, 'appeal_review_roles')}\nappeals_channel = {cfg['channels'].get('appeals_channel')}"
            return themed_embed("Review Module", f"```py\n{body}\n```")
        if module_key == "economy":
            return themed_embed("Orders Module", f"```py\n{cfg['economy_settings']}\n```")
        if module_key == "staff":
            body = f"module_enabled.staff = {cfg['module_enabled'].get('staff', True)}\nstaff_manage_roles = {self.bot.db.get_permission_roles(guild_id, 'staff_manage_roles')}\nstaff_logs_channel = {cfg['channels'].get('staff_logs_channel')}"
            return themed_embed("Staff Management Module", f"```py\n{body}\n```")
        if module_key == "api":
            body = f"module_enabled.api = {cfg['module_enabled'].get('api', True)}\nprovider_mode = {cfg['provider_mode']}\nallowed_actions = {cfg.get('allowed_actions', [])}"
            return themed_embed("API Actions Module", f"```py\n{body}\n```")
        if module_key == "sessions":
            body = f"module_enabled.sessions = {cfg['module_enabled'].get('sessions', True)}\nsession_host_roles = {self.bot.db.get_permission_roles(guild_id, 'session_host_roles')}\nsession_announce_channel = {cfg['channels'].get('session_announce_channel')}"
            return themed_embed("Session Module", f"```py\n{body}\n```")
        # default
        body = f"channels = {cfg['channels']}\nvariables = {vars_map}\nadmins_bypass = {cfg['admins_bypass']}\ntemplates = {TEMPLATE_NAMES}"
        return themed_embed("Default Settings", f"```py\n{body}\n```")

    config = app_commands.Group(name="config", description="GUI config panel")

    @config.command(name="open", description="Open the main config GUI")
    async def open(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.build_config_embed(interaction.guild_id), view=ConfigView(self, interaction.guild_id), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigCog(bot))
