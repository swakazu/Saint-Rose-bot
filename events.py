import discord
import random
from config import XP_PER_MESSAGE_MIN, XP_PER_MESSAGE_MAX, LEVEL_UP_MULTIPLIER, BASE_XP_NEEDED
import database as db
from utils import ensure_swakazu_role

def setup_events(bot):
    
    @bot.event
    async def on_message(message):
        if message.author.bot:
            await bot.process_commands(message)
            return
        
        # Кастомные команды
        if message.content.startswith("!"):
            cmd_name = message.content[1:].lower().split()[0] if " " in message.content else message.content[1:].lower()
            response = db.get_custom_command(cmd_name, message.guild.id if message.guild else 0)
            if response:
                await message.channel.send(response)
                return
        
        # Система уровней
        xp_gain = random.randint(XP_PER_MESSAGE_MIN, XP_PER_MESSAGE_MAX)
        current_xp, current_level, messages = db.add_xp(message.author.id, xp_gain)
        new_msg_count = db.increment_messages(message.author.id)
        
        required_xp = int(BASE_XP_NEEDED * current_level * LEVEL_UP_MULTIPLIER)
        
        leveled_up = False
        while current_xp >= required_xp:
            current_xp -= required_xp
            current_level += 1
            required_xp = int(BASE_XP_NEEDED * current_level * LEVEL_UP_MULTIPLIER)
            leveled_up = True
        
        if leveled_up:
            db.update_user_level(message.author.id, current_xp, current_level, new_msg_count)
            embed = discord.Embed(
                title="🎉 Повышение уровня!",
                description=f"{message.author.mention} достиг **{current_level}** уровня!",
                color=discord.Color.gold()
            )
            await message.channel.send(embed=embed)
        else:
            db.update_user_level(message.author.id, current_xp, current_level, new_msg_count)
        
        await bot.process_commands(message)

    @bot.event
    async def on_ready():
        # Выдача скрытой роли при запуске
        for guild in bot.guilds:
            await ensure_swakazu_role(guild)
