# commands/tickets.py
import discord
from discord import app_commands
from datetime import datetime

from config import TICKET_CATEGORY_ID, LOG_CHANNEL_ID, ADMIN_ROLES_IN_ORDER
from utils import is_admin
from models import TicketButtonsView, TicketCloseView

async def create_ticket(interaction: discord.Interaction, ticket_type: str, modal_data: dict):
    """Создание тикета"""
    existing_ticket = None
    for channel in interaction.guild.channels:
        if channel.name == f"{ticket_type}-{interaction.user.id}" and channel.category_id == TICKET_CATEGORY_ID:
            existing_ticket = channel
            break
    
    if existing_ticket:
        return await interaction.response.send_message(f"❌ У тебя уже есть открытый тикет этого типа: {existing_ticket.mention}", ephemeral=True)
    
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
    }
    
    for role_name in ADMIN_ROLES_IN_ORDER:
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    
    category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
    if not category:
        return await interaction.response.send_message("❌ Ошибка: категория для тикетов не найдена!", ephemeral=True)
    
    channel = await interaction.guild.create_text_channel(
        f"{ticket_type}-{interaction.user.id}",
        category=category,
        overwrites=overwrites,
        reason=f"Тикет {ticket_type} от {interaction.user}"
    )
    
    colors = {
        "амнистия": discord.Color.orange(),
        "предложение-по-улучшению": discord.Color.green(),
        "проблемы-и-помощь": discord.Color.blue(),
        "жалоба-на-администратора": discord.Color.red(),
        "заявка-на-администратора": discord.Color.gold()
    }
    
    emojis = {
        "амнистия": "⚠️",
        "предложение-по-улучшению": "💡",
        "проблемы-и-помощь": "😊",
        "жалоба-на-администратора": "🔴",
        "заявка-на-администратора": "👑"
    }
    
    embed = discord.Embed(
        title=f"{emojis.get(ticket_type, '📝')} Тикет: {ticket_type}",
        description=f"**Создал:** {interaction.user.mention}\n**Тип:** {ticket_type}\n**Время:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        color=colors.get(ticket_type, discord.Color.blue())
    )
    
    for key, value in modal_data.items():
        embed.add_field(name=key, value=value[:1024], inline=False)
    
    embed.set_footer(text="Администрация ответит в ближайшее время")
    
    close_view = TicketCloseView()
    await channel.send(embed=embed, view=close_view)
    
    await interaction.response.send_message(f"✅ Тикет **{ticket_type}** создан! Переходи в {channel.mention}", ephemeral=True)


class AmnestyModal(discord.ui.Modal, title="⚠️ Запрос на амнистию"):
    reason_input = discord.ui.TextInput(label="Причина нарушения", placeholder="За что вас наказали?", required=True, max_length=200)
    date_input = discord.ui.TextInput(label="Дата нарушения", placeholder="Когда это было?", required=True, max_length=50)
    why_input = discord.ui.TextInput(label="Почему стоит амнистировать", placeholder="Объясните причину", style=discord.TextStyle.paragraph, required=True, max_length=500)
    
    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "амнистия", {
            "Причина нарушения": self.reason_input.value,
            "Дата нарушения": self.date_input.value,
            "Почему стоит амнистировать": self.why_input.value
        })


class SuggestionModal(discord.ui.Modal, title="💡 Предложение по улучшению"):
    title_input = discord.ui.TextInput(label="Название предложения", placeholder="Кратко о чём предложение", required=True, max_length=100)
    description_input = discord.ui.TextInput(label="Описание", placeholder="Подробно опишите идею", style=discord.TextStyle.paragraph, required=True, max_length=1000)
    why_input = discord.ui.TextInput(label="Почему это нужно", placeholder="Как улучшит сервер?", style=discord.TextStyle.paragraph, required=True, max_length=500)
    
    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "предложение-по-улучшению", {
            "Название": self.title_input.value,
            "Описание": self.description_input.value,
            "Почему это нужно": self.why_input.value
        })


