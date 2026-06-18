# logger.py
import discord
from config import LOG_CHANNEL_ID

async def send_log(bot, message: str, color: discord.Color = discord.Color.blue()):
    """
    Отправляет сообщение в указанный канал для логов.
    """
    if bot is None:
        print("❌ Бот не передан в функцию send_log.")
        return

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        print(f"❌ Канал с ID {LOG_CHANNEL_ID} не найден! Проверьте config.py")
        return

    # Создаем Embed для красивого отображения
    embed = discord.Embed(
        description=message,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="Логи сервера Saint-Rose")

    try:
        await channel.send(embed=embed)
    except Exception as e:
        print(f"❌ Не удалось отправить лог в канал: {e}")
