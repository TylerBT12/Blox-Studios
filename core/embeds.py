from __future__ import annotations

from datetime import datetime, timezone

import discord


def apply_variables(text: str, guild: discord.Guild, user: discord.abc.User, extra: dict[str, str] | None = None) -> str:
    values = {
        "guild_name": guild.name,
        "member_count": str(guild.member_count or 0),
        "user": user.mention,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    if extra:
        values.update(extra)

    for key, value in values.items():
        text = text.replace(f"{{{key}}}", value)
    return text


def build_embed(bot, guild: discord.Guild, title: str, description: str) -> discord.Embed:
    color = bot.config.get("default_embed_color", 3447003)
    brand = bot.config.get("branding", {})

    embed = discord.Embed(title=title, description=description, color=color)
    if brand.get("author_name"):
        embed.set_author(name=brand["author_name"])
    if brand.get("footer_text"):
        embed.set_footer(text=brand["footer_text"])
    if brand.get("thumbnail_url"):
        embed.set_thumbnail(url=brand["thumbnail_url"])
    if brand.get("banner_url"):
        embed.set_image(url=brand["banner_url"])
    return embed
