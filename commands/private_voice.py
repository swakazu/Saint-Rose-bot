import discord
from discord import app_commands
import asyncio
from config import PRIVATE_VOICE_CREATE_CHANNEL_ID, PRIVATE_VOICE_CATEGORY_ID, PRIVATE_VOICE_DELETE_TIMEOUT
from utils import is_admin

private_rooms = {}
panel_messages = {}

class RoomPanel(discord.ui.View):
    def __init__(self, owner_id: int, channel: discord.VoiceChannel):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.channel = channel
    
    async def check(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Только создатель комнаты!", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="👑 Назначить создателя", style=discord.ButtonStyle.secondary, row=0)
    async def transfer_owner(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check(interaction):
            return
        
        members = [m for m in self.channel.members if not m.bot and m.id != self.owner_id]
        if not members:
            return await interaction.response.send_message("❌ Нет других участников", ephemeral=True)
        
        select = discord.ui.Select(
            placeholder="Выберите нового создателя",
            options=[discord.SelectOption(label=m.display_name[:50], value=str(m.id)) for m in members[:25]]
        )
        
        async def select_cb(ctx):
            private_rooms[self.channel.id] = int(select.values[0])
            await ctx.response.send_message(f"✅ Новый создатель: <@{select.values[0]}>", ephemeral=True)
            await update_panel(self.channel.guild, self.channel)
        
        select.callback = select_cb
        view = discord.ui.View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message("👑 Выберите нового создателя:", view=view, ephemeral=True)
    
    @discord.ui.button(label="🔐 Доступ", style=discord.ButtonStyle.secondary, row=0)
    async def manage_access(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check(interaction):
            return
        
        select = discord.ui.Select(
            placeholder="Выберите пользователя",
            options=[discord.SelectOption(label=m.display_name[:50], value=str(m.id)) for m in interaction.guild.members[:25] if not m.bot]
        )
        
        async def select_cb(ctx):
            user = ctx.guild.get_member(int(select.values[0]))
            if user:
                current = self.channel.overwrites_for(user)
                if current.connect is False:
                    await self.channel.set_permissions(user, connect=True, view_channel=True)
                    await ctx.response.send_message(f"✅ {user.display_name} получил доступ", ephemeral=True)
                else:
                    await self.channel.set_permissions(user, connect=False)
                    await ctx.response.send_message(f"❌ {user.display_name} потерял доступ", ephemeral=True)
        
        select.callback = select_cb
        view = discord.ui.View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message("🔐 Выберите пользователя:", view=view, ephemeral=True)
    
    @discord.ui.button(label="👥 Лимит", style=discord.ButtonStyle.secondary, row=0)
    async def set_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check(interaction):
            return
        
        modal = LimitModal(self.channel)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🔒 Закрыть/открыть", style=discord.ButtonStyle.secondary, row=1)
    async def toggle_lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check(interaction):
            return
        
        current = self.channel.overwrites_for(interaction.guild.default_role)
        if current.connect is False:
            await self.channel.set_permissions(interaction.guild.default_role, connect=None)
            await interaction.response.send_message("🔓 Комната открыта", ephemeral=True)
        else:
            await self.channel.set_permissions(interaction.guild.default_role, connect=False)
            await interaction.response.send_message("🔒 Комната закрыта", ephemeral=True)
    
    @discord.ui.button(label="✏️ Переименовать", style=discord.ButtonStyle.secondary, row=1)
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check(interaction):
            return
        
        modal = RenameModal(self.channel)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="👁️ Скрыть/показать", style=discord.ButtonStyle.secondary, row=1)
    async def toggle_hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check(interaction):
            return
        
        current = self.channel.overwrites_for(interaction.guild.default_role)
        if current.view_channel is False:
            await self.channel.set_permissions(interaction.guild.default_role, view_channel=None)
            await interaction.response.send_message("👁️ Комната видна всем", ephemeral=True)
        else:
            await self.channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await interaction.response.send_message("👻 Комната скрыта", ephemeral=True)
    
    @discord.ui.button(label="👢 Выгнать", style=discord.ButtonStyle.danger, row=2)
    async def kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check(interaction):
            return
        
        members = [m for m in self.channel.members if m.id != self.owner_id]
        if not members:
            return await interaction.response.send_message("❌ Нет других участников", ephemeral=True)
        
        select = discord.ui.Select(
            placeholder="Кого выгнать",
            options=[discord.SelectOption(label=m.display_name[:50], value=str(m.id)) for m in members[:25]]
        )
        
        async def select_cb(ctx):
            user = ctx.guild.get_member(int(select.values[0]))
            if user and user in self.channel.members:
                await user.move_to(None)
                await ctx.response.send_message(f"👢 {user.display_name} выгнан", ephemeral=True)
        
        select.callback = select_cb
        view = discord.ui.View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message("👢 Выберите участника:", view=view, ephemeral=True)
    
    @discord.ui.button(label="🎤 Запретить/разрешить говорить", style=discord.ButtonStyle.secondary, row=2)
    async def mute(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check(interaction):
            return
        
        members = [m for m in self.channel.members if m.id != self.owner_id]
        if not members:
            return await interaction.response.send_message("❌ Нет других участников", ephemeral=True)
        
        select = discord.ui.Select(
            placeholder="Кому ограничить",
            options=[discord.SelectOption(label=m.display_name[:50], value=str(m.id)) for m in members[:25]]
        )
        
        async def select_cb(ctx):
            user = ctx.guild.get_member(int(select.values[0]))
            if user:
                current = self.channel.overwrites_for(user)
                if current.speak is False:
                    await self.channel.set_permissions(user, speak=None)
                    await ctx.response.send_message(f"🎤 {user.display_name} может говорить", ephemeral=True)
                else:
                    await self.channel.set_permissions(user, speak=False)
                    await ctx.response.send_message(f"🔇 {user.display_name} не может говорить", ephemeral=True)
        
        select.callback = select_cb
        view = discord.ui.View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message("🎤 Выберите участника:", view=view, ephemeral=True)
    
    @discord.ui.button(label="❌ Удалить комнату", style=discord.ButtonStyle.danger, row=2)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check(interaction):
            return
        
        await interaction.response.send_message("🗑️ Комната удаляется...", ephemeral=True)
        for member in list(self.channel.members):
            await member.move_to(None)
        
        if self.channel.id in panel_messages:
            try:
                msg = await self.channel.fetch_message(panel_messages[self.channel.id])
                await msg.delete()
            except:
                pass
        
        await self.channel.delete()
        private_rooms.pop(self.channel.id, None)
        panel_messages.pop(self.channel.id, None)

class RenameModal(discord.ui.Modal, title="✏️ Изменить название"):
    name = discord.ui.TextInput(label="Новое название", placeholder="Введите название", required=True, max_length=100)
    
    def __init__(self, channel: discord.VoiceChannel):
        super().__init__()
        self.channel = channel
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.channel.edit(name=self.name.value)
            await interaction.response.send_message(f"✅ Название: {self.name.value}", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Ошибка", ephemeral=True)

class LimitModal(discord.ui.Modal, title="👥 Лимит участников"):
    limit = discord.ui.TextInput(label="Лимит (0-99)", placeholder="0 = безлимит", required=True, max_length=2)
    
    def __init__(self, channel: discord.VoiceChannel):
        super().__init__()
        self.channel = channel
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit = int(self.limit.value)
            if 0 <= limit <= 99:
                await self.channel.edit(user_limit=limit if limit > 0 else None)
                await interaction.response.send_message(f"✅ Лимит: {limit if limit > 0 else 'безлимит'}", ephemeral=True)
            else:
                raise ValueError
        except:
            await interaction.response.send_message("❌ Число 0-99", ephemeral=True)

async def create_voice_room(member: discord.Member):
    """Создание приватной голосовой комнаты"""
    category = member.guild.get_channel(PRIVATE_VOICE_CATEGORY_ID)
    
    channel = await member.guild.create_voice_channel(
        name=f"🔊 {member.display_name}",
        category=category,
        user_limit=0
    )
    
    await channel.set_permissions(member.guild.default_role, connect=False, view_channel=False)
    await channel.set_permissions(member, connect=True, view_channel=True)
    
    private_rooms[channel.id] = member.id
    
    embed = discord.Embed(
        title="🎤 Приватные комнаты",
        description="**Управление комнатой:**\n\n"
                   "• 👑 Назначить нового создателя\n"
                   "• 🔐 Управление доступом\n"
                   "• 👥 Изменить лимит участников\n"
                   "• 🔒 Закрыть/открыть комнату\n"
                   "• ✏️ Изменить название\n"
                   "• 👁️ Скрыть/показать комнату\n"
                   "• 👢 Выгнать участника\n"
                   "• 🎤 Запретить/разрешить говорить",
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"Создатель: {member.display_name}")
    
    view = RoomPanel(member.id, channel)
    msg = await channel.send(embed=embed, view=view)
    panel_messages[channel.id] = msg.id
    
    await member.move_to(channel)
    return channel

async def update_panel(guild: discord.Guild, channel: discord.VoiceChannel):
    """Обновляет панель управления комнатой"""
    if channel.id not in panel_messages or channel.id not in private_rooms:
        return
    
    owner_id = private_rooms[channel.id]
    owner = guild.get_member(owner_id)
    
    try:
        msg_id = panel_messages[channel.id]
        msg = await channel.fetch_message(msg_id)
        
        embed = discord.Embed(
            title="🎤 Приватные комнаты",
            description="**Управление комнатой:**\n\n"
                       "• 👑 Назначить нового создателя\n"
                       "• 🔐 Управление доступом\n"
                       "• 👥 Изменить лимит участников\n"
                       "• 🔒 Закрыть/открыть комнату\n"
                       "• ✏️ Изменить название\n"
                       "• 👁️ Скрыть/показать комнату\n"
                       "• 👢 Выгнать участника\n"
                       "• 🎤 Запретить/разрешить говорить",
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Создатель: {owner.display_name if owner else 'Неизвестен'}")
        
        view = RoomPanel(owner_id, channel)
        await msg.edit(embed=embed, view=view)
    except:
        pass

def setup_private_voice(bot):
    
    @bot.event
    async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # Заход в канал создания комнаты
        if after.channel and after.channel.id == PRIVATE_VOICE_CREATE_CHANNEL_ID:
            # Проверяем, нет ли уже комнаты
            for room_id, owner_id in private_rooms.items():
                if owner_id == member.id:
                    room = member.guild.get_channel(room_id)
                    if room:
                        await member.move_to(room)
                        return
            
            await create_voice_room(member)
        
        # Если комната опустела - удаляем
        if before.channel and before.channel.id in private_rooms:
            if len(before.channel.members) == 0:
                await asyncio.sleep(PRIVATE_VOICE_DELETE_TIMEOUT)
                if len(before.channel.members) == 0 and before.channel.id in private_rooms:
                    try:
                        if before.channel.id in panel_messages:
                            try:
                                msg = await before.channel.fetch_message(panel_messages[before.channel.id])
                                await msg.delete()
                            except:
                                pass
                        await before.channel.delete()
                        private_rooms.pop(before.channel.id, None)
                        panel_messages.pop(before.channel.id, None)
                    except:
                        pass
    
    @bot.tree.command(name="админ_панель_комнат", description="Создать панель управления комнатами")
    async def admin_panel(interaction: discord.Interaction):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Только администрация!", ephemeral=True)
        
        embed = discord.Embed(
            title="🎤 Приватные комнаты",
            description=f"**Как создать комнату:** Зайдите в голосовой канал <#{PRIVATE_VOICE_CREATE_CHANNEL_ID}>",
            color=discord.Color.purple()
        )
        embed.set_footer(text="Saint-Rose • Приватные комнаты")
        await interaction.response.send_message(embed=embed)
    
    print("✅ Приватные комнаты загружены!")
