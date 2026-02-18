from __future__ import annotations

import secrets

import discord
from discord import app_commands
from discord.ext import commands, tasks

from core.embeds import build_embed
from core.premium import TIERS
from core.timeparse import format_dt, parse_duration


class PremiumCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.expiry_loop.start()

    def cog_unload(self):
        self.expiry_loop.cancel()

    premium = app_commands.Group(name="premium", description="Premium management")

    @premium.command(name="status", description="Show guild premium status")
    async def status(self, interaction: discord.Interaction):
        p = self.bot.premium.get(interaction.guild_id)
        e = build_embed(self.bot, interaction.guild, "Premium Status", f"Active: **{self.bot.premium.is_active(interaction.guild_id)}**\nTier: **{p.get('tier') or 'None'}**\nExpires: **{format_dt(p.get('expires_at'))}**")
        await interaction.response.send_message(embed=e)

    @premium.command(name="redeem", description="Redeem a premium license key")
    async def redeem(self, interaction: discord.Interaction, key: str):
        lic = self.bot.premium.redeem(key, interaction.guild_id)
        if not lic:
            await interaction.response.send_message("Invalid or exhausted key.", ephemeral=True)
            return
        expiry = parse_duration(lic["duration"])
        self.bot.premium.set_premium(interaction.guild_id, lic["tier"], expiry.isoformat() if expiry else None, interaction.user.id)
        await interaction.response.send_message(f"Redeemed! Tier={lic['tier']} expires={format_dt(expiry.isoformat() if expiry else None)}")

    @premium.command(name="tiercheck", description="Check your guild premium tier")
    async def tiercheck(self, interaction: discord.Interaction):
        p = self.bot.premium.get(interaction.guild_id)
        await interaction.response.send_message(f"Current tier: {p.get('tier') or 'None'}")

    @premium.command(name="features", description="List premium feature locks")
    async def features(self, interaction: discord.Interaction):
        text = "Gold: advanced embeds\nPlatinum: dashboard widgets + analytics\nEnterprise: full analytics + white-label branding"
        await interaction.response.send_message(text)

    @app_commands.command(name="license_generate", description="Generate a license key (owner only)")
    async def license_generate(self, interaction: discord.Interaction, tier: str, duration: str, uses: app_commands.Range[int, 1, 100] = 1):
        if interaction.user.id not in self.bot.config.get("owner_ids", []):
            await interaction.response.send_message("Owner only.", ephemeral=True)
            return
        if tier not in TIERS:
            await interaction.response.send_message(f"Tier must be one of {TIERS}", ephemeral=True)
            return
        _ = parse_duration(duration)
        key = secrets.token_urlsafe(16)
        self.bot.premium.create_license(key, tier, duration, uses)
        await interaction.response.send_message(f"Generated key: `{key}`")

    @tasks.loop(minutes=1)
    async def expiry_loop(self):
        expired = self.bot.premium.expire_due()
        if expired:
            print(f"Expired premium for {expired}")


async def setup(bot):
    cog = PremiumCog(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.premium)
    bot.tree.add_command(cog.license_generate)
