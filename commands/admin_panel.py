import discord
from discord import app_commands
from datetime import datetime, timedelta

from utils import is_admin, can_moderate
import database as db



class MuteModal(discord.ui.Modal, title="🔇 Мьют участника"):
    member_id = discord.ui.TextInput(label="ID участника", placeholder="Введите ID пользователя", required=True)
    minutes = discord.ui.TextInput(label="Минуты", placeholder="На сколько минут замьютить", required=True)
    reason = discord.ui.TextInput(label="Причина", placeholder="Причина мьюта", required=False, default="Не указана")
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            member = await interaction.guild.fetch_member(int(self.member_id.value))
            minutes = int(self.minutes.value)
        except:
            return await interaction.response.send_message("❌ Неверный ID или количество минут", ephemeral=True)
        
        if not can_moderate(interaction.user, member):
            return await interaction.response.send_message("❌ Нельзя замутить вышестоящего!", ephemeral=True)
        
        await member.timeout(timedelta(minutes=minutes), reason=self.reason.value)
        await interaction.response.send_message(f"✅ {member.mention} замьючен на {minutes} мин. Причина: {self.reason.value}", ephemeral=True)

class WarnModal(discord.ui.Modal, title="⚠️ Предупреждение"):
    member_id = discord.ui.TextInput(label="ID участника", placeholder="Введите ID пользователя", required=True)
    reason = discord.ui.TextInput(label="Причина", placeholder="Причина предупреждения", required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            member = await interaction.guild.fetch_member(int(self.member_id.value))
        except:
            return await interaction.response.send_message("❌ Неверный ID", ephemeral=True)
        
        if not can_moderate(interaction.user, member):
            return await interaction.response.send_message("❌ Нельзя выдать предупреждение вышестоящему!", ephemeral=True)
        
        db.add_warning(member.id, interaction.guild_id, interaction.user.id, self.reason.value)
        await interaction.response.send_message(f"⚠️ {member.mention} получил предупреждение. Причина: {self.reason.value}", ephemeral=True)

class GiveCookieModal(discord.ui.Modal, title="🍪 Дать печеньку"):
    member_id = discord.ui.TextInput(label="ID участника", placeholder="Введите ID пользователя", required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            member = await interaction.guild.fetch_member(int(self.member_id.value))
        except:
            return await interaction.response.send_message("❌ Неверный ID", ephemeral=True)
        
        db.add_cookie(member.id)
        await interaction.response.send_message(f"🍪 {interaction.user.mention} дал печеньку {member.mention}!", ephemeral=True)

class SayModal(discord.ui.Modal, title="💬 Отправить сообщение"):
    channel_id = discord.ui.TextInput(label="ID канала", placeholder="Введите ID канала", required=True)
    message = discord.ui.TextInput(label="Текст сообщения", placeholder="Что отправить?", style=discord.TextStyle.paragraph, required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel = await interaction.guild.fetch_channel(int(self.channel_id.value))
        except:
            return await interaction.response.send_message("❌ Неверный ID канала", ephemeral=True)
        
        await channel.send(self.message.value)
        await interaction.response.send_message(f"✅ Сообщение отправлено в {channel.mention}", ephemeral=True)

class AnnounceModal(discord.ui.Modal, title="📢 Создать объявление"):
    title = discord.ui.TextInput(label="Заголовок", placeholder="Заголовок объявления", required=True)
    description = discord.ui.TextInput(label="Описание", placeholder="Текст объявления", style=discord.TextStyle.paragraph, required=True)
    color = discord.ui.TextInput(label="Цвет", placeholder="red/green/blue/yellow", required=False, default="blue")
    
    async def on_submit(self, interaction: discord.Interaction):
        colors = {"red": 0xFF0000, "green": 0x00FF00, "blue": 0x3498db, "yellow": 0xFFD700}
        embed = discord.Embed(
            title=self.title.value,
            description=self.description.value,
            color=colors.get(self.color.value, 0x3498db)
        )
        embed.set_footer(text=f"Объявление от {interaction.guild.name}")
        embed.timestamp = datetime.now()
        
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Объявление отправлено!", ephemeral=True)



class AdminPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🛡️ Модерация", style=discord.ButtonStyle.primary, custom_id="admin_panel_moderation")
    async def moderation_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не администратор!", ephemeral=True)
        
        embed = discord.Embed(
            title="🛡️ Панель модерации Saint-Rose",
            description="Выберите действие:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=ModerationPanelView())
    
    @discord.ui.button(label="💰 Экономика", style=discord.ButtonStyle.success, custom_id="admin_panel_economy")
    async def economy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не администратор!", ephemeral=True)
        
        embed = discord.Embed(
            title="💰 Панель экономики",
            description="Управление печеньками и уровнем:",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=EconomyPanelView())
    
    @discord.ui.button(label="📢 Коммуникация", style=discord.ButtonStyle.secondary, custom_id="admin_panel_communication")
    async def communication_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не администратор!", ephemeral=True)
        
        embed = discord.Embed(
            title="📢 Панель коммуникации",
            description="Отправка сообщений и объявлений:",
            color=discord.Color.purple()
        )
        await interaction.response.edit_message(embed=embed, view=CommunicationPanelView())
    
    @discord.ui.button(label="❌ Закрыть панель", style=discord.ButtonStyle.danger, custom_id="admin_panel_close")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Ты не администратор!", ephemeral=True)
        
        await interaction.response.edit_message(content="Панель закрыта.", embed=None, view=None)


class ModerationPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🔇 Мьют", style=discord.ButtonStyle.danger, custom_id="mod_mute")
    async def mute_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MuteModal())
    
    @discord.ui.button(label="⚠️ Предупреждение", style=discord.ButtonStyle.danger, custom_id="mod_warn")
    async def warn_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WarnModal())
    
    @discord.ui.button(label="🍪 Дать печеньку", style=discord.ButtonStyle.success, custom_id="mod_give_cookie")
    async def give_cookie_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GiveCookieModal())
    
    @discord.ui.button(label="💬 Say", style=discord.ButtonStyle.primary, custom_id="mod_say")
    async def say_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SayModal())
    
    @discord.ui.button(label="📢 Announce", style=discord.ButtonStyle.success, custom_id="mod_announce")
    async def announce_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AnnounceModal())
    
    @discord.ui.button(label="◀️ Назад", style=discord.ButtonStyle.secondary, custom_id="mod_back")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👑 Админ-панель Saint-Rose",
            description="Выберите категорию:",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=AdminPanelView())


class EconomyPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🍪 Дать печеньку", style=discord.ButtonStyle.success, custom_id="eco_give")
    async def give_cookie_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GiveCookieModal())
    
    @discord.ui.button(label="🏆 Топ печенек", style=discord.ButtonStyle.primary, custom_id="eco_top")
    async def top_cookie_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        top = db.get_cookie_leaderboard(10)
        if not top:
            return await interaction.response.send_message("Никто ещё не получал печеньки...", ephemeral=True)
        
        embed = discord.Embed(title="🍪 Топ печенек", color=discord.Color.gold())
        for i, (uid, cookies) in enumerate(top, 1):
            member = interaction.guild.get_member(uid)
            name = member.display_name if member else f"Пользователь {uid}"
            embed.add_field(name=f"#{i}", value=f"{name} — {cookies} 🍪", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="◀️ Назад", style=discord.ButtonStyle.secondary, custom_id="eco_back")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👑 Админ-панель Saint-Rose",
            description="Выберите категорию:",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=AdminPanelView())


class CommunicationPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="💬 Say", style=discord.ButtonStyle.primary, custom_id="comm_say")
    async def say_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SayModal())
    
    @discord.ui.button(label="📢 Announce", style=discord.ButtonStyle.success, custom_id="comm_announce")
    async def announce_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AnnounceModal())
    
    @discord.ui.button(label="◀️ Назад", style=discord.ButtonStyle.secondary, custom_id="comm_back")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👑 Админ-панель Saint-Rose",
            description="Выберите категорию:",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=AdminPanelView())


def setup_admin_panel_commands(bot):
    
    @bot.tree.command(name="admin_panel", description="Открыть админ-панель с кнопками")
    async def admin_panel(interaction: discord.Interaction):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Только администрация может использовать эту панель!", ephemeral=True)
        
        embed = discord.Embed(
            title="👑 Админ-панель Saint-Rose",
            description="Выберите категорию для управления:\n\n"
                       "🛡️ **Модерация** — мьют, предупреждения\n"
                       "💰 **Экономика** — выдача печенек, топ\n"
                       "📢 **Коммуникация** — say, announce",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Используйте кнопки для навигации")
        
        await interaction.response.send_message(embed=embed, view=AdminPanelView())