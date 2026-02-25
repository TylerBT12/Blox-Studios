from __future__ import annotations

import discord


def module_webhook_enabled(cfg: dict, module: str, is_premium: bool) -> bool:
    if not is_premium:
        return False
    return cfg.get("webhook_modules", {}).get(module, False)


async def send_via_webhook_or_channel(
    channel: discord.TextChannel,
    cfg: dict,
    module: str,
    content: str | None,
    embeds: list[discord.Embed],
    premium_enabled: bool,
):
    if module_webhook_enabled(cfg, module, premium_enabled):
        hooks = await channel.webhooks()
        hook = hooks[0] if hooks else await channel.create_webhook(name="Bot Relay")
        name = cfg.get("webhook_overrides", {}).get(module, {}).get("name") or cfg.get("webhook_name") or "Ops Relay"
        avatar_url = cfg.get("webhook_overrides", {}).get(module, {}).get("avatar_url") or cfg.get("webhook_avatar_url")
        await hook.send(content=content, embeds=embeds[:5], username=name, avatar_url=avatar_url)
        return

    await channel.send(content=content, embeds=embeds[:5])
