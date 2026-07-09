import discord
from config import LOG_CHANNEL_ID

async def send_log(bot, message, color=discord.Color.blue()):
    """Отправляет лог в канал"""
    if bot is None:
        print("❌ Бот не передан в функцию send_log")
        return
    
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        print(f"❌ Канал с ID {LOG_CHANNEL_ID} не найден")
        return
    
    embed = discord.Embed(
        description=message,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="Логи сервера Saint-Rose")
    
    try:
        await channel.send(embed=embed)
    except Exception as e:
        print(f"❌ Не удалось отправить лог: {e}")
