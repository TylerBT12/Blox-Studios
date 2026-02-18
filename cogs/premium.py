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

    def _is_owner(self, user_id: int) -> bool:
        return user_id in self.bot.config.get("owner_ids", [])

    def _can_control(self, guild_id: int, user_id: int) -> bool:
        return self.bot.premium.can_control(guild_id, user_id, self.bot.config.get("owner_ids", []))

    premium = app_commands.Group(name="premium", description="Premium management")

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
            await interaction.response.send_message("You are not allowed to manage premium. Ask owner to add you as controller.", ephemeral=True)
            return
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

    @premium.command(name="activate_tier", description="Activate premium tier manually")
    async def activate_tier(self, interaction: discord.Interaction, tier: str, duration: str):
        if not self._can_control(interaction.guild_id, interaction.user.id):
            await interaction.response.send_message("You are not allowed to manage premium.", ephemeral=True)
            return
        if tier not in TIERS:
            await interaction.response.send_message(f"Tier must be one of {TIERS}", ephemeral=True)
            return
        expiry = parse_duration(duration)
        self.bot.premium.set_premium(interaction.guild_id, tier, expiry.isoformat() if expiry else None, interaction.user.id)
        await interaction.response.send_message(f"Premium updated to {tier} (expires: {format_dt(expiry.isoformat() if expiry else None)})")

    @premium.command(name="deactivate", description="Deactivate premium for this guild")
    async def deactivate(self, interaction: discord.Interaction):
        if not self._can_control(interaction.guild_id, interaction.user.id):
            await interaction.response.send_message("You are not allowed to manage premium.", ephemeral=True)
            return
        self.bot.premium.remove_premium(interaction.guild_id)
        await interaction.response.send_message("Premium deactivated for this guild.")

    @premium.command(name="add_controller", description="Allow a user to manage premium in this guild")
    async def add_controller(self, interaction: discord.Interaction, user: discord.Member):
        if not self._is_owner(interaction.user.id):
            await interaction.response.send_message("Owner only.", ephemeral=True)
            return
        updated = self.bot.premium.add_controller(interaction.guild_id, user.id)
        await interaction.response.send_message(f"Added {user.mention} as premium controller. Total: {len(updated)}")

    @premium.command(name="remove_controller", description="Remove premium manager access from user")
    async def remove_controller(self, interaction: discord.Interaction, user: discord.Member):
        if not self._is_owner(interaction.user.id):
            await interaction.response.send_message("Owner only.", ephemeral=True)
            return
        updated = self.bot.premium.remove_controller(interaction.guild_id, user.id)
        await interaction.response.send_message(f"Removed {user.mention} from premium controllers. Total: {len(updated)}")

    @premium.command(name="controllers", description="List users allowed to control premium")
    async def controllers(self, interaction: discord.Interaction):
        rows = self.bot.premium.list_controllers(interaction.guild_id)
        if not rows:
            await interaction.response.send_message("No premium controllers configured.")
            return
        await interaction.response.send_message("\n".join(f"- <@{uid}> (`{uid}`)" for uid in rows))

    @app_commands.command(name="license_generate", description="Generate a license key (owner only)")
    async def license_generate(self, interaction: discord.Interaction, tier: str, duration: str, uses: app_commands.Range[int, 1, 100] = 1):
        if not self._is_owner(interaction.user.id):
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
    await bot.add_cog(PremiumCog(bot))
