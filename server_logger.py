# server_logger.py
import discord
from discord.ext import commands
from datetime import datetime
import asyncio

from config import LOG_CHANNEL_ID
from logger import send_log


class ServerLogger(commands.Cog):
    """Отслеживает все события на сервере и логирует их в канал"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        await send_log(
            self.bot,
            f"✅ **Система логирования сервера активирована!**\nБот {self.bot.user} готов отслеживать события.",
            discord.Color.green()
        )
    
    # ========== УЧАСТНИКИ ==========
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Вход участника на сервер"""
        embed = discord.Embed(
            title="👋 Новый участник",
            description=f"{member.mention} присоединился к серверу!",
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
        """Выход участника с сервера (или кик)"""
        # Проверяем, был ли участник кикнут
        try:
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    # Это был кик!
                    embed = discord.Embed(
                        title="👢 Участник кикнут",
                        description=f"**Пользователь:** {member.mention}\n**ID:** {member.id}",
                        color=discord.Color.orange(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(name="👮 Модератор", value=entry.user.mention, inline=True)
                    embed.add_field(name="📝 Причина", value=entry.reason or "Не указана", inline=True)
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.set_footer(text=f"Всего участников: {member.guild.member_count}")
                    
                    channel = self.bot.get_channel(LOG_CHANNEL_ID)
                    if channel:
                        await channel.send(embed=embed)
                    return
        except:
            pass
        
        # Если это не кик — обычный выход
        embed = discord.Embed(
            title="🚪 Участник покинул сервер",
            description=f"{member.mention} вышел с сервера",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 ID", value=member.id, inline=True)
        embed.add_field(name="📅 Присоединился", value=member.joined_at.strftime("%d.%m.%Y %H:%M") if member.joined_at else "Неизвестно", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Всего участников: {member.guild.member_count}")
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        """Обновление профиля пользователя (имя, ник, аватар)"""
        changes = []
        
        if before.name != after.name:
            changes.append(f"📝 Имя: `{before.name}` → `{after.name}`")
        if before.discriminator != after.discriminator and before.discriminator != "0":
            changes.append(f"🔢 Тег: `{before.discriminator}` → `{after.discriminator}`")
        if before.display_avatar.url != after.display_avatar.url:
            changes.append("🖼️ Аватар изменён")
        if before.global_name != after.global_name:
            changes.append(f"🌐 Глобальное имя: `{before.global_name}` → `{after.global_name}`")
        
        if changes:
            embed = discord.Embed(
                title="📝 Профиль пользователя обновлён",
                description=f"Пользователь: {after.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Изменения", value="\n".join(changes[:5]), inline=False)
            
            channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)
    
    # ========== РОЛИ ==========
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Обновление участника (роли, никнейм, тайм-аут)"""
        changes = []
        
        # Проверяем изменение никнейма
        if before.nick != after.nick:
            changes.append(f"✏️ Никнейм: `{before.nick or 'Нет'}` → `{after.nick or 'Нет'}`")
        
        # Проверяем изменение ролей
        old_roles = set(before.roles)
        new_roles = set(after.roles)
        
        added_roles = new_roles - old_roles
        removed_roles = old_roles - new_roles
        
        if added_roles:
            roles_str = ", ".join([f"`{role.name}`" for role in added_roles if role.name != "@everyone"])
            if roles_str:
                changes.append(f"✅ Добавлены роли: {roles_str}")
        
        if removed_roles:
            roles_str = ", ".join([f"`{role.name}`" for role in removed_roles if role.name != "@everyone"])
            if roles_str:
                changes.append(f"❌ Удалены роли: {roles_str}")
        
        # Проверяем изменение тайм-аута (мьюта)
        if before.timed_out_until != after.timed_out_until:
            # Если был наложен тайм-аут
            if after.timed_out_until and not before.timed_out_until:
                duration = after.timed_out_until - datetime.now()
                minutes = int(duration.total_seconds() // 60)
                hours = int(duration.total_seconds() // 3600)
                
                if hours >= 24:
                    time_str = f"{hours // 24}д {hours % 24}ч"
                elif hours >= 1:
                    time_str = f"{hours}ч {minutes % 60}мин"
                else:
                    time_str = f"{minutes}мин"
                
                embed = discord.Embed(
                    title="🔇 Тайм-аут (мьют) наложен",
                    description=f"**Участник:** {after.mention}\n**Длительность:** {time_str}",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                embed.set_thumbnail(url=after.display_avatar.url)
                
                # Ищем причину из аудита
                try:
                    async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                        if entry.target.id == after.id:
                            embed.add_field(name="👮 Модератор", value=entry.user.mention, inline=True)
                            if entry.reason:
                                embed.add_field(name="📝 Причина", value=entry.reason, inline=True)
                            break
                except:
                    pass
                
                channel = self.bot.get_channel(LOG_CHANNEL_ID)
                if channel:
                    await channel.send(embed=embed)
            
            # Если тайм-аут снят
            elif before.timed_out_until and not after.timed_out_until:
                embed = discord.Embed(
                    title="✅ Тайм-аут (мьют) снят",
                    description=f"**Участник:** {after.mention}",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.set_thumbnail(url=after.display_avatar.url)
                
                channel = self.bot.get_channel(LOG_CHANNEL_ID)
                if channel:
                    await channel.send(embed=embed)
        
        # Если были изменения (роли, ник) — логируем их отдельно
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
        """Бан участника"""
        embed = discord.Embed(
            title="🔨 Участник забанен",
            description=f"**Пользователь:** {user.mention}\n**ID:** {user.id}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Всего участников: {guild.member_count}")
        
        # Пытаемся найти причину из аудита
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    embed.add_field(name="👮 Модератор", value=entry.user.mention, inline=True)
                    embed.add_field(name="📝 Причина", value=entry.reason or "Не указана", inline=True)
                    break
        except:
            pass
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Разбан участника"""
        embed = discord.Embed(
            title="✅ Участник разбанен",
            description=f"**Пользователь:** {user.mention}\n**ID:** {user.id}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Пытаемся найти модератора из аудита
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
                if entry.target.id == user.id:
                    embed.add_field(name="👮 Модератор", value=entry.user.mention, inline=True)
                    break
        except:
            pass
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
    
    # ========== СООБЩЕНИЯ ==========
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Редактирование сообщения"""
        if before.author.bot:
            return
        
        if before.content == after.content:
            return
        
        embed = discord.Embed(
            title="✏️ Сообщение отредактировано",
            description=f"**Автор:** {before.author.mention}\n**Канал:** {before.channel.mention}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="До", value=before.content[:1000] or "Пусто", inline=False)
        embed.add_field(name="После", value=after.content[:1000] or "Пусто", inline=False)
        embed.set_footer(text=f"ID: {before.id}")
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Удаление сообщения"""
        if message.author.bot:
            return
        
        embed = discord.Embed(
            title="🗑️ Сообщение удалено",
            description=f"**Автор:** {message.author.mention}\n**Канал:** {message.channel.mention}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Содержание", value=message.content[:1000] or "Пусто/Вложение", inline=False)
        embed.set_footer(text=f"ID: {message.id}")
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        """Массовое удаление сообщений (очистка)"""
        if not messages:
            return
        
        channel = messages[0].channel
        count = len(messages)
        
        embed = discord.Embed(
            title="🗑️ Массовое удаление сообщений",
            description=f"**Канал:** {channel.mention}\n**Удалено:** {count} сообщений",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
    
    # ========== ГОЛОСОВЫЕ КАНАЛЫ ==========
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Изменение голосового статуса"""
        # Заход в голосовой канал
        if after.channel and before.channel != after.channel:
            embed = discord.Embed(
                title="🔊 Заход в голосовой канал",
                description=f"{member.mention} зашёл в {after.channel.mention}",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Участников в канале: {len(after.channel.members)}")
            
            channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)
        
        # Выход из голосового канала
        elif before.channel and before.channel != after.channel:
            embed = discord.Embed(
                title="🔇 Выход из голосового канала",
                description=f"{member.mention} вышел из {before.channel.mention}",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Осталось: {len(before.channel.members)} участников")
            
            channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)
        
        # Перемещение между каналами
        elif before.channel and after.channel and before.channel != after.channel:
            embed = discord.Embed(
                title="🔄 Перемещение в голосовом канале",
                description=f"{member.mention} переместился\n**Из:** {before.channel.mention}\n**В:** {after.channel.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)
        
        # Изменение статуса (микрофон/наушники)
        if before.self_mute != after.self_mute:
            status = "🔇 выключил" if after.self_mute else "🎤 включил"
            embed = discord.Embed(
                title=f"🎙️ {member.display_name} {status} микрофон",
                color=discord.Color.blue() if not after.self_mute else discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)
        
        if before.self_deaf != after.self_deaf:
            status = "🔇 выключил" if after.self_deaf else "🔊 включил"
            embed = discord.Embed(
                title=f"🔊 {member.display_name} {status} звук",
                color=discord.Color.blue() if not after.self_deaf else discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)
    
    # ========== КАНАЛЫ ==========
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Создание нового канала"""
        embed = discord.Embed(
            title="➕ Канал создан",
            description=f"**Название:** {channel.mention}\n**Тип:** {channel.type}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"ID: {channel.id}")
        
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Удаление канала"""
        embed = discord.Embed(
            title="➖ Канал удалён",
            description=f"**Название:** {channel.name}\n**Тип:** {channel.type}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"ID: {channel.id}")
        
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Обновление канала (переименование, изменение прав)"""
        changes = []
        
        if before.name != after.name:
            changes.append(f"📝 Название: `{before.name}` → `{after.name}`")
        if before.position != after.position:
            changes.append(f"🔄 Позиция: `{before.position}` → `{after.position}`")
        if before.category != after.category:
            changes.append(f"📂 Категория: `{before.category}` → `{after.category}`")
        if before.topic != after.topic and hasattr(before, 'topic'):
            changes.append(f"📝 Тема: `{before.topic}` → `{after.topic}`")
        
        if changes:
            embed = discord.Embed(
                title="✏️ Канал обновлён",
                description=f"{after.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Изменения", value="\n".join(changes[:5]), inline=False)
            
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
    
    # ========== РОЛИ (глобальные) ==========
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Создание новой роли"""
        embed = discord.Embed(
            title="➕ Роль создана",
            description=f"**Название:** {role.mention}\n**Цвет:** {role.color}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Отображается отдельно", value="Да" if role.hoist else "Нет", inline=True)
        embed.add_field(name="Упоминаема", value="Да" if role.mentionable else "Нет", inline=True)
        embed.set_footer(text=f"ID: {role.id}")
        
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Удаление роли"""
        embed = discord.Embed(
            title="➖ Роль удалена",
            description=f"**Название:** {role.name}\n**Цвет:** {role.color}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"ID: {role.id}")
        
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """Обновление роли"""
        changes = []
        
        if before.name != after.name:
            changes.append(f"📝 Название: `{before.name}` → `{after.name}`")
        if before.color != after.color:
            changes.append(f"🎨 Цвет: `{before.color}` → `{after.color}`")
        if before.hoist != after.hoist:
            changes.append(f"📌 Отдельное отображение: `{before.hoist}` → `{after.hoist}`")
        if before.mentionable != after.mentionable:
            changes.append(f"🔊 Упоминаемость: `{before.mentionable}` → `{after.mentionable}`")
        
        if changes:
            embed = discord.Embed(
                title="✏️ Роль обновлена",
                description=f"{after.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Изменения", value="\n".join(changes[:5]), inline=False)
            
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
    
    # ========== СЕРВЕР ==========
    
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """Обновление сервера"""
        changes = []
        
        if before.name != after.name:
            changes.append(f"📝 Название: `{before.name}` → `{after.name}`")
        if before.region != after.region:
            changes.append(f"🌍 Регион: `{before.region}` → `{after.region}`")
        if before.afk_timeout != after.afk_timeout:
            changes.append(f"⏰ AFK таймаут: `{before.afk_timeout}` → `{after.afk_timeout}`")
        if before.icon != after.icon:
            changes.append("🖼️ Иконка сервера изменена")
        if before.banner != after.banner:
            changes.append("🖼️ Баннер сервера изменён")
        
        if changes:
            embed = discord.Embed(
                title="✏️ Сервер обновлён",
                description=f"**{after.name}**",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Изменения", value="\n".join(changes[:5]), inline=False)
            
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
    
    # ========== ЛОГИРОВАНИЕ ПРЕДУПРЕЖДЕНИЙ ==========
    
    async def log_warning(self, moderator, member, reason):
        """Логирует предупреждение в канал"""
        embed = discord.Embed(
            title="⚠️ Предупреждение выдано",
            description=f"**Участник:** {member.mention}\n**ID:** {member.id}",
            color=discord.Color.yellow(),
            timestamp=datetime.now()
        )
        embed.add_field(name="👮 Модератор", value=moderator.mention, inline=True)
        embed.add_field(name="📝 Причина", value=reason or "Не указана", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)


async def setup_server_logger(bot):
    """Добавляет логгер в бота"""
    await bot.add_cog(ServerLogger(bot))
    print("✅ Логирование сервера активировано!")
