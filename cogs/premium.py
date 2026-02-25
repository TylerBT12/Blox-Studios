from __future__ import annotations

import secrets

import discord
from discord import app_commands
from discord.ext import commands, tasks

from core.embeds import build_embed, send_embed
from core.premium import TIERS
from core.timeparse import format_dt, parse_duration


class PremiumCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.expiry_loop.start()

    def cog_unload(self):
        self.expiry_loop.cancel()

    def _is_owner(self, user_id: int) -> bool:
        return user_id in self.bot.config.get("owner_ids", [])

    def _can_control(self, guild_id: int, user_id: int) -> bool:
        return self.bot.premium.can_control(guild_id, user_id, self.bot.config.get("owner_ids", []))

    premium = app_commands.Group(name="premium", description="Premium management")
    key = app_commands.Group(name="key", description="License key management")

    @premium.command(name="status", description="Show guild premium status")
    async def status(self, interaction: discord.Interaction):
        p = self.bot.premium.get(interaction.guild_id)
        e = build_embed(self.bot, interaction.guild, "Premium Status", f"Active: **{self.bot.premium.is_active(interaction.guild_id)}**\nTier: **{p.get('tier') or 'None'}**\nExpires: **{format_dt(p.get('expires_at'))}**")
        controllers = self.bot.premium.list_controllers(interaction.guild_id)
        e.add_field(name="Premium Controllers", value=", ".join(f"<@{u}>" for u in controllers) if controllers else "None")
        await interaction.response.send_message(embed=e)

    @premium.command(name="redeem", description="Redeem a premium license key")
    async def redeem(self, interaction: discord.Interaction, key: str):
        if not self._can_control(interaction.guild_id, interaction.user.id):
            await send_embed(interaction, self.bot, "Premium Access Denied", "You are not allowed to manage premium. Ask owner to add you as controller.", ephemeral=True)
            return
        lic = self.bot.premium.redeem(key, interaction.guild_id)
        if not lic:
            await send_embed(interaction, self.bot, "Invalid Key", "This license key is invalid or exhausted.", ephemeral=True)
            return
        expiry = parse_duration(lic["duration"])
        self.bot.premium.set_premium(interaction.guild_id, lic["tier"], expiry.isoformat() if expiry else None, interaction.user.id)
        await send_embed(interaction, self.bot, "Premium Redeemed", f"Tier: **{lic['tier']}**\nExpires: **{format_dt(expiry.isoformat() if expiry else None)}**")

    @premium.command(name="tiercheck", description="Check your guild premium tier")
    async def tiercheck(self, interaction: discord.Interaction):
        p = self.bot.premium.get(interaction.guild_id)
        await send_embed(interaction, self.bot, "Premium Tier", f"Current tier: **{p.get('tier') or 'None'}**")

    @premium.command(name="features", description="List premium feature locks")
    async def features(self, interaction: discord.Interaction):
        text = "**Gold:** advanced embeds\n**Platinum:** dashboard widgets + analytics\n**Enterprise:** full analytics + white-label branding"
        await send_embed(interaction, self.bot, "Premium Features", text)

    @premium.command(name="activate_tier", description="Activate premium tier manually")
    async def activate_tier(self, interaction: discord.Interaction, tier: str, duration: str):
        if not self._can_control(interaction.guild_id, interaction.user.id):
            await send_embed(interaction, self.bot, "Premium Access Denied", "You are not allowed to manage premium.", ephemeral=True)
            return
        if tier not in TIERS:
            await send_embed(interaction, self.bot, "Invalid Tier", f"Tier must be one of {TIERS}", ephemeral=True)
            return
        expiry = parse_duration(duration)
        self.bot.premium.set_premium(interaction.guild_id, tier, expiry.isoformat() if expiry else None, interaction.user.id)
        await send_embed(interaction, self.bot, "Premium Updated", f"Tier set to **{tier}**\nExpires: **{format_dt(expiry.isoformat() if expiry else None)}**")

    @premium.command(name="deactivate", description="Deactivate premium for this guild")
    async def deactivate(self, interaction: discord.Interaction):
        if not self._can_control(interaction.guild_id, interaction.user.id):
            await send_embed(interaction, self.bot, "Premium Access Denied", "You are not allowed to manage premium.", ephemeral=True)
            return
        self.bot.premium.remove_premium(interaction.guild_id)
        await send_embed(interaction, self.bot, "Premium Deactivated", "Premium is now disabled for this guild.")

    @premium.command(name="add_controller", description="Allow a user to manage premium in this guild")
    async def add_controller(self, interaction: discord.Interaction, user: discord.Member):
        if not self._is_owner(interaction.user.id):
            await send_embed(interaction, self.bot, "Owner Only", "Only global owners can assign premium controllers.", ephemeral=True)
            return
        updated = self.bot.premium.add_controller(interaction.guild_id, user.id)
        await send_embed(interaction, self.bot, "Controller Added", f"Added {user.mention} as premium controller.\nTotal controllers: **{len(updated)}**")

    @premium.command(name="remove_controller", description="Remove premium manager access from user")
    async def remove_controller(self, interaction: discord.Interaction, user: discord.Member):
        if not self._is_owner(interaction.user.id):
            await send_embed(interaction, self.bot, "Owner Only", "Only global owners can remove premium controllers.", ephemeral=True)
            return
        updated = self.bot.premium.remove_controller(interaction.guild_id, user.id)
        await send_embed(interaction, self.bot, "Controller Removed", f"Removed {user.mention}.\nTotal controllers: **{len(updated)}**")

    @premium.command(name="controllers", description="List users allowed to control premium")
    async def controllers(self, interaction: discord.Interaction):
        rows = self.bot.premium.list_controllers(interaction.guild_id)
        if not rows:
            await send_embed(interaction, self.bot, "Premium Controllers", "No premium controllers configured.")
            return
        await send_embed(interaction, self.bot, "Premium Controllers", "\n".join(f"- <@{uid}> (`{uid}`)" for uid in rows))

    @key.command(name="create", description="Create a license key (owner only)")
    async def key_create(self, interaction: discord.Interaction, tier: str, duration: str, uses: app_commands.Range[int, 1, 100] = 1):
        if not self._is_owner(interaction.user.id):
            await send_embed(interaction, self.bot, "Owner Only", "Only global owners can create license keys.", ephemeral=True)
            return
        if tier not in TIERS:
            await send_embed(interaction, self.bot, "Invalid Tier", f"Tier must be one of {TIERS}", ephemeral=True)
            return
        _ = parse_duration(duration)
        code = secrets.token_urlsafe(16)
        self.bot.premium.create_license(code, tier, duration, uses)
        await send_embed(interaction, self.bot, "License Key Created", f"Key: `{code}`\nTier: **{tier}**\nDuration: **{duration}**\nUses: **{uses}**")

    @tasks.loop(minutes=1)
    async def expiry_loop(self):
        expired = self.bot.premium.expire_due()
        if expired:
            print(f"Expired premium for {expired}")


async def setup(bot):
    await bot.add_cog(PremiumCog(bot))
