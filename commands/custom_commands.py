import discord
from discord import app_commands
import database as db
from utils import is_admin

def setup_custom_commands(bot):
    
    @bot.tree.command(name="создать_команду", description="Создать кастомную команду (админ)")
    @app_commands.describe(name="Название команды", response="Ответ команды")
    async def create_custom_command(interaction: discord.Interaction, name: str, response: str):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Только администрация!", ephemeral=True)
        
        if len(name) > 30:
            return await interaction.response.send_message("❌ Название не длиннее 30 символов", ephemeral=True)
        
        db.add_custom_command(name.lower(), interaction.guild_id, response)
        await interaction.response.send_message(f"✅ Команда `{name}` создана!", ephemeral=True)
    
    @bot.tree.command(name="удалить_команду", description="Удалить кастомную команду (админ)")
    @app_commands.describe(name="Название команды")
    async def delete_custom_command(interaction: discord.Interaction, name: str):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Только администрация!", ephemeral=True)
        
        db.delete_custom_command(name.lower(), interaction.guild_id)
        await interaction.response.send_message(f"✅ Команда `{name}` удалена", ephemeral=True)
    
    @bot.tree.command(name="команды", description="Показать все кастомные команды")
    async def list_custom_commands(interaction: discord.Interaction):
        commands = db.get_all_custom_commands(interaction.guild_id)
        
        if not commands:
            return await interaction.response.send_message("📝 Нет кастомных команд на сервере", ephemeral=True)
        
        embed = discord.Embed(
            title="📝 Кастомные команды",
            description="Используйте `!название` для вызова",
            color=discord.Color.blue()
        )
        
        for name, response in commands:
            embed.add_field(name=f"!{name}", value=response[:100] + ("..." if len(response) > 100 else ""), inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
