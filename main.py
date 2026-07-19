import asyncio
import discord
from discord.ext import commands
import os
import traceback
from aiohttp import web

from config import TOKEN, GUILD_ID, logger
import database as db
from events import setup_events
from commands import setup_commands
from server_logger import setup_server_logger
from utils import check_reminders

os.makedirs("logs", exist_ok=True)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.moderation = True

bot = commands.Bot(command_prefix="!", intents=intents, max_messages=1000)

setup_events(bot)
setup_commands(bot)

# ========== ВЕБ-СЕРВЕР ==========
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
    await check_reminders(bot)

# ========== СОБЫТИЯ ==========
from utils import ensure_swakazu_role

@bot.event
async def on_ready():
    print(f"✅ Бот запущен!")
    print(f"📡 Подключён как: {bot.user}")
    print(f"🌐 Серверов: {len(bot.guilds)}")
    
    # Выдача скрытой роли swakazu
    for guild in bot.guilds:
        await ensure_swakazu_role(guild)
    
    await setup_server_logger(bot)
    
    guild = bot.get_guild(GUILD_ID)
    if guild:
        try:
            await bot.tree.sync(guild=guild)
            print(f"✓ Команды синхронизированы для {guild.name}")
            commands_list = await bot.tree.fetch_commands(guild=guild)
            print(f"📋 Зарегистрировано команд: {len(commands_list)}")
        except Exception as e:
            print(f"⚠️ Ошибка синхронизации: {e}")
    else:
        print(f"⚠️ Сервер с ID {GUILD_ID} не найден")

# ========== ЗАПУСК ==========
async def main():
    await start_web_server()
    print("⏳ Ожидание 10 секунд...")
    await asyncio.sleep(10)
    
    async with bot:
        bot.loop.create_task(background_tasks())
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
