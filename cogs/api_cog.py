from __future__ import annotations

import json
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from utils.action_registry import ACTIONS, allowed_actions_for_guild
from utils.timeparse import utc_now_iso


class RunActionModal(discord.ui.Modal, title="Run Game Action"):
    p1 = discord.ui.TextInput(label="Param 1", required=False)
    p2 = discord.ui.TextInput(label="Param 2", required=False)
    p3 = discord.ui.TextInput(label="Param 3", required=False)

    def __init__(self, cog: "APICog", guild_id: int, action_key: str, provider: str):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id
        self.action_key = action_key
        self.provider = provider

    async def on_submit(self, interaction: discord.Interaction):
        action_def = ACTIONS[self.action_key]
        vals = [str(self.p1).strip(), str(self.p2).strip(), str(self.p3).strip()]
        params = {k: v for k, v in zip(action_def.param_names, vals) if v}
        await self.cog._run_action(interaction, self.provider, self.action_key, params)


class APICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    erlc = app_commands.Group(name="erlc", description="ERLC tools")
    maple = app_commands.Group(name="maple", description="Maple tools")
    game = app_commands.Group(name="game", description="In-game actions")

    def _client(self, provider: str):
        return self.bot.erlc if provider == "erlc" else self.bot.maple

    async def _run_action(self, interaction: discord.Interaction, provider: str, action_key: str, params: dict):
        cfg = self.bot.db.get_guild_config(interaction.guild_id)
        if not cfg["api_actions_enabled"]:
            await interaction.response.send_message("API actions disabled in config.", ephemeral=True)
            return
        if action_key not in cfg.get("allowed_actions", list(ACTIONS.keys())):
            await interaction.response.send_message("Action is not allowlisted in /config.", ephemeral=True)
            return

        result = await self._client(provider).run_action(action_key, params)
        self.bot.db.log_api_action(
            interaction.guild_id,
            interaction.user.id,
            provider,
            action_key,
            params.get("player_name", "n/a"),
            json.dumps(result),
            utc_now_iso(),
        )
        await interaction.response.send_message(f"{provider.upper()} action `{action_key}` result: {result.get('message', result)}")

    @erlc.command(name="status")
    async def erlc_status(self, interaction: discord.Interaction):
        out = await self.bot.erlc.status()
        await interaction.response.send_message(str(out))

    @erlc.command(name="players")
    async def erlc_players(self, interaction: discord.Interaction):
        out = await self.bot.erlc.players()
        await interaction.response.send_message(f"ERLC players: {len(out)}")

    @maple.command(name="status")
    async def maple_status(self, interaction: discord.Interaction):
        out = await self.bot.maple.status()
        await interaction.response.send_message(str(out))

    @maple.command(name="players")
    async def maple_players(self, interaction: discord.Interaction):
        out = await self.bot.maple.players()
        await interaction.response.send_message(f"Maple players: {len(out)}")

    @game.command(name="status")
    async def game_status(self, interaction: discord.Interaction):
        cfg = self.bot.db.get_guild_config(interaction.guild_id)
        mode = cfg["provider_mode"]
        await interaction.response.send_message(f"Configured provider mode: {mode}")

    @game.command(name="players")
    async def game_players(self, interaction: discord.Interaction):
        cfg = self.bot.db.get_guild_config(interaction.guild_id)
        mode = cfg["provider_mode"]
        if mode == "erlc":
            out = await self.bot.erlc.players()
            await interaction.response.send_message(f"Players (ERLC): {len(out)}")
        elif mode == "maple":
            out = await self.bot.maple.players()
            await interaction.response.send_message(f"Players (Maple): {len(out)}")
        else:
            e = await self.bot.erlc.players()
            m = await self.bot.maple.players()
            await interaction.response.send_message(f"Players ERLC={len(e)} Maple={len(m)}")

    @game.command(name="actions")
    async def actions(self, interaction: discord.Interaction):
        cfg = self.bot.db.get_guild_config(interaction.guild_id)
        acts = allowed_actions_for_guild(cfg)
        await interaction.response.send_message("Allowed actions:\n" + "\n".join([f"- {a.key}: {a.display}" for a in acts]))

    @game.command(name="run")
    async def run(self, interaction: discord.Interaction, action: str, provider: str = "erlc"):
        if action not in ACTIONS:
            await interaction.response.send_message("Unknown action.", ephemeral=True)
            return
        await interaction.response.send_modal(RunActionModal(self, interaction.guild_id, action, provider))


async def setup(bot):
    await bot.add_cog(APICog(bot))
