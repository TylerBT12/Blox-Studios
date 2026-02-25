from __future__ import annotations

from datetime import datetime, timezone

from discord.ext import commands

from core.premium import PREMIUM_PLAN
from core.timeparse import format_dt, parse_duration


class OwnerPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        return ctx.author.id in self.bot.config.get("owner_ids", [])

    @commands.command(name="givepremium")
    async def givepremium(self, ctx: commands.Context, guild_id: int, duration: str):
        expiry = parse_duration(duration)
        self.bot.premium.set_premium(guild_id, PREMIUM_PLAN, expiry.isoformat() if expiry else None, ctx.author.id)
        await ctx.send(f"Premium granted to `{guild_id}` | plan={PREMIUM_PLAN} | expires={format_dt(expiry.isoformat() if expiry else None)}")

    @commands.command(name="extendpremium")
    async def extendpremium(self, ctx: commands.Context, guild_id: int, duration: str):
        prem = self.bot.premium.get(guild_id)
        now = datetime.now(timezone.utc)
        current = prem.get("expires_at")
        base = datetime.fromisoformat(current) if current else now
        extra = parse_duration(duration)
        if extra is None:
            new_expiry = None
        else:
            delta = extra - now
            new_expiry = (base + delta).isoformat()
        self.bot.premium.set_premium(guild_id, PREMIUM_PLAN, new_expiry, ctx.author.id)
        await ctx.send(f"Extended premium for `{guild_id}` to {format_dt(new_expiry)}")

    @commands.command(name="removepremium")
    async def removepremium(self, ctx: commands.Context, guild_id: int):
        self.bot.premium.remove_premium(guild_id)
        await ctx.send(f"Removed premium from `{guild_id}`")

    @commands.command(name="forceexpire")
    async def forceexpire(self, ctx: commands.Context, guild_id: int):
        prem = self.bot.premium.get(guild_id)
        if not prem.get("active"):
            await ctx.send("Guild has no active premium.")
            return
        self.bot.premium.set_premium(guild_id, PREMIUM_PLAN, datetime.now(timezone.utc).isoformat(), ctx.author.id)
        self.bot.premium.expire_due()
        await ctx.send(f"Force expired premium for `{guild_id}`")

    @commands.command(name="guildinfo")
    async def guildinfo(self, ctx: commands.Context, guild_id: int):
        prem = self.bot.premium.get(guild_id)
        await ctx.send(f"Guild `{guild_id}` premium={prem}")

    @commands.command(name="premiumlist")
    async def premiumlist(self, ctx: commands.Context):
        guilds = self.bot.premium.list_guilds()
        if not guilds:
            await ctx.send("No premium guilds found.")
            return
        lines = [f"{gid}: active={v.get('active')} expires={format_dt(v.get('expires_at'))}" for gid, v in guilds.items()]
        await ctx.send("\n".join(lines[:30]))

    @commands.command(name="globalstats")
    async def globalstats(self, ctx: commands.Context):
        guilds = len(self.bot.guilds)
        users = sum(g.member_count or 0 for g in self.bot.guilds)
        premium_count = sum(1 for _, p in self.bot.premium.list_guilds().items() if p.get("active"))
        await ctx.send(f"Guilds={guilds} | Users={users} | PremiumGuilds={premium_count}")

    @commands.command(name="globallist")
    async def globallist(self, ctx: commands.Context):
        lines = [f"{g.id} - {g.name} ({g.member_count})" for g in self.bot.guilds]
        await ctx.send("\n".join(lines[:40]) if lines else "No guilds")


async def setup(bot):
    await bot.add_cog(OwnerPanel(bot))
