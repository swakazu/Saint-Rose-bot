import discord
from discord import app_commands
from datetime import datetime
import database as db
from profile_generator import generate_profile_image

def setup_profile_commands(bot):
    
    @bot.tree.command(name="профиль", description="Показать свой профиль или профиль другого участника")
    @app_commands.describe(member="Участник (опционально)")
    async def profile(interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        await interaction.response.defer(ephemeral=(member is not None))
        
        level_data = db.get_user_level(target.id) or (0, 1, 0)
        xp, level, messages = level_data
        required_xp = int(100 * level * 1.5)
        
        cookies = db.get_cookies(target.id)
        warns = db.get_warning_count(target.id, interaction.guild_id)
        
        top_cookies = db.get_cookie_leaderboard(50)
        rank = None
        top_percent = None
        for i, (uid, _) in enumerate(top_cookies, 1):
            if uid == target.id:
                rank = i
                top_percent = round((i / len(top_cookies)) * 100) if top_cookies else 100
                break
        
        profile_img = await generate_profile_image(
            user=target,
            level=level,
            xp=xp,
            next_xp=required_xp,
            cookies=cookies,
            warns=warns,
            messages=messages,
            join_date=target.joined_at or datetime.now(),
            rank=rank,
            top_percent=top_percent
        )
        
        file = discord.File(profile_img, filename="profile.png")
        
        embed = discord.Embed(
            title=f"📸 Профиль {target.display_name}",
            color=discord.Color.gold()
        )
        embed.set_image(url="attachment://profile.png")
        
        await interaction.followup.send(embed=embed, file=file, ephemeral=(member is not None))
    
    @bot.tree.command(name="топ", description="Показать топ участников")
    @app_commands.describe(by="По какому критерию (levels или cookies)")
    async def leaderboard(interaction: discord.Interaction, by: str = "levels"):
        await interaction.response.defer()
        
        if by.lower() == "cookies":
            top = db.get_cookie_leaderboard(10)
            title = "🍪 Топ печенек"
            value_name = "печенек"
        else:
            top = db.get_level_leaderboard(10)
            title = "📊 Топ уровней"
            value_name = "уровень"
        
        if not top:
            return await interaction.followup.send("📊 Пока нет данных для топа!", ephemeral=True)
        
        embed = discord.Embed(title=title, color=discord.Color.gold())
        
        for i, data in enumerate(top, 1):
            uid = data[0]
            if by.lower() == "cookies":
                val = f"{data[1]} {value_name}"
            else:
                val = f"Уровень {data[1]} (XP: {data[2]})"
            
            member = interaction.guild.get_member(uid)
            if member:
                name = member.display_name
            else:
                name = f"Пользователь {uid}"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            embed.add_field(name=f"{medal} {name}", value=val, inline=False)
        
        embed.set_footer(text=f"Сервер {interaction.guild.name}")
        await interaction.followup.send(embed=embed)
