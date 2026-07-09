import asyncio
import discord
from datetime import datetime
from config import ADMIN_ROLES_IN_ORDER
import database as db

def get_admin_level(member):
    """Возвращает уровень администратора (0 - высший, 999 - не админ)"""
    if not hasattr(member, 'roles'):
        return 999
    
    for i, role_name in enumerate(ADMIN_ROLES_IN_ORDER):
        role = discord.utils.get(member.roles, name=role_name)
        if role:
            return i
    return 999

def is_admin(member):
    """Проверяет, является ли участник администратором"""
    if not hasattr(member, 'roles'):
        return False
    return get_admin_level(member) != 999

def can_moderate(member, target):
    """Проверяет, может ли member модеррировать target"""
    if not hasattr(member, 'roles') or not hasattr(target, 'roles'):
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
