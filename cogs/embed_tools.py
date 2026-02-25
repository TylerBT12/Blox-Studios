from __future__ import annotations

import json

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from core.embeds import send_embed


class EmbedToolsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    embed = app_commands.Group(name="embed", description="Simple embed + Discohook tools")

    def _get_webhook(self, guild_id: int) -> str | None:
        data = self.bot.guild_store.read().get(str(guild_id), {})
        return data.get("discohook_webhook_url")

    def _set_webhook(self, guild_id: int, url: str) -> None:
        def updater(data):
            g = data.get(str(guild_id), {})
            g["discohook_webhook_url"] = url
            data[str(guild_id)] = g
            return data

        self.bot.guild_store.update(updater)

    @embed.command(name="setwebhook", description="Set your Discohook/Discord webhook URL")
    async def setwebhook(self, interaction: discord.Interaction, url: str):
        if not url.startswith("https://discord.com/api/webhooks/"):
            await send_embed(interaction, self.bot, "Invalid Webhook", "Webhook URL must start with `https://discord.com/api/webhooks/`", ephemeral=True)
            return
        self._set_webhook(interaction.guild_id, url)
        await send_embed(interaction, self.bot, "Webhook Saved", "Your Discohook webhook URL has been saved.")

    @embed.command(name="status", description="Show webhook setup status")
    async def status(self, interaction: discord.Interaction):
        url = self._get_webhook(interaction.guild_id)
        if not url:
            await send_embed(interaction, self.bot, "Webhook Status", "No webhook set. Use `/embed setwebhook <url>`.")
            return
        masked = url[:40] + "..." + url[-8:]
        await send_embed(interaction, self.bot, "Webhook Status", f"Configured: `{masked}`")

    @embed.command(name="post", description="Post a simple custom embed")
    async def post(self, interaction: discord.Interaction, title: str, description: str):
        e = discord.Embed(title=title[:256], description=description[:4000], color=discord.Color.blurple())
        await interaction.channel.send(embed=e)
        await send_embed(interaction, self.bot, "Embed Posted", "Your custom embed was sent.", ephemeral=True)

    @embed.command(name="post_discohook", description="Post raw Discohook JSON payload to webhook")
    async def post_discohook(self, interaction: discord.Interaction, payload_json: str):
        url = self._get_webhook(interaction.guild_id)
        if not url:
            await send_embed(interaction, self.bot, "Webhook Missing", "Set webhook first with `/embed setwebhook <url>`.", ephemeral=True)
            return

        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            await send_embed(interaction, self.bot, "Invalid JSON", "Payload must be valid JSON copied from Discohook.", ephemeral=True)
            return

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status >= 300:
                    txt = await resp.text()
                    await send_embed(interaction, self.bot, "Webhook Error", f"Failed with status {resp.status}: {txt[:1200]}", ephemeral=True)
                    return

        await send_embed(interaction, self.bot, "Discohook Payload Sent", "Webhook message was posted successfully.")


async def setup(bot):
    await bot.add_cog(EmbedToolsCog(bot))
