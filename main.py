import asyncio
import discord
from discord.ext import commands
import os
import traceback
from aiohttp import web

from config import TOKEN, GUILD_ID, BOT_NAME, logger
import database as db
from events import setup_events
from commands import setup_commands
from server_logger import setup_server_logger

# Создание папки для логов
os.makedirs("logs", exist_ok=True)

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.moderation = True

# Создание бота с дополнительными настройками
bot = commands.Bot(
    command_prefix="!", 
    intents=intents,
    max_messages=1000  # Ограничиваем кэш
)

# Регистрация событий и команд
setup_events(bot)
setup_commands(bot)


# ========== ВЕБ-СЕРВЕР ДЛЯ ПИНГА ==========
async def health_check(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    print("✅ Веб-сервер запущен на порту 10000")


# ========== ФОНОВЫЕ ЗАДАЧИ ==========
async def background_tasks():
    await bot.wait_until_ready()
    from utils import check_reminders
    await check_reminders(bot)


# ========== СОБЫТИЯ БОТА ==========
@bot.event
async def on_ready():
    print(f"✅ {BOT_NAME} запущен!")
    print(f"📡 Подключён как: {bot.user}")
    print(f"🌐 Серверов: {len(bot.guilds)}")
    
    await setup_server_logger(bot)
    
    guild = bot.get_guild(GUILD_ID)
    if guild:
        try:
            await bot.tree.sync(guild=guild)
            print(f"✓ Команды синхронизированы для сервера {guild.name}")
            commands_list = await bot.tree.fetch_commands(guild=guild)
            print(f"📋 Зарегистрировано команд: {len(commands_list)}")
        except Exception as e:
            print(f"⚠️ Ошибка синхронизации: {e}")
    else:
        print(f"⚠️ Сервер с ID {GUILD_ID} не найден")
    
    try:
        await bot.tree.sync()
        print("✓ Глобальная синхронизация выполнена")
    except:
        pass


# ========== ЗАПУСК ==========
async def main():
    """Главная асинхронная функция"""
    await start_web_server()
    
    # 👇 ВАЖНО: задержка перед подключением к Discord
    print("⏳ Ожидание 10 секунд перед подключением...")
    await asyncio.sleep(10)
    
    async with bot:
        bot.loop.create_task(background_tasks())
        try:
            # 👇 Добавляем повторные попытки
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await bot.start(TOKEN)
                    break
                except discord.errors.HTTPException as e:
                    if "429" in str(e):
                        print(f"⚠️ Попытка {attempt + 1}/{max_retries} не удалась. Ожидание 30 секунд...")
                        await asyncio.sleep(30)
                        if attempt == max_retries - 1:
                            raise
                    else:
                        raise
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            print(traceback.format_exc())
            raise e


if __name__ == "__main__":
    asyncio.run(main())
