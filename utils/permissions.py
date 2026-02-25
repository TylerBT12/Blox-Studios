from __future__ import annotations

from typing import Iterable

import discord


async def has_group_permission(db, interaction: discord.Interaction, group: str) -> bool:
    cfg = db.get_guild_config(interaction.guild_id)
    if not cfg.get("module_enabled", {}).get(group.split("_")[0], True):
        return False

    if cfg.get("admins_bypass", True) and isinstance(interaction.user, discord.Member):
        if interaction.user.guild_permissions.administrator:
            return True

    allowed_role_ids: Iterable[int] = db.get_permission_roles(interaction.guild_id, group)
    if not allowed_role_ids:
        return False

    if not isinstance(interaction.user, discord.Member):
        return False

    member_role_ids = {r.id for r in interaction.user.roles}
    return any(rid in member_role_ids for rid in allowed_role_ids)
