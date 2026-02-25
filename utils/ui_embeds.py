from __future__ import annotations

import discord

PANEL_BANNER = "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1200&q=60"


def themed_embed(title: str, description: str, *, success: bool = True) -> discord.Embed:
    color = 0x2ECC71 if success else 0xE74C3C
    e = discord.Embed(title=title, description=description, color=color)
    e.set_author(name="mr_tyleromgplay")
    e.set_image(url=PANEL_BANNER)
    e.set_footer(text="Tropica Configuration Panel | Powered by Tropical Systems")
    return e


def config_home_embed(module_states: dict[str, bool]) -> discord.Embed:
    checks = {True: "✅", False: "✖"}
    lines = [
        "Welcome to Tropica",
        "",
        "Thank you for choosing **Tropica** – your personal slice of paradise.",
        "This config is where you shape **Tropica's** vibe, tune all features,",
        "and make **Tropica** feel just right for your server!",
        "",
        "**Current Set Up**",
        f"• 🧰 Default Settings: {checks[module_states.get('default', True)]}",
        f"• ⚠️ Infraction Module: {checks[module_states.get('infractions', True)]}",
        f"• ⭐ Review Module: {checks[module_states.get('appeals', True)]}",
        f"• 🛒 Orders Module: {checks[module_states.get('economy', True)]}",
        f"• 🛡️ Staff Management Module: {checks[module_states.get('staff', True)]}",
        f"• 🎮 API Actions Module: {checks[module_states.get('api', True)]}",
        f"• 📊 Session Module: {checks[module_states.get('sessions', True)]}",
    ]
    e = themed_embed("Tropica Config", "\n".join(lines), success=True)
    return e
