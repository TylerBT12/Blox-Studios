from __future__ import annotations

from datetime import datetime, timezone

from discord.ext import commands

from utils.timeparse import parse_duration


class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        return ctx.author.id in self.bot.owner_ids

    @commands.command(name="GrantPremium")
    async def grant_premium(self, ctx: commands.Context, guild_id: int, duration: str):
        expires = parse_duration(duration).isoformat()
        self.bot.db.set_premium(guild_id, expires)
        await ctx.send(f"Premium granted for guild {guild_id} until {expires}")

    @commands.command(name="RevokePremium")
    async def revoke(self, ctx: commands.Context, guild_id: int):
        self.bot.db.revoke_premium(guild_id)
        await ctx.send("Premium revoked")

    @commands.command(name="PremiumStatus")
    async def status(self, ctx: commands.Context, guild_id: int):
        exp = self.bot.db.get_premium(guild_id)
        if not exp:
            await ctx.send("Premium: OFF")
            return
        now = datetime.now(timezone.utc)
        await ctx.send(f"Premium: {'ON' if datetime.fromisoformat(exp) > now else 'EXPIRED'} expires_at={exp}")

    @commands.command(name="OwnerStats")
    async def stats(self, ctx: commands.Context):
        total_guilds = len(self.bot.guilds)
        premium_count = self.bot.db._exec("SELECT COUNT(*) FROM premium").fetchone()[0]
        await ctx.send(f"Guilds={total_guilds} PremiumGuilds={premium_count}")


async def setup(bot):
    await bot.add_cog(OwnerCog(bot))
