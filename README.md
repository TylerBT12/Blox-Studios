# Blox Studios Discord Bot

Production-structured Discord bot with slash-first architecture, premium licensing, dashboard, moderation, appeals, sessions, staff management, and owner-only global panel.

## Features
- Slash commands for public features
- Prefix (`.`) commands only for Global Owner Panel
- Modular cogs with persistent JSON storage
- Auto file creation for all data stores
- Premium per-guild with expiry / unlimited, tiers, and license redeem
- Dashboard auto-refresh background loop
- Moderation (warnings, infractions, cases) with logging
- Appeals with staff review buttons
- Session and staff analytics
- Configurable permissions/channels/embeds
- Command menu system with category/search/all views (owner commands visible to owner)

## Quick start
1. Create `config.json` from template (auto-created on first run).
2. Fill `token` and `owner_ids`.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run:
   ```bash
   python bot.py
   ```

## Folder layout
- `bot.py` bootstrap and cog loading
- `core/` storage, premium, embeds, config
- `cogs/` feature modules
- `data/` persistent JSON databases
