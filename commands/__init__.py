from commands.moderation import setup_moderation_commands
from commands.economy import setup_economy_commands
from commands.tickets import setup_tickets_commands
from commands.admin_panel import setup_admin_panel_commands
from commands.fun import setup_fun_commands
from commands.utility import setup_utility_commands
from commands.information import setup_information_commands
from commands.profile import setup_profile_commands
from commands.custom_commands import setup_custom_commands
from commands.private_voice import setup_private_voice
from commands.voice import setup_voice_commands
from commands.swakazu import setup_swakazu_commands

def setup_commands(bot):
    """Регистрация всех команд"""
    setup_moderation_commands(bot)
    setup_economy_commands(bot)
    setup_tickets_commands(bot)
    setup_admin_panel_commands(bot)
    setup_fun_commands(bot)
    setup_utility_commands(bot)
    setup_information_commands(bot)
    setup_profile_commands(bot)
    setup_custom_commands(bot)
    setup_private_voice(bot)
    setup_voice_commands(bot)
    print("✅ Все команды загружены!")