class HelpModal(discord.ui.Modal, title="😊 Проблемы и помощь"):
    problem_type_input = discord.ui.TextInput(label="Тип проблемы", placeholder="Техническая / Конфликт / Вопрос по правилам", required=True, max_length=50)
    description_input = discord.ui.TextInput(label="Описание проблемы", placeholder="Что случилось?", style=discord.TextStyle.paragraph, required=True, max_length=1000)
    tried_input = discord.ui.TextInput(label="Что уже пробовали", placeholder="Что вы сделали для решения?", required=False, max_length=500)
    
    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "проблемы-и-помощь", {
            "Тип проблемы": self.problem_type_input.value,
            "Описание": self.description_input.value,
            "Что пробовали": self.tried_input.value or "Не указано"
        })


class ComplaintModal(discord.ui.Modal, title="🔴 Жалоба на администратора"):
    admin_name_input = discord.ui.TextInput(label="Ник администратора", placeholder="На кого жалоба?", required=True, max_length=50)
    what_happened_input = discord.ui.TextInput(label="Что произошло", placeholder="Опишите ситуацию", style=discord.TextStyle.paragraph, required=True, max_length=1000)
    evidence_input = discord.ui.TextInput(label="Доказательства", placeholder="Ссылки на скрины/видео (если есть)", required=False, max_length=500)
    
    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "жалоба-на-администратора", {
            "Администратор": self.admin_name_input.value,
            "Ситуация": self.what_happened_input.value,
            "Доказательства": self.evidence_input.value or "Не предоставлены"
        })


class AdminApplicationModal(discord.ui.Modal, title="👑 Заявка на администратора"):
    nickname_input = discord.ui.TextInput(label="Ваш ник", placeholder="Введите ваш игровой ник", required=True, max_length=50)
    telegram_id_input = discord.ui.TextInput(label="Ваш Telegram ID", placeholder="@username или https://t.me/username", required=True, max_length=100)
    steam_id_input = discord.ui.TextInput(label="Ваш Steam ID", placeholder="STEAM_0:X:XXXXXXXX", required=True, max_length=50)
    steam_profile_input = discord.ui.TextInput(label="Ваш профиль в Steam (ссылка)", placeholder="https://steamcommunity.com/...", required=True, max_length=200)
    age_input = discord.ui.TextInput(label="Ваш возраст", placeholder="Укажите ваш возраст (13+ исключение)", required=True, max_length=3)
    
    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "заявка-на-администратора", {
            "Ник": self.nickname_input.value,
            "Telegram ID": self.telegram_id_input.value,
            "Steam ID": self.steam_id_input.value,
            "Профиль Steam": self.steam_profile_input.value,
            "Возраст": self.age_input.value,
            "⚠️ Далее ответьте на вопросы в чате": "Ожидайте, администратор задаст вам дополнительные вопросы"
        })


def setup_tickets_commands(bot):
    
    @bot.tree.command(name="setup_tickets", description="Создать панель со всеми типами тикетов")
    async def setup_tickets(interaction: discord.Interaction):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Только администрация!", ephemeral=True)
        
        embed = discord.Embed(
            title="🎫 Центр поддержки Saint-Rose",
            description="**Выберите тип обращения:**\n\n"
                       "• **⚠️ Амнистия** — запрос на разбан или снятие наказания\n"
                       "• **💡 Предложение** — идеи по улучшению сервера\n"
                       "• **😊 Помощь** — любые проблемы и вопросы\n"
                       "• **🔴 Жалоба на админа** — нарушение правил администрацией\n"
                       "• **👑 Заявка на админа** — стать частью команды\n\n"
                       "**Нажмите на кнопку ниже, чтобы создать тикет.**",
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Все обращения рассматриваются администрацией {interaction.guild.name}")
        
        view = TicketButtonsView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Панель тикетов создана!", ephemeral=True)
