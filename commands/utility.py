import discord
from discord import app_commands
from datetime import datetime, timedelta
from utils import is_admin
import database as db

def setup_utility_commands(bot):
    
    @bot.tree.command(name="напомни", description="Установить напоминание")
    @app_commands.describe(minutes="Через сколько минут", text="Что напомнить")
    async def remind(interaction: discord.Interaction, minutes: int, text: str):
        if minutes < 1 or minutes > 1440:
            return await interaction.response.send_message("❌ От 1 до 1440 минут", ephemeral=True)
        
        remind_time = datetime.now() + timedelta(minutes=minutes)
        db.add_reminder(interaction.user.id, interaction.channel_id, text, remind_time)
        await interaction.response.send_message(f"⏰ Напомню через {minutes} минут: **{text}**", ephemeral=True)
    
    @bot.tree.command(name="say", description="Отправить сообщение от имени бота")
    @app_commands.describe(channel="Канал", message="Текст сообщения")
    async def say(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не админ!", ephemeral=True)
        
        await channel.send(message)
        await interaction.response.send_message(f"✅ Сообщение отправлено в {channel.mention}", ephemeral=True)
    
    @bot.tree.command(name="announce", description="Создать объявление")
    @app_commands.describe(title="Заголовок", description="Текст объявления", color="Цвет (red/green/blue/yellow)")
    async def announce(interaction: discord.Interaction, title: str, description: str, color: str = "blue"):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не админ!", ephemeral=True)
        
        colors = {
            "red": discord.Color.red(),
            "green": discord.Color.green(),
            "blue": discord.Color.blue(),
            "yellow": discord.Color.yellow()
        }
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=colors.get(color, discord.Color.blue())
        )
        embed.set_footer(text=f"Объявление от {interaction.guild.name}")
        embed.timestamp = datetime.now()
        
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Объявление отправлено!", ephemeral=True)
