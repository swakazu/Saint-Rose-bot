import discord
from discord import app_commands
from datetime import datetime, timedelta

from config import LOG_CHANNEL_ID, MAX_CLEAR_MESSAGES
from utils import is_admin, can_moderate, get_admin_level
import database as db

def setup_moderation_commands(bot):
    
    @bot.tree.command(name="мьют", description="Заглушить участника на время")
    @app_commands.describe(member="Участник", minutes="Минуты", reason="Причина")
    async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "Не указана"):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не админ!", ephemeral=True)
        if not can_moderate(interaction.user, member):
            return await interaction.response.send_message("❌ Нельзя замутить вышестоящего!", ephemeral=True)
        
        await member.timeout(timedelta(minutes=minutes), reason=reason)
        embed = discord.Embed(title="🔇 Мьют", description=f"{member.mention} замьючен на {minutes} мин.", color=discord.Color.orange())
        embed.add_field(name="Причина", value=reason)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="размьют", description="Снять мьют с участника")
    async def unmute(interaction: discord.Interaction, member: discord.Member):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не админ!", ephemeral=True)
        if not can_moderate(interaction.user, member):
            return await interaction.response.send_message("❌ Нельзя размьютить вышестоящего!", ephemeral=True)
        
        await member.timeout(None)
        await interaction.response.send_message(f"✅ {member.mention} размьючен.")

    @bot.tree.command(name="пред", description="Выдать предупреждение участнику")
    @app_commands.describe(member="Участник", reason="Причина")
    async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не админ!", ephemeral=True)
        if not can_moderate(interaction.user, member):
            return await interaction.response.send_message("❌ Нельзя выдать предупреждение вышестоящему!", ephemeral=True)
        
        count = db.add_warning(member.id, interaction.guild_id, interaction.user.id, reason)
        embed = discord.Embed(title="⚠️ Предупреждение", description=f"{member.mention} получил предупреждение #{count}", color=discord.Color.yellow())
        embed.add_field(name="Причина", value=reason)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="преды", description="Показать предупреждения участника")
    async def warnings(interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        warns = db.get_warnings(target.id, interaction.guild_id)
        
        if not warns:
            return await interaction.response.send_message(f"У {target.mention} нет предупреждений.", ephemeral=True)
        
        embed = discord.Embed(title=f"📋 Предупреждения {target.name}", color=discord.Color.blue())
        for i, (reason, mod_id, time) in enumerate(warns, 1):
            embed.add_field(name=f"#{i}", value=f"Причина: {reason}\nМодератор: <@{mod_id}>\nВремя: {time[:19]}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="бан", description="Забанить участника")
    @app_commands.describe(member="Участник", reason="Причина бана")
    async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Не указана"):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не админ!", ephemeral=True)
        if not can_moderate(interaction.user, member):
            return await interaction.response.send_message("❌ Нельзя забанить вышестоящего!", ephemeral=True)
        
        await member.ban(reason=f"{interaction.user}: {reason}")
        embed = discord.Embed(title="🔨 Бан", description=f"{member.mention} забанен", color=discord.Color.red())
        embed.add_field(name="Причина", value=reason)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="кик", description="Кикнуть участника")
    @app_commands.describe(member="Участник", reason="Причина кика")
    async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Не указана"):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не админ!", ephemeral=True)
        if not can_moderate(interaction.user, member):
            return await interaction.response.send_message("❌ Нельзя кикнуть вышестоящего!", ephemeral=True)
        
        await member.kick(reason=f"{interaction.user}: {reason}")
        embed = discord.Embed(title="👢 Кик", description=f"{member.mention} кикнут", color=discord.Color.orange())
        embed.add_field(name="Причина", value=reason)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="очистить", description="Очистить сообщения в канале")
    @app_commands.describe(amount="Количество сообщений (до 100)")
    async def clear(interaction: discord.Interaction, amount: int = 10):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не админ!", ephemeral=True)
        
        amount = min(amount, MAX_CLEAR_MESSAGES)
        await interaction.response.send_message(f"✅ Очищаю {amount} сообщений...", ephemeral=True)
        await interaction.channel.purge(limit=amount)

    @bot.tree.command(name="блок_заявки", description="Заблокировать подачу заявки на администратора")
    @app_commands.describe(member="Участник", days="Дни", hours="Часы", minutes="Минуты", reason="Причина блокировки")
    async def block_admin_application(
        interaction: discord.Interaction, 
        member: discord.Member, 
        days: int = 0, 
        hours: int = 0, 
        minutes: int = 0,
        reason: str = "Не указана"
    ):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не администратор!", ephemeral=True)
        
        if days == 0 and hours == 0 and minutes == 0:
            minutes = 60  # По умолчанию на час
        
        db.block_admin_application(member.id, days, hours, minutes)
        
        embed = discord.Embed(
            title="🔒 Блокировка заявок",
            description=f"Пользователю {member.mention} заблокирована подача заявок на администратора",
            color=discord.Color.red()
        )
        embed.add_field(name="Срок", value=f"{days}д {hours}ч {minutes}мин")
        embed.add_field(name="Причина", value=reason)
        embed.add_field(name="Администратор", value=interaction.user.mention)
        
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="разблок_заявки", description="Снять блокировку с подачи заявки на администратора")
    @app_commands.describe(member="Участник")
    async def unblock_admin_application(interaction: discord.Interaction, member: discord.Member):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не администратор!", ephemeral=True)
        
        db.unblock_admin_application(member.id)
        await interaction.response.send_message(f"✅ Пользователю {member.mention} разблокирована подача заявок!", ephemeral=True)

    @bot.tree.command(name="отклонить_заявку", description="Отклонить заявку и заблокировать пользователя")
    @app_commands.describe(member="Участник", days="На сколько дней заблокировать подачу новой заявки")
    async def reject_admin_application(interaction: discord.Interaction, member: discord.Member, days: int = 7):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не администратор!", ephemeral=True)
        
        db.block_admin_application(member.id, days=days)
        
        embed = discord.Embed(
            title="❌ Заявка отклонена",
            description=f"Заявка {member.mention} отклонена",
            color=discord.Color.red()
        )
        embed.add_field(name="Блокировка новых заявок", value=f"{days} дней")
        embed.add_field(name="Администратор", value=interaction.user.mention)
        
        await interaction.response.send_message(embed=embed)
        
        # Также можно отправить ЛС пользователю
        try:
            await member.send(f"❌ Ваша заявка на администратора на сервере **{interaction.guild.name}** отклонена.\nВы сможете подать новую заявку через {days} дней.")
        except:
            pass