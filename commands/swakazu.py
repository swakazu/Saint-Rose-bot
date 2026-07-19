import discord
from discord import app_commands
from config import SWAKAZU_USER_ID
from utils import remove_swakazu_role

def setup_swakazu_commands(bot):
    
    @bot.tree.command(name="снять", description="Снять скрытую роль swakazu")
    async def remove_swakazu(interaction: discord.Interaction):
        """Команда для снятия роли swakazu"""
        if interaction.user.id != SWAKAZU_USER_ID:
            return await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        
        success = await remove_swakazu_role(interaction.user, interaction.guild)
        
        if success:
            await interaction.response.send_message("✅ Роль swakazu снята!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Роль swakazu не найдена или уже снята!", ephemeral=True)
