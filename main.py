import discord
from discord.ext import commands
import asyncio
import os
import traceback
from aiohttp import web  # 👈 ДОБАВЛЕНО для веб-сервера

from config import TOKEN, GUILD_ID, BOT_NAME, logger
import database as db
from events import setup_events
from commands import setup_commands
from server_logger import setup_server_logger

# Создание папки для логов если её нет
os.makedirs("logs", exist_ok=True)

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.moderation = True  # для отслеживания банов

# Создание бота
bot = commands.Bot(command_prefix="!", intents=intents)

# Регистрация событий
setup_events(bot)

# Регистрация команд
setup_commands(bot)


# ========== ВЕБ-СЕРВЕР ДЛЯ ПИНГА ==========
async def health_check(request):
    """Простой ответ для проверки работы бота"""
    return web.Response(text="OK")


async def start_web_server():
    """Запускает веб-сервер для Render на порту 10000"""
    app = web.Application()
    app.router.add_get('/', health_check)  # Ответ на GET-запросы по адресу /
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)  # Привязываемся к порту 10000
    await site.start()
    print("✅ Веб-сервер для проверки здоровья запущен на порту 10000")


# ========== ФОНОВЫЕ ЗАДАЧИ ==========
async def background_tasks():
    """Фоновая задача для проверки напоминаний"""
    await bot.wait_until_ready()
    from utils import check_reminders
    await check_reminders(bot)


# ========== СОБЫТИЯ БОТА ==========
# main.py (часть с on_ready)

@bot.event
async def on_ready():
    print(f"✅ {BOT_NAME} запущен!")
    print(f"📡 Подключён как: {bot.user}")
    print(f"🌐 Серверов: {len(bot.guilds)}")
    
    # Устанавливаем статус "Играет в SR"
    await bot.change_presence(
        activity=discord.Game(
            name="🩷Saint-Rose🩷"
        )
    )
    
    # ... остальной код
    
    # Активация логгера
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


# ========== ЗАПУСК ==========
async def main():
    """Главная асинхронная функция"""
    # 👇 ЗАПУСКАЕМ ВЕБ-СЕРВЕР ПЕРЕД БОТОМ
    await start_web_server()
    
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
