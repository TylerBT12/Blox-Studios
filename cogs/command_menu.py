from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core.embeds import build_embed


class CommandMenuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    menu = app_commands.Group(name="menu", description="Command navigation center")

    def _slash_commands(self, include_owner: bool) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        for cmd in self.bot.tree.get_commands():
            name = f"/{cmd.qualified_name}"
            desc = cmd.description or "No description"
            if not include_owner and cmd.name in {"license_generate"}:
                continue
            rows.append((name, desc))
        rows.sort(key=lambda x: x[0])
        return rows

    def _owner_prefix_commands(self) -> list[str]:
        owner_cog = self.bot.get_cog("OwnerPanel")
        if not owner_cog:
            return []
        cmds = []
        for cmd in owner_cog.get_commands():
            cmds.append(f".{cmd.name}")
        return sorted(cmds)

    @menu.command(name="all", description="Show all available commands")
    async def all_commands(self, interaction: discord.Interaction):
        is_owner = interaction.user.id in self.bot.config.get("owner_ids", [])
        slash_rows = self._slash_commands(include_owner=is_owner)
        owner_rows = self._owner_prefix_commands() if is_owner else []

        embed = build_embed(self.bot, interaction.guild, "Command Menu", "Browse all command systems and categories.")
        if slash_rows:
            block = "\n".join([f"`{name}` - {desc}" for name, desc in slash_rows[:25]])
            embed.add_field(name="Slash Commands", value=block, inline=False)
            if len(slash_rows) > 25:
                embed.add_field(name="Slash Overflow", value=f"+{len(slash_rows)-25} more (use /menu category)", inline=False)
        if owner_rows:
            embed.add_field(name="Owner Prefix Commands", value="\n".join(f"`{c}`" for c in owner_rows), inline=False)
        elif not is_owner:
            embed.add_field(name="Owner Commands", value="Hidden (owner-only)", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @menu.command(name="category", description="Show commands from a specific category")
    async def category(self, interaction: discord.Interaction, name: str):
        key = name.strip().lower()
        categories: dict[str, list[tuple[str, str]]] = {}
        for cmd in self.bot.tree.get_commands():
            root = cmd.qualified_name.split(" ")[0]
            categories.setdefault(root, []).append((f"/{cmd.qualified_name}", cmd.description or "No description"))

        rows = categories.get(key)
        if not rows:
            await interaction.response.send_message("Unknown category. Example: premium, dashboard, moderation, menu", ephemeral=True)
            return

        rows.sort(key=lambda x: x[0])
        lines = "\n".join([f"`{n}` - {d}" for n, d in rows[:30]])
        e = build_embed(self.bot, interaction.guild, f"Category: {key}", lines)
        await interaction.response.send_message(embed=e, ephemeral=True)

    @menu.command(name="search", description="Search commands by keyword")
    async def search(self, interaction: discord.Interaction, query: str):
        q = query.lower().strip()
        is_owner = interaction.user.id in self.bot.config.get("owner_ids", [])
        matches: list[str] = []

        for cmd in self.bot.tree.get_commands():
            name = f"/{cmd.qualified_name}"
            desc = cmd.description or ""
            hay = f"{name} {desc}".lower()
            if q in hay:
                matches.append(f"`{name}` - {desc}")

        if is_owner:
            for c in self._owner_prefix_commands():
                if q in c.lower():
                    matches.append(f"`{c}` - owner panel command")

        if not matches:
            await interaction.response.send_message("No commands matched your query.", ephemeral=True)
            return

        e = build_embed(self.bot, interaction.guild, f"Search: {query}", "\n".join(matches[:35]))
        await interaction.response.send_message(embed=e, ephemeral=True)


async def setup(bot):
    cog = CommandMenuCog(bot)
    await bot.add_cog(cog)
