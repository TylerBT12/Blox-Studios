from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import discord


BUILT_INS = {
    "date": lambda: datetime.utcnow().strftime("%Y-%m-%d"),
    "time": lambda: datetime.utcnow().strftime("%H:%M UTC"),
}


def validate_discohook_json(raw: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Template must be a JSON object")
    if "embeds" in data and not isinstance(data["embeds"], list):
        raise ValueError("embeds must be a list")
    return data


def _apply_vars(text: str, variables: dict[str, str]) -> str:
    for k, v in variables.items():
        text = text.replace("{" + k + "}", str(v))
    return text


def build_from_template(raw_json: str, variables: dict[str, str]) -> tuple[str | None, list[discord.Embed]]:
    payload = validate_discohook_json(raw_json)
    content = payload.get("content")
    if isinstance(content, str):
        content = _apply_vars(content, variables)

    embeds: list[discord.Embed] = []
    for e in payload.get("embeds", [])[:5]:
        title = _apply_vars(e.get("title", ""), variables) if e.get("title") else None
        description = _apply_vars(e.get("description", ""), variables) if e.get("description") else None
        color = e.get("color", 0x5865F2)
        embed = discord.Embed(title=title, description=description, color=color)
        if e.get("footer") and isinstance(e["footer"], dict):
            embed.set_footer(text=_apply_vars(e["footer"].get("text", ""), variables))
        if e.get("author") and isinstance(e["author"], dict):
            embed.set_author(name=_apply_vars(e["author"].get("name", ""), variables))
        if e.get("thumbnail") and isinstance(e["thumbnail"], dict):
            embed.set_thumbnail(url=e["thumbnail"].get("url", ""))
        if e.get("image") and isinstance(e["image"], dict):
            embed.set_image(url=e["image"].get("url", ""))
        embeds.append(embed)
    return content, embeds
