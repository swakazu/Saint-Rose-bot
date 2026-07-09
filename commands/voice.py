import discord
from discord import app_commands
from utils import is_admin

def setup_voice_commands(bot):
    
    @bot.tree.command(name="join", description="Подключить бота к голосовому каналу")
    @app_commands.describe(channel="ID голосового канала")
    async def join_voice(interaction: discord.Interaction, channel: str):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не админ!", ephemeral=True)
        
        try:
            channel_id = int(channel)
            voice_channel = interaction.guild.get_channel(channel_id)
            
            if not voice_channel:
                return await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
            
            if not isinstance(voice_channel, discord.VoiceChannel):
                return await interaction.response.send_message("❌ Это не голосовой канал!", ephemeral=True)
            
        except ValueError:
            return await interaction.response.send_message("❌ Неверный ID канала!", ephemeral=True)
        
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect()
        
        await interaction.response.send_message("✅", ephemeral=True)
