from commands.moderation import setup_moderation_commands
from commands.economy_upgraded import setup_economy_commands
from commands.tickets import setup_tickets_commands
from commands.admin_panel import setup_admin_panel_commands
from commands.fun import setup_fun_commands
from commands.utility import setup_utility_commands
from commands.information import setup_information_commands
from commands.profile import setup_profile_commands
from commands.custom_commands import setup_custom_commands
from commands.private_voice import setup_private_voice

def setup_commands(bot):
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