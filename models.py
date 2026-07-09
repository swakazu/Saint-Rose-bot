import discord
import asyncio
from datetime import datetime
from config import LOG_CHANNEL_ID
from utils import is_admin
import database as db

# ============= КНОПКИ ДЛЯ ТИКЕТОВ =============

class TicketCloseView(discord.ui.View):
    """Кнопка закрытия тикета"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🔒 Закрыть тикет", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Сохраняем транскрипт
        messages = []
        async for msg in interaction.channel.history(limit=100):
            messages.append(f"{msg.author}: {msg.content} ({msg.created_at})")
        
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
    """Панель создания тикетов"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="⚠️ Амнистия", style=discord.ButtonStyle.secondary, custom_id="ticket_amnesty")
    async def amnesty_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from commands.tickets import AmnestyModal
        await interaction.response.send_modal(AmnestyModal())
    
    @discord.ui.button(label="💡 Предложение", style=discord.ButtonStyle.primary, custom_id="ticket_suggestion")
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
    
    @discord.ui.button(label="👑 Заявка на Helper", style=discord.ButtonStyle.primary, custom_id="ticket_admin_application", row=2)
    async def admin_application_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if db.is_admin_application_blocked(interaction.user.id):
            remaining = db.get_admin_application_block_remaining(interaction.user.id)
            return await interaction.response.send_message(
                f"❌ Вы не можете подать заявку ещё **{remaining}**!",
                ephemeral=True
            )
        
        embed = discord.Embed(
            title="📝 Заявка на пост Helper",
            description="Для подачи заявки заполните форму:",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        embed.add_field(
            name="🔗 Ссылка на форму",
            value="[Нажмите здесь](https://forms.gle/PuPzJyyBtZ5ZCSFe8)",
            inline=False
        )
        embed.add_field(
            name="📌 Важно",
            value="• Возраст: от 14 лет\n• Заполните форму подробно",
            inline=False
        )
        embed.set_footer(text="Saint-Rose Project")
        
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message("✅ Ссылка отправлена в ЛС!", ephemeral=True)
        except:
            await interaction.response.send_message(embed=embed, ephemeral=True)

# ============= МОДАЛЬНЫЕ ОКНА =============

class AmnestyModal(discord.ui.Modal, title="⚠️ Запрос на амнистию"):
    reason = discord.ui.TextInput(label="Причина нарушения", placeholder="За что вас наказали?", required=True, max_length=200)
    date = discord.ui.TextInput(label="Дата нарушения", placeholder="Когда это было?", required=True, max_length=50)
    why = discord.ui.TextInput(label="Почему стоит амнистировать", placeholder="Объясните", style=discord.TextStyle.paragraph, required=True, max_length=500)
    
    async def on_submit(self, interaction: discord.Interaction):
        from commands.tickets import create_ticket
        await create_ticket(interaction, "амнистия", {
            "Причина нарушения": self.reason.value,
            "Дата нарушения": self.date.value,
            "Почему стоит амнистировать": self.why.value
        })


class SuggestionModal(discord.ui.Modal, title="💡 Предложение по улучшению"):
    title = discord.ui.TextInput(label="Название", placeholder="Кратко о чём предложение", required=True, max_length=100)
    description = discord.ui.TextInput(label="Описание", placeholder="Подробно опишите идею", style=discord.TextStyle.paragraph, required=True, max_length=1000)
    why = discord.ui.TextInput(label="Почему это нужно", placeholder="Как улучшит сервер?", style=discord.TextStyle.paragraph, required=True, max_length=500)
    
    async def on_submit(self, interaction: discord.Interaction):
        from commands.tickets import create_ticket
        await create_ticket(interaction, "предложение-по-улучшению", {
            "Название": self.title.value,
            "Описание": self.description.value,
            "Почему это нужно": self.why.value
        })


class HelpModal(discord.ui.Modal, title="😊 Проблемы и помощь"):
    problem_type = discord.ui.TextInput(label="Тип проблемы", placeholder="Техническая / Конфликт / Вопрос", required=True, max_length=50)
    description = discord.ui.TextInput(label="Описание", placeholder="Что случилось?", style=discord.TextStyle.paragraph, required=True, max_length=1000)
    tried = discord.ui.TextInput(label="Что пробовали", placeholder="Что вы сделали?", required=False, max_length=500)
    
    async def on_submit(self, interaction: discord.Interaction):
        from commands.tickets import create_ticket
        await create_ticket(interaction, "проблемы-и-помощь", {
            "Тип проблемы": self.problem_type.value,
            "Описание": self.description.value,
            "Что пробовали": self.tried.value or "Не указано"
        })


class ComplaintModal(discord.ui.Modal, title="🔴 Жалоба на администратора"):
    admin_name = discord.ui.TextInput(label="Ник администратора", placeholder="На кого жалоба?", required=True, max_length=50)
    what_happened = discord.ui.TextInput(label="Что произошло", placeholder="Опишите ситуацию", style=discord.TextStyle.paragraph, required=True, max_length=1000)
    evidence = discord.ui.TextInput(label="Доказательства", placeholder="Ссылки на скрины", required=False, max_length=500)
    
    async def on_submit(self, interaction: discord.Interaction):
        from commands.tickets import create_ticket
        await create_ticket(interaction, "жалоба-на-администратора", {
            "Администратор": self.admin_name.value,
            "Ситуация": self.what_happened.value,
            "Доказательства": self.evidence.value or "Не предоставлены"
        })
