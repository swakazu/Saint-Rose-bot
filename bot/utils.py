import asyncio
import discord
from datetime import datetime
from config import ADMIN_ROLES_IN_ORDER, OWNER_ID
import database as db

def get_admin_level(member):
    # Если передан User вместо Member
    if not hasattr(member, 'roles'):
        return 999
    
    if member.id == OWNER_ID:
        return 0
    for i, role_name in enumerate(ADMIN_ROLES_IN_ORDER):
        role = discord.utils.get(member.roles, name=role_name)
        if role:
            return i
    return 999

def is_admin(member):
    # Если передан User вместо Member
    if not hasattr(member, 'roles'):
        return False
    return get_admin_level(member) != 999

def can_moderate(member, target):
    # Если передан User вместо Member
    if not hasattr(member, 'roles') or not hasattr(target, 'roles'):
        return False
    return get_admin_level(member) < get_admin_level(target)

def get_role_hierarchy(guild: discord.Guild):
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
            
            for rid, uid, cid, msg, rtime in reminders:
                if datetime.now() >= datetime.fromisoformat(rtime):
                    channel = bot.get_channel(cid)
                    if channel:
                        await channel.send(f"⏰ <@{uid}>, напоминание: {msg}")
                    db.delete_reminder(rid)
        except Exception as e:
            print(f"Ошибка в напоминаниях: {e}")
        
        await asyncio.sleep(30)