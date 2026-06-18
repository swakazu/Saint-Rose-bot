import discord
from discord.ext import commands
import asyncio
import os
import traceback

from config import TOKEN, GUILD_ID, BOT_NAME, logger
import database as db
from events import setup_events
from commands import setup_commands
from server_logger import setup_server_logger  # 👈 ДОБАВЛЕНО

# Создание папки для логов если её нет
os.makedirs("logs", exist_ok=True)

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.moderation = True  # 👈 ДОБАВЛЕНО для отслеживания банов

# Создание бота
bot = commands.Bot(command_prefix="!", intents=intents)

# Регистрация событий
setup_events(bot)

# Регистрация команд
setup_commands(bot)

async def background_tasks():
    """Фоновая задача для проверки напоминаний"""
    await bot.wait_until_ready()
    from utils import check_reminders
    await check_reminders(bot)

@bot.event
async def on_ready():
    print(f"✅ {BOT_NAME} запущен!")
    print(f"📡 Подключён как: {bot.user}")
    print(f"🌐 Серверов: {len(bot.guilds)}")
    
    # 👇 АКТИВАЦИЯ ЛОГГЕРА
    await setup_server_logger(bot)
    
    guild = bot.get_guild(GUILD_ID)
    if guild:
        try:
            # Синхронизация команд для конкретного сервера
            await bot.tree.sync(guild=guild)
            print(f"✓ Команды синхронизированы для сервера {guild.name}")
            
            # Показываем все команды
            commands_list = await bot.tree.fetch_commands(guild=guild)
            print(f"📋 Зарегистрировано команд: {len(commands_list)}")
            for cmd in commands_list:
                print(f"  - /{cmd.name}")
        except Exception as e:
            print(f"⚠️ Ошибка синхронизации: {e}")
    else:
        print(f"⚠️ Сервер с ID {GUILD_ID} не найден")
    
    # Также синхронизируем глобально
    try:
        await bot.tree.sync()
        print("✓ Глобальная синхронизация выполнена")
    except:
        pass

async def main():
    """Главная асинхронная функция"""
    async with bot:
        bot.loop.create_task(background_tasks())
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            print(traceback.format_exc())
            raise e

if __name__ == "__main__":
    asyncio.run(main())
