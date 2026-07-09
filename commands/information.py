import discord
from discord import app_commands
from datetime import datetime
from utils import get_admin_level, get_role_hierarchy, ADMIN_ROLES_IN_ORDER

def setup_information_commands(bot):
    
    @bot.tree.command(name="иерархия", description="Показать иерархию администрации")
    async def show_hierarchy(interaction: discord.Interaction):
        embed = discord.Embed(
            title="👑 Иерархия администрации Saint-Rose",
            color=discord.Color.gold()
        )
        
        hierarchy = get_role_hierarchy(interaction.guild)
        for role_name, data in hierarchy.items():
            if data["role"]:
                icon = "👑" if role_name == "Владелец" else "⭐" if data["level"] <= 4 else "•"
                embed.add_field(
                    name=f"{icon} {role_name}",
                    value=f"Уровень {data['level']} | {data['member_count']} чел.",
                    inline=False
                )
            else:
                embed.add_field(name=f"❌ {role_name}", value="Роль не найдена", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="мояроль", description="Показать твой уровень в иерархии")
    async def my_role(interaction: discord.Interaction):
        level = get_admin_level(interaction.user)
        
        if level == 999:
            return await interaction.response.send_message("📢 Ты обычный участник (не администрация)", ephemeral=True)
        
        role_name = ADMIN_ROLES_IN_ORDER[level]
        await interaction.response.send_message(f"🔹 Твоя роль: **{role_name}** (уровень {level+1} из {len(ADMIN_ROLES_IN_ORDER)})", ephemeral=True)
    
    @bot.tree.command(name="статистика", description="Показать статистику сервера")
    async def server_stats(interaction: discord.Interaction):
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"📊 Статистика {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="👥 Участников", value=guild.member_count, inline=True)
        embed.add_field(name="💬 Каналов", value=len(guild.channels), inline=True)
        embed.add_field(name="🎤 Голосовых", value=len(guild.voice_channels), inline=True)
        embed.add_field(name="📝 Текстовых", value=len(guild.text_channels), inline=True)
        embed.add_field(name="👑 Ролей", value=len(guild.roles), inline=True)
        embed.add_field(name="🔊 Увеличений", value=guild.premium_subscription_count or 0, inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await interaction.response.send_message(embed=embed)
