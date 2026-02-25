from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from utils.ui_embeds import themed_embed


class EconomyAdminView(discord.ui.View):
    def __init__(self, cog: "EconomyCog", guild_id: int):
        super().__init__(timeout=600)
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(label="Add Shop Item", style=discord.ButtonStyle.primary)
    async def add_item(self, interaction: discord.Interaction, _btn: discord.ui.Button):
        await interaction.response.send_modal(AddItemModal(self.cog, self.guild_id))


class AddItemModal(discord.ui.Modal, title="Add Shop Item"):
    name = discord.ui.TextInput(label="Name")
    price = discord.ui.TextInput(label="Price")
    description = discord.ui.TextInput(label="Description")

    def __init__(self, cog: "EconomyCog", guild_id: int):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        self.cog.bot.db.add_shop_item(self.guild_id, str(self.name), int(str(self.price)), str(self.description))
        await interaction.response.send_message("Item added.", ephemeral=True)


class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    economy = app_commands.Group(name="economy", description="Economy commands")

    @economy.command(name="balance")
    async def balance(self, interaction: discord.Interaction):
        bal = self.bot.db.get_balance(interaction.guild_id, interaction.user.id)
        cur = self.bot.db.get_guild_config(interaction.guild_id)["economy_settings"]["currency_name"]
        await interaction.response.send_message(embed=themed_embed("Economy Balance", f"Balance: **{bal} {cur}**"))

    @economy.command(name="daily")
    async def daily(self, interaction: discord.Interaction):
        cfg = self.bot.db.get_guild_config(interaction.guild_id)["economy_settings"]
        cd = self.bot.db.get_cooldowns(interaction.guild_id, interaction.user.id)
        now = datetime.now(timezone.utc)
        if cd["daily_at"]:
            last = datetime.fromisoformat(cd["daily_at"])
            if now - last < timedelta(hours=cfg["daily_cooldown_h"]):
                left = timedelta(hours=cfg["daily_cooldown_h"]) - (now - last)
                await interaction.response.send_message(embed=themed_embed("Daily Cooldown", f"Daily on cooldown: {left}", success=False), ephemeral=True)
                return
        self.bot.db.change_balance(interaction.guild_id, interaction.user.id, cfg["daily_amount"])
        self.bot.db.set_cooldown(interaction.guild_id, interaction.user.id, "daily_at", now.isoformat())
        await interaction.response.send_message(embed=themed_embed("Daily Claimed", f"You claimed +{cfg['daily_amount']}"))

    @economy.command(name="work")
    async def work(self, interaction: discord.Interaction):
        cfg = self.bot.db.get_guild_config(interaction.guild_id)["economy_settings"]
        cd = self.bot.db.get_cooldowns(interaction.guild_id, interaction.user.id)
        now = datetime.now(timezone.utc)
        if cd["work_at"]:
            last = datetime.fromisoformat(cd["work_at"])
            if now - last < timedelta(minutes=cfg["work_cooldown_m"]):
                left = timedelta(minutes=cfg["work_cooldown_m"]) - (now - last)
                await interaction.response.send_message(embed=themed_embed("Work Cooldown", f"Work on cooldown: {left}", success=False), ephemeral=True)
                return
        gain = random.randint(cfg["work_min"], cfg["work_max"])
        self.bot.db.change_balance(interaction.guild_id, interaction.user.id, gain)
        self.bot.db.set_cooldown(interaction.guild_id, interaction.user.id, "work_at", now.isoformat())
        await interaction.response.send_message(embed=themed_embed("Work Complete", f"Work payout: +{gain}"))

    @economy.command(name="pay")
    async def pay(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount <= 0:
            await interaction.response.send_message(embed=themed_embed("Transfer Error", "Amount must be positive.", success=False), ephemeral=True)
            return
        cfg = self.bot.db.get_guild_config(interaction.guild_id)["economy_settings"]
        if amount > cfg["transfer_max"]:
            await interaction.response.send_message(embed=themed_embed("Transfer Error", "Over transfer max limit.", success=False), ephemeral=True)
            return
        bal = self.bot.db.get_balance(interaction.guild_id, interaction.user.id)
        if bal < amount:
            await interaction.response.send_message(embed=themed_embed("Transfer Error", "Insufficient funds.", success=False), ephemeral=True)
            return
        tax = int(amount * (cfg.get("transfer_tax_percent", 0) / 100))
        recv = amount - tax
        self.bot.db.change_balance(interaction.guild_id, interaction.user.id, -amount)
        self.bot.db.change_balance(interaction.guild_id, user.id, recv)
        await interaction.response.send_message(embed=themed_embed("Transfer Complete", f"Paid {user.mention} {recv} (tax {tax})"))

    @economy.command(name="leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        rows = self.bot.db.top_balances(interaction.guild_id)
        lines = [f"{i+1}. <@{r['user_id']}> - {r['balance']}" for i, r in enumerate(rows)]
        await interaction.response.send_message(embed=themed_embed("Economy Leaderboard", "\n".join(lines) or "No data"))

    @economy.command(name="shop")
    async def shop(self, interaction: discord.Interaction):
        rows = self.bot.db.list_shop_items(interaction.guild_id)
        await interaction.response.send_message(embed=themed_embed("Economy Shop", "\n".join([f"#{r['id']} {r['name']} - {r['price']}" for r in rows]) or "Shop empty"))

    @economy.command(name="buy")
    async def buy(self, interaction: discord.Interaction, item_id: int):
        row = self.bot.db._exec("SELECT * FROM economy_shop_items WHERE guild_id=? AND id=?", (interaction.guild_id, item_id)).fetchone()
        if not row:
            await interaction.response.send_message(embed=themed_embed("Shop Error", "Item not found.", success=False), ephemeral=True)
            return
        bal = self.bot.db.get_balance(interaction.guild_id, interaction.user.id)
        if bal < row["price"]:
            await interaction.response.send_message(embed=themed_embed("Transfer Error", "Insufficient funds.", success=False), ephemeral=True)
            return
        self.bot.db.change_balance(interaction.guild_id, interaction.user.id, -row["price"])
        self.bot.db.add_inventory(interaction.guild_id, interaction.user.id, item_id, 1)
        await interaction.response.send_message(embed=themed_embed("Purchase Complete", f"Purchased {row['name']}"))

    @economy.command(name="inventory")
    async def inventory(self, interaction: discord.Interaction):
        rows = self.bot.db.list_inventory(interaction.guild_id, interaction.user.id)
        await interaction.response.send_message(embed=themed_embed("Inventory", "\n".join([f"{r['name']} x{r['qty']}" for r in rows]) or "Inventory empty"))

    @economy.command(name="admin")
    async def admin(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=themed_embed("Economy Admin", "Use button below to add shop items."), view=EconomyAdminView(self, interaction.guild_id), ephemeral=True)


async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
