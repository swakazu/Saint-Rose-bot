import asyncio
import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1510638426016448602

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ПРЯМОЕ ОПРЕДЕЛЕНИЕ КОМАНДЫ (без импорта)
class CreateRoomButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🎤 Создать приватную комнату", style=discord.ButtonStyle.success, emoji="🎤")
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Тест: кнопка работает!", ephemeral=True)

class CreateRoomView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreateRoomButton())

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущен!")
    
    guild = bot.get_guild(GUILD_ID)
    if guild:
        print(f"📡 Сервер найден: {guild.name}")
        
        # Регистрируем команду
        @bot.tree.command(name="приватные_комнаты", description="Создать панель приватных комнат", guild=discord.Object(id=GUILD_ID))
        async def private_rooms_panel(interaction: discord.Interaction):
            embed = discord.Embed(
                title="🎤 Приватные комнаты",
                description="Нажми на кнопку!",
                color=discord.Color.purple()
            )
            view = CreateRoomView()
            await interaction.response.send_message(embed=embed, view=view)
        
        # Синхронизация
        await bot.tree.sync(guild=guild)
        print("✅ Команды синхронизированы!")
        
        # Проверяем
        commands_list = await bot.tree.fetch_commands(guild=guild)
        print(f"📋 Зарегистрировано команд: {len(commands_list)}")
        for cmd in commands_list:
            print(f"  - /{cmd.name}")
    else:
        print("❌ Сервер не найден!")
    
    await bot.close()

asyncio.run(bot.start(TOKEN))
