import discord
from discord import app_commands
import aiohttp
import random

def setup_fun_commands(bot):
    
    @bot.tree.command(name="лисы", description="Случайная картинка с лисой")
    async def fox(interaction: discord.Interaction):
        if random.random() < 0.3:
            return await interaction.response.send_message("🦊 Лиса убежала... попробуй ещё раз!")
        
        async with aiohttp.ClientSession() as session:
            async with session.get("https://randomfox.ca/floof/") as resp:
                data = await resp.json()
                await interaction.response.send_message(data.get("image", "https://randomfox.ca/images/1.jpg"))

    @bot.tree.command(name="пёс", description="Случайная картинка с собакой")
    async def dog(interaction: discord.Interaction):
        if random.random() < 0.3:
            return await interaction.response.send_message("🐕 Пёс гуляет... зайди позже!")
        
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as resp:
                data = await resp.json()
                await interaction.response.send_message(data.get("message", "https://images.dog.ceo/breeds/hound-afghan/n02088094_1003.jpg"))

    @bot.tree.command(name="шар", description="Магический шар предскажет будущее")
    @app_commands.describe(question="Твой вопрос")
    async def eight_ball(interaction: discord.Interaction, question: str):
        answers = ["✅ Да", "❌ Нет", "🤔 Возможно", "🌟 Определённо да", "💫 Спроси позже", "🔮 Звёзды говорят — да", "🌙 Лучше не сейчас"]
        await interaction.response.send_message(f"**Вопрос:** {question}\n**Ответ:** {random.choice(answers)}")