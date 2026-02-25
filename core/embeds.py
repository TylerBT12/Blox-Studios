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
    brand = bot.config.get("branding", {}).copy()

    if guild and hasattr(bot, "guild_store"):
        gdata = bot.guild_store.read().get(str(guild.id), {})
        gbrand = gdata.get("embed_branding", {})
        gstyle = gdata.get("embed_style", {})
        gtmpl = gdata.get("embed_templates", {})
        color = gstyle.get("color", color)
        brand["author_name"] = gbrand.get("author", brand.get("author_name", ""))
        brand["footer_text"] = gbrand.get("footer", brand.get("footer_text", ""))
        brand["thumbnail_url"] = gbrand.get("thumbnail_url", brand.get("thumbnail_url", ""))
        brand["banner_url"] = gbrand.get("banner_url", brand.get("banner_url", ""))
        title = f"{gtmpl.get('title_prefix', '')}{title}{gtmpl.get('title_suffix', '')}"
        description = f"{gtmpl.get('description_prefix', '')}{description}{gtmpl.get('description_suffix', '')}"

    embed = discord.Embed(title=title[:256], description=description[:4000], color=color, timestamp=datetime.now(timezone.utc))
    if brand.get("author_name"):
        embed.set_author(name=brand["author_name"])
    if brand.get("footer_text"):
        embed.set_footer(text=brand["footer_text"])
    if brand.get("thumbnail_url"):
        embed.set_thumbnail(url=brand["thumbnail_url"])
    if brand.get("banner_url"):
        embed.set_image(url=brand["banner_url"])
    return embed


async def send_embed(interaction: discord.Interaction, bot, title: str, description: str, ephemeral: bool = False):
    e = build_embed(bot, interaction.guild, title, description)
    await interaction.response.send_message(embed=e, ephemeral=ephemeral)


async def send_embed_followup(interaction: discord.Interaction, bot, title: str, description: str, ephemeral: bool = False):
    e = build_embed(bot, interaction.guild, title, description)
    await interaction.followup.send(embed=e, ephemeral=ephemeral)
