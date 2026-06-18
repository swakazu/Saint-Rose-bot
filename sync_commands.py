import asyncio
import discord
from discord.ext import commands
from config import TOKEN, GUILD_ID

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущен!")
    
    guild = bot.get_guild(GUILD_ID)
    
    if guild:
        print(f"📡 Синхронизация команд для сервера: {guild.name}")
        
        # Полностью очищаем команды на сервере
        bot.tree.clear_commands(guild=guild)
        
        # Синхронизируем
        await bot.tree.sync(guild=guild)
        
        print("✅ Команды синхронизированы!")
        
        # Показываем какие команды зарегистрированы
        commands_list = await bot.tree.fetch_commands(guild=guild)
        print(f"📋 Зарегистрировано команд: {len(commands_list)}")
        for cmd in commands_list:
            print(f"  - /{cmd.name}")
    else:
        print(f"❌ Сервер {GUILD_ID} не найден")
    
    await bot.close()

asyncio.run(bot.start(TOKEN))