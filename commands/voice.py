# commands/voice.py
import discord
from discord import app_commands
from discord.ext import commands

def setup_voice_commands(bot):
    """Настройка голосовых команд"""
    
    @bot.tree.command(name="join", description="Подключить бота к голосовому каналу")
    @app_commands.describe(channel="ID голосового канала")
    async def join_voice(interaction: discord.Interaction, channel: str):
        # Проверяем, что пользователь админ
        from utils import is_admin
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ Ты не админ!", ephemeral=True)
            return
        
        # Пытаемся найти канал по ID
        try:
            channel_id = int(channel)
            voice_channel = interaction.guild.get_channel(channel_id)
            
            if not voice_channel:
                await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
                return
            
            if not isinstance(voice_channel, discord.VoiceChannel):
                await interaction.response.send_message("❌ Это не голосовой канал!", ephemeral=True)
                return
            
        except ValueError:
            await interaction.response.send_message("❌ Неверный ID канала!", ephemeral=True)
            return
        
        # Проверяем, не находится ли бот уже в голосовом канале
        if interaction.guild.voice_client:
            # Если бот уже в голосовом канале, перемещаем его
            await interaction.guild.voice_client.move_to(voice_channel)
        else:
            # Подключаем бота к голосовому каналу
            await voice_channel.connect()
        
        # Отвечаем без лишнего текста (можно даже ничего не отправлять)
        await interaction.response.send_message("✅", ephemeral=True)
