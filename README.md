# Blox Studios All-in-One Bot (discord.py 2.x)

A config-first, production-ready Discord bot with:
- Sessions + staff + infractions + appeals
- Economy system (SQLite)
- ERLC + Maple tools with safe allowlisted game actions
- Premium (Free vs Premium only)
- `/config open` GUI as the control center
- Tropica-style dark panel embeds for config and default responses

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill values:
   - `BOT_TOKEN`
   - `OWNER_IDS` (comma-separated user IDs)
   - optional `ERLC_API_KEY`, `MAPLE_API_KEY`
3. Run:
   ```bash
   python main.py
   ```

## Config-first design
Everything is controlled from:
- `/config open`

Inside that panel, use:
- **Set Any Key** (key/value modal)
- **Set Template JSON** (paste Discohook JSON)
- **Refresh**

### Main config key paths
- Channels:
  - `channels.session_announce_channel`
  - `channels.staff_logs_channel`
  - `channels.infraction_logs_channel`
  - `channels.appeals_channel`
  - `channels.economy_logs_channel`
  - `channels.api_action_logs_channel`
- Permissions (JSON list of role IDs):
  - `permissions.session_host_roles`
  - `permissions.staff_manage_roles`
  - `permissions.infraction_roles`
  - `permissions.appeal_review_roles`
  - `permissions.economy_admin_roles`
  - `permissions.api_action_roles`
  - `permissions.config_admin_roles`
- Toggles:
  - `admins_bypass`
  - `module_enabled.sessions`
  - `module_enabled.staff`
  - `module_enabled.infractions`
  - `module_enabled.appeals`
  - `module_enabled.api`
  - `module_enabled.economy`
- Variables:
  - `variables.server_name`, `variables.department_name`, `variables.currency_name`, etc.
- API:
  - `provider_mode` (`erlc`, `maple`, `both`)
  - `api_actions_enabled`
  - `require_action_confirmation`
  - `log_all_actions`
  - `allowed_actions` (JSON list)
- Webhooks (Premium):
  - `webhook.name`
  - `webhook.avatar_url`
  - `webhook.module_sessions`
  - `webhook.module_staff`
  - `webhook.module_economy`
- Economy:
  - `economy.currency_name`
  - `economy.starting_balance`
  - `economy.daily_amount`
  - `economy.work_min`
  - `economy.work_max`
  - `economy.daily_cooldown_h`
  - `economy.work_cooldown_m`
  - `economy.transfer_max`
  - `economy.transfer_tax_percent`

## Commands (simple)
### Config
- `/config open`

### Sessions
- `/session start`
- `/session end`
- `/session announce`
- `/session info`

### Staff
- `/staff promote <user>`
- `/staff demote <user>`
- `/staff history <user>`

### Infractions
- `/infraction issue <user>`
- `/infraction view <case_id>`
- `/infraction history <user>`

### Appeals
- `/appeal submit`
- `/appeal view <appeal_id>`
- `/appeal list`

### Economy
- `/economy balance`
- `/economy daily`
- `/economy work`
- `/economy pay <user> <amount>`
- `/economy leaderboard`
- `/economy shop`
- `/economy buy <item_id>`
- `/economy inventory`
- `/economy admin`

### ERLC / Maple / Game Actions
- `/erlc status`
- `/erlc players`
- `/maple status`
- `/maple players`
- `/game status`
- `/game players`
- `/game actions`
- `/game run <action> [provider]`

### Owner prefix commands
- `.GrantPremium <guild_id> <duration>`
- `.RevokePremium <guild_id>`
- `.PremiumStatus <guild_id>`
- `.OwnerStats`

## Premium
Only two states:
- Free
- Premium (with expiry timestamp)

Premium is granted by owner via dot commands and enables advanced webhook identity/customization features.

## Database notes
SQLite file: `data/bot.db`

Tables:
- `guild_config`
- `guild_variables`
- `guild_permissions`
- `embed_templates`
- `premium`
- `sessions`
- `staff_events`
- `infractions`
- `appeals`
- `economy_users`
- `economy_shop_items`
- `economy_inventory`
- `api_action_audit`

All data persists through restarts.
