# bot_profile.py
import discord
from discord.ext import commands
from discord import app_commands
from config import DISCORD_LINK, TELEGRAM_LINK, SERVER_IP, SERVER_PORT


class ProfileButtonsView(discord.ui.View):
    """Кнопки для профиля бота"""
    def __init__(self):
        super().__init__(timeout=None)
        
        # Кнопка Discord
        self.add_item(discord.ui.Button(
            label="Discord",
            style=discord.ButtonStyle.link,
            url=DISCORD_LINK,
            emoji="💬"
        ))
        
        # Кнопка Telegram
        self.add_item(discord.ui.Button(
            label="Telegram",
            style=discord.ButtonStyle.link,
            url=TELEGRAM_LINK,
            emoji="📱"
        ))


async def setup_bot_profile(bot):
    """Настраивает профиль бота с информацией о сервере"""
    
    @bot.tree.command(name="профиль_бота", description="Показать информацию о сервере")
    async def bot_profile(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 Играет в",
            description=f"**SR**\n\n"
                       f"**SaintRose**\n"
                       f"Connect `{SERVER_IP}:{SERVER_PORT}`\n"
                       f"`{datetime.now().strftime('%H:%M:%S')}`\n\n"
                       f"**[Discord]({DISCORD_LINK})**\n"
                       f"**[Telegram]({TELEGRAM_LINK})**",
            color=discord.Color.green()
        )
        embed.set_footer(text="Нажми на кнопки ниже")
        
        view = ProfileButtonsView()
        await interaction.response.send_message(embed=embed, view=view)
