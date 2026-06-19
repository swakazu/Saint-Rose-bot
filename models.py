import discord
from discord import app_commands
import asyncio
from datetime import datetime, timedelta

from config import LOG_CHANNEL_ID, ADMIN_ROLES_IN_ORDER, COLORS
from utils import is_admin, can_moderate
import database as db


class TicketCloseView(discord.ui.View):
    """Кнопка закрытия тикета с сохранением транскрипта"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🔒 Закрыть тикет", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        messages = []
        async for message in interaction.channel.history(limit=100):
            messages.append(f"{message.author}: {message.content} ({message.created_at})")
        
        transcript = "\n".join(reversed(messages))
        
        with open(f"logs/transcript_{interaction.channel.name}.txt", "w", encoding="utf-8") as f:
            f.write(transcript)
        
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            file = discord.File(f"logs/transcript_{interaction.channel.name}.txt")
            embed = discord.Embed(
                title="📄 Тикет закрыт",
                description=f"Тикет **{interaction.channel.name}** закрыт\nЗакрыл: {interaction.user.mention}",
                color=discord.Color.orange()
            )
            await log_channel.send(embed=embed, file=file)
        
        await interaction.followup.send("Тикет будет закрыт через 5 секунд...")
        await asyncio.sleep(5)
        
        try:
            await interaction.channel.delete()
        except:
            pass


class TicketButtonsView(discord.ui.View):
    """Панель с кнопками для создания тикетов"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="⚠️ Амнистия", style=discord.ButtonStyle.secondary, custom_id="ticket_amnesty")
    async def amnesty_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from commands.tickets import AmnestyModal
        await interaction.response.send_modal(AmnestyModal())
    
    @discord.ui.button(label="!? Предложение", style=discord.ButtonStyle.primary, custom_id="ticket_suggestion")
    async def suggestion_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from commands.tickets import SuggestionModal
        await interaction.response.send_modal(SuggestionModal())
    
    @discord.ui.button(label="😊 Помощь", style=discord.ButtonStyle.success, custom_id="ticket_help")
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from commands.tickets import HelpModal
        await interaction.response.send_modal(HelpModal())
    
    @discord.ui.button(label="🔴 Жалоба на админа", style=discord.ButtonStyle.danger, custom_id="ticket_complaint")
    async def complaint_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from commands.tickets import ComplaintModal
        await interaction.response.send_modal(ComplaintModal())
    
    @discord.ui.button(label="👑 Заявка на админа", style=discord.ButtonStyle.primary, custom_id="ticket_admin_application", row=2)
    async def admin_application_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Проверяем блокировку
        if db.is_admin_application_blocked(interaction.user.id):
            remaining = db.get_admin_application_block_remaining(interaction.user.id)
            return await interaction.response.send_message(
                f"❌ Вы не можете подать заявку на администратора ещё **{remaining}**!\n"
                f"Причина: отклонение предыдущей заявки.",
                ephemeral=True
            )
        
        # --- НОВАЯ ЛОГИКА: Отправляем ссылку на Google Форму ---
        embed = discord.Embed(
            title="📝 Заявка на пост Helper",
            description="Для подачи заявки на должность Helper, пожалуйста, заполните официальную форму.",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        embed.add_field(
            name="🔗 Ссылка на форму",
            value="[Нажмите здесь, чтобы перейти к заполнению заявки](https://forms.gle/PuPzJyyBtZ5ZCSFe8)",
            inline=False
        )
        embed.add_field(
            name="📌 Важно",
            value="• Заявки принимаются от кандидатов от 13 лет (исключения обсуждаются).\n"
                  "• Убедитесь, что вы можете уделять время серверу.\n"
                  "• Заполните форму максимально подробно.",
            inline=False
        )
        embed.set_footer(text="Saint-Rose Project • Заявки на Helper")
        
        # Пытаемся отправить в ЛС
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message("✅ Я отправил вам ссылку на форму в личные сообщения! Проверьте ЛС.", ephemeral=True)
        except discord.Forbidden:
            # Если ЛС закрыты — отправляем в канал (только пользователь видит)
            await interaction.response.send_message(embed=embed, ephemeral=True)


class AmnestyModal(discord.ui.Modal, title="⚠️ Запрос на амнистию"):
    reason = discord.ui.TextInput(
        label="Причина нарушения", 
        placeholder="За что вас наказали?", 
        required=True, 
        max_length=200
    )
    date = discord.ui.TextInput(
        label="Дата нарушения", 
        placeholder="Когда это было?", 
        required=True, 
        max_length=50
    )
    why = discord.ui.TextInput(
        label="Почему стоит амнистировать", 
        placeholder="Объясните причину", 
        style=discord.TextStyle.paragraph, 
        required=True, 
        max_length=500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        from commands.tickets import create_ticket
        await create_ticket(interaction, "амнистия", {
            "Причина нарушения": self.reason.value,
            "Дата нарушения": self.date.value,
            "Почему стоит амнистировать": self.why.value
        })


class SuggestionModal(discord.ui.Modal, title="!? Предложение по улучшению"):
    title = discord.ui.TextInput(
        label="Название предложения", 
        placeholder="Кратко о чём предложение", 
        required=True, 
        max_length=100
    )
    description = discord.ui.TextInput(
        label="Описание", 
        placeholder="Подробно опишите идею", 
        style=discord.TextStyle.paragraph, 
        required=True, 
        max_length=1000
    )
    why = discord.ui.TextInput(
        label="Почему это нужно", 
        placeholder="Как улучшит сервер?", 
        style=discord.TextStyle.paragraph, 
        required=True, 
        max_length=500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        from commands.tickets import create_ticket
        await create_ticket(interaction, "предложение-по-улучшению", {
            "Название": self.title.value,
            "Описание": self.description.value,
            "Почему это нужно": self.why.value
        })


class HelpModal(discord.ui.Modal, title="😊 Проблемы и помощь"):
    problem_type = discord.ui.TextInput(
        label="Тип проблемы", 
        placeholder="Техническая / Конфликт / Вопрос по правилам", 
        required=True, 
        max_length=50
    )
    description = discord.ui.TextInput(
        label="Описание проблемы", 
        placeholder="Что случилось?", 
        style=discord.TextStyle.paragraph, 
        required=True, 
        max_length=1000
    )
    tried = discord.ui.TextInput(
        label="Что уже пробовали", 
        placeholder="Что вы сделали для решения?", 
        required=False, 
        max_length=500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        from commands.tickets import create_ticket
        await create_ticket(interaction, "проблемы-и-помощь", {
            "Тип проблемы": self.problem_type.value,
            "Описание": self.description.value,
            "Что пробовали": self.tried.value or "Не указано"
        })


class ComplaintModal(discord.ui.Modal, title="🔴 Жалоба на администратора"):
    admin_name = discord.ui.TextInput(
        label="Ник администратора", 
        placeholder="На кого жалоба?", 
        required=True, 
        max_length=50
    )
    what_happened = discord.ui.TextInput(
        label="Что произошло", 
        placeholder="Опишите ситуацию", 
        style=discord.TextStyle.paragraph, 
        required=True, 
        max_length=1000
    )
    evidence = discord.ui.TextInput(
        label="Доказательства", 
        placeholder="Ссылки на скрины/видео (если есть)", 
        required=False, 
        max_length=500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        from commands.tickets import create_ticket
        await create_ticket(interaction, "жалоба-на-администратора", {
            "Администратор": self.admin_name.value,
            "Ситуация": self.what_happened.value,
            "Доказательства": self.evidence.value or "Не предоставлены"
        })


class AdminApplicationModal(discord.ui.Modal, title="👑 Заявка на администратора"):
    nickname = discord.ui.TextInput(
        label="Ваш ник",
        placeholder="Введите ваш игровой ник",
        required=True,
        max_length=50
    )
    telegram_id = discord.ui.TextInput(
        label="Ваш Telegram ID",
        placeholder="@username или https://t.me/username",
        required=True,
        max_length=100
    )
    steam_id = discord.ui.TextInput(
        label="Ваш Steam ID",
        placeholder="STEAM_0:X:XXXXXXXX",
        required=True,
        max_length=50
    )
    steam_profile = discord.ui.TextInput(
        label="Профиль в Steam (ссылка)",
        placeholder="https://steamcommunity.com/...",
        required=True,
        max_length=200
    )
    age = discord.ui.TextInput(
        label="Ваш возраст",
        placeholder="Укажите возраст (13+, исключения обсуждаются)",
        required=True,
        max_length=3
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        from commands.tickets import create_ticket
        await create_ticket(interaction, "заявка-на-администратора", {
            "Ник": self.nickname.value,
            "Telegram ID": self.telegram_id.value,
            "Steam ID": self.steam_id.value,
            "Профиль Steam": self.steam_profile.value,
            "Возраст": self.age.value,
            "⚠️ Дополнительные вопросы": "Администратор задаст: время на сервере, опыт администрирования, мотивацию и т.д."
        })
