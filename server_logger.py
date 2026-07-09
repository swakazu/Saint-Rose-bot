import discord
from discord.ext import commands
from datetime import datetime
from config import LOG_CHANNEL_ID
from logger import send_log

class ServerLogger(commands.Cog):
    """Отслеживает события на сервере"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        await send_log(
            self.bot,
            f"✅ **Система логирования активирована!**\nБот {self.bot.user} готов.",
            discord.Color.green()
        )
    
    # ========== УЧАСТНИКИ ==========
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(
            title="👋 Новый участник",
            description=f"{member.mention} присоединился!",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="📅 Аккаунт создан", value=member.created_at.strftime("%d.%m.%Y %H:%M"), inline=True)
        embed.add_field(name="👤 ID", value=member.id, inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Всего участников: {member.guild.member_count}")
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(
            title="🚪 Участник покинул сервер",
            description=f"{member.mention} вышел",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 ID", value=member.id, inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Всего участников: {member.guild.member_count}")
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
    
    # ========== РОЛИ ==========
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        changes = []
        
        if before.nick != after.nick:
            changes.append(f"✏️ Никнейм: `{before.nick or 'Нет'}` → `{after.nick or 'Нет'}`")
        
        old_roles = set(before.roles)
        new_roles = set(after.roles)
        
        added = new_roles - old_roles
        removed = old_roles - new_roles
        
        if added:
            roles_str = ", ".join([f"`{r.name}`" for r in added if r.name != "@everyone"])
            if roles_str:
                changes.append(f"✅ Добавлены: {roles_str}")
        
        if removed:
            roles_str = ", ".join([f"`{r.name}`" for r in removed if r.name != "@everyone"])
            if roles_str:
                changes.append(f"❌ Удалены: {roles_str}")
        
        if changes:
            embed = discord.Embed(
                title="🔄 Участник обновлён",
                description=f"{after.mention}",
                color=discord.Color.purple(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Изменения", value="\n".join(changes[:5]), inline=False)
            embed.set_thumbnail(url=after.display_avatar.url)
            
            channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)
    
    # ========== БАНЫ ==========
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(
            title="🔨 Участник забанен",
            description=f"**Пользователь:** {user.mention}\n**ID:** {user.id}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Всего участников: {guild.member_count}")
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = discord.Embed(
            title="✅ Участник разбанен",
            description=f"**Пользователь:** {user.mention}\n**ID:** {user.id}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
    
    # ========== СООБЩЕНИЯ ==========
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        
        embed = discord.Embed(
            title="✏️ Сообщение отредактировано",
            description=f"**Автор:** {before.author.mention}\n**Канал:** {before.channel.mention}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="До", value=before.content[:1000] or "Пусто", inline=False)
        embed.add_field(name="После", value=after.content[:1000] or "Пусто", inline=False)
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        
        embed = discord.Embed(
            title="🗑️ Сообщение удалено",
            description=f"**Автор:** {message.author.mention}\n**Канал:** {message.channel.mention}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Содержание", value=message.content[:1000] or "Пусто", inline=False)
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
    
    # ========== ГОЛОСОВЫЕ КАНАЛЫ ==========
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel and before.channel != after.channel:
            embed = discord.Embed(
                title="🔊 Заход в голосовой",
                description=f"{member.mention} зашёл в {after.channel.mention}",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Участников: {len(after.channel.members)}")
            
            channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)
        
        elif before.channel and before.channel != after.channel:
            embed = discord.Embed(
                title="🔇 Выход из голосового",
                description=f"{member.mention} вышел из {before.channel.mention}",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Осталось: {len(before.channel.members)}")
            
            channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)

async def setup_server_logger(bot):
    await bot.add_cog(ServerLogger(bot))
    print("✅ Логирование сервера активировано!")
