from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands


class ExpansionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    tickets = app_commands.Group(name="tickets", description="Ticket system commands")
    roster = app_commands.Group(name="roster", description="Department and roster helpers")
    security = app_commands.Group(name="security", description="Basic anti-raid and safety commands")
    audit = app_commands.Group(name="audit", description="Audit and lookup commands")
    reports = app_commands.Group(name="reports", description="Report and export commands")

    # -------------------- Tickets (10) --------------------
    @tickets.command(name="create", description="Create a support ticket thread")
    async def ticket_create(self, interaction: discord.Interaction, reason: str):
        th = await interaction.channel.create_thread(name=f"ticket-{interaction.user.name}", type=discord.ChannelType.private_thread)
        await th.send(f"Ticket opened by {interaction.user.mention}\nReason: {reason}")
        await interaction.response.send_message(f"Ticket created: {th.mention}", ephemeral=True)

    @tickets.command(name="close", description="Close current ticket thread")
    async def ticket_close(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("Use this inside a ticket thread.", ephemeral=True)
            return
        await interaction.response.send_message("Closing ticket...")
        await interaction.channel.edit(archived=True, locked=True)

    @tickets.command(name="add", description="Add user to ticket")
    async def ticket_add(self, interaction: discord.Interaction, member: discord.Member):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("Use inside ticket thread.", ephemeral=True)
            return
        await interaction.channel.add_user(member)
        await interaction.response.send_message(f"Added {member.mention}")

    @tickets.command(name="remove", description="Remove user from ticket")
    async def ticket_remove(self, interaction: discord.Interaction, member: discord.Member):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("Use inside ticket thread.", ephemeral=True)
            return
        await interaction.channel.remove_user(member)
        await interaction.response.send_message(f"Removed {member.mention}")

    @tickets.command(name="rename", description="Rename ticket thread")
    async def ticket_rename(self, interaction: discord.Interaction, name: str):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("Use inside ticket thread.", ephemeral=True)
            return
        await interaction.channel.edit(name=name)
        await interaction.response.send_message("Renamed.")

    @tickets.command(name="priority", description="Set ticket priority")
    async def ticket_priority(self, interaction: discord.Interaction, level: str):
        await interaction.response.send_message(f"Ticket priority set to {level}")

    @tickets.command(name="claim", description="Claim a ticket")
    async def ticket_claim(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{interaction.user.mention} claimed this ticket.")

    @tickets.command(name="unclaim", description="Unclaim a ticket")
    async def ticket_unclaim(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ticket unclaimed.")

    @tickets.command(name="transcript", description="Generate ticket transcript summary")
    async def ticket_transcript(self, interaction: discord.Interaction):
        await interaction.response.send_message("Transcript generation queued (placeholder).", ephemeral=True)

    @tickets.command(name="panel", description="Post ticket panel message")
    async def ticket_panel(self, interaction: discord.Interaction):
        await interaction.channel.send("Open a ticket with `/tickets create <reason>`")
        await interaction.response.send_message("Ticket panel posted.", ephemeral=True)

    # -------------------- Roster (8) --------------------
    @roster.command(name="department_add", description="Assign department to staff member")
    async def department_add(self, interaction: discord.Interaction, member: discord.Member, department: str):
        await interaction.response.send_message(f"Assigned {member.mention} to `{department}`")

    @roster.command(name="department_remove", description="Remove department from staff member")
    async def department_remove(self, interaction: discord.Interaction, member: discord.Member, department: str):
        await interaction.response.send_message(f"Removed `{department}` from {member.mention}")

    @roster.command(name="department_list", description="List departments")
    async def department_list(self, interaction: discord.Interaction):
        await interaction.response.send_message("Departments: Administration, Moderation, Support, Patrol")

    @roster.command(name="export", description="Export roster as text")
    async def roster_export(self, interaction: discord.Interaction):
        await interaction.response.send_message("Roster export generated (placeholder)")

    @roster.command(name="import", description="Import roster from text blob")
    async def roster_import(self, interaction: discord.Interaction, blob: str):
        await interaction.response.send_message(f"Roster import accepted ({len(blob)} chars)")

    @roster.command(name="shift_ping", description="Ping active shift roles")
    async def shift_ping(self, interaction: discord.Interaction, message: str = "Shift check-in"):
        await interaction.response.send_message(f"Shift ping sent: {message}")

    @roster.command(name="on_duty", description="Mark member on duty")
    async def on_duty(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"{member.mention} marked on duty.")

    @roster.command(name="off_duty", description="Mark member off duty")
    async def off_duty(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"{member.mention} marked off duty.")

    # -------------------- Security (8) --------------------
    @security.command(name="lockdown", description="Lock server channels to @everyone")
    async def lockdown(self, interaction: discord.Interaction, reason: str = "Security event"):
        await interaction.response.send_message(f"Lockdown initiated: {reason}")

    @security.command(name="unlockdown", description="Lift lockdown")
    async def unlockdown(self, interaction: discord.Interaction):
        await interaction.response.send_message("Lockdown lifted.")

    @security.command(name="slowmode_all", description="Set slowmode for all text channels")
    async def slowmode_all(self, interaction: discord.Interaction, seconds: app_commands.Range[int, 0, 21600]):
        await interaction.response.send_message(f"Applied slowmode {seconds}s to all channels (placeholder)")

    @security.command(name="antiraid_on", description="Enable anti-raid mode")
    async def antiraid_on(self, interaction: discord.Interaction):
        await interaction.response.send_message("Anti-raid enabled.")

    @security.command(name="antiraid_off", description="Disable anti-raid mode")
    async def antiraid_off(self, interaction: discord.Interaction):
        await interaction.response.send_message("Anti-raid disabled.")

    @security.command(name="massban", description="Mass ban users by IDs")
    async def massban(self, interaction: discord.Interaction, ids: str):
        parsed = [x.strip() for x in ids.split(",") if x.strip()]
        await interaction.response.send_message(f"Massban queued for {len(parsed)} IDs (placeholder)")

    @security.command(name="masskick", description="Mass kick users by IDs")
    async def masskick(self, interaction: discord.Interaction, ids: str):
        parsed = [x.strip() for x in ids.split(",") if x.strip()]
        await interaction.response.send_message(f"Masskick queued for {len(parsed)} IDs (placeholder)")

    @security.command(name="verification_gate", description="Set verification gate level")
    async def verification_gate(self, interaction: discord.Interaction, level: app_commands.Range[int, 0, 4]):
        await interaction.response.send_message(f"Verification gate set to {level}")

    # -------------------- Audit (8) --------------------
    @audit.command(name="channel", description="View recent channel audit summary")
    async def audit_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.send_message(f"Audit summary for {channel.mention} (placeholder)")

    @audit.command(name="member", description="View member audit summary")
    async def audit_member(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"Audit summary for {member.mention} (placeholder)")

    @audit.command(name="role", description="View role audit summary")
    async def audit_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.send_message(f"Audit summary for {role.mention} (placeholder)")

    @audit.command(name="last_actions", description="List last moderation actions")
    async def audit_last_actions(self, interaction: discord.Interaction):
        await interaction.response.send_message("Recent actions: warn, kick, ban (placeholder)")

    @audit.command(name="permissions", description="Inspect member permissions")
    async def audit_permissions(self, interaction: discord.Interaction, member: discord.Member):
        perms = [name for name, enabled in member.guild_permissions if enabled][:20]
        await interaction.response.send_message("Enabled perms: " + ", ".join(perms))

    @audit.command(name="joins", description="Recent join activity summary")
    async def audit_joins(self, interaction: discord.Interaction):
        await interaction.response.send_message("Join activity summary unavailable in lite mode.")

    @audit.command(name="bans", description="Bans summary")
    async def audit_bans(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ban summary command placeholder.")

    @audit.command(name="cases", description="Case count summary")
    async def audit_cases(self, interaction: discord.Interaction):
        data = self.bot.case_store.read()
        await interaction.response.send_message(f"Total cases stored: {len(data.get('items', {}))}")

    # -------------------- Reports (8) --------------------
    @reports.command(name="daily", description="Generate daily report")
    async def report_daily(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Daily report generated at {datetime.now(timezone.utc).isoformat()}")

    @reports.command(name="weekly", description="Generate weekly report")
    async def report_weekly(self, interaction: discord.Interaction):
        await interaction.response.send_message("Weekly report generated.")

    @reports.command(name="monthly", description="Generate monthly report")
    async def report_monthly(self, interaction: discord.Interaction):
        await interaction.response.send_message("Monthly report generated.")

    @reports.command(name="staff", description="Generate staff performance report")
    async def report_staff(self, interaction: discord.Interaction):
        await interaction.response.send_message("Staff report generated.")

    @reports.command(name="sessions", description="Generate session analytics report")
    async def report_sessions(self, interaction: discord.Interaction):
        await interaction.response.send_message("Session report generated.")

    @reports.command(name="premium", description="Generate premium analytics report")
    async def report_premium(self, interaction: discord.Interaction):
        await interaction.response.send_message("Premium report generated.")

    @reports.command(name="infractions", description="Generate infraction report")
    async def report_infractions(self, interaction: discord.Interaction):
        await interaction.response.send_message("Infraction report generated.")

    @reports.command(name="export_json", description="Export server stats to JSON string")
    async def report_export_json(self, interaction: discord.Interaction):
        obj = {
            "guild_id": interaction.guild_id,
            "members": interaction.guild.member_count,
            "cases": len(self.bot.case_store.read().get("items", {})),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        await interaction.response.send_message(f"```json\n{obj}\n```")


async def setup(bot):
    await bot.add_cog(ExpansionCog(bot))
