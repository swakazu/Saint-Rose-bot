import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("saint_rose_data.db")
cursor = conn.cursor()

def init_db():
    """Инициализация всех таблиц"""
    
    # Предупреждения
    cursor.execute("""CREATE TABLE IF NOT EXISTS warnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        guild_id INTEGER,
        moderator_id INTEGER,
        reason TEXT,
        time TEXT
    )""")
    
    # Уровни
    cursor.execute("""CREATE TABLE IF NOT EXISTS levels (
        user_id INTEGER PRIMARY KEY,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        messages INTEGER DEFAULT 0,
        last_message_time TEXT
    )""")
    
    # Экономика
    cursor.execute("""CREATE TABLE IF NOT EXISTS economy (
        user_id INTEGER PRIMARY KEY,
        cookies INTEGER DEFAULT 0,
        daily_last_claim TEXT,
        weekly_last_claim TEXT
    )""")
    
    # Инвентарь
    cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER,
        item_id TEXT,
        quantity INTEGER DEFAULT 1,
        PRIMARY KEY (user_id, item_id)
    )""")
    
    # Напоминания
    cursor.execute("""CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        channel_id INTEGER,
        message TEXT,
        remind_time TEXT
    )""")
    
    # Кастомные команды
    cursor.execute("""CREATE TABLE IF NOT EXISTS custom_commands (
        name TEXT,
        guild_id INTEGER,
        response TEXT,
        PRIMARY KEY (name, guild_id)
    )""")
    
    # Блокировка заявок
    cursor.execute("""CREATE TABLE IF NOT EXISTS admin_applications_block (
        user_id INTEGER PRIMARY KEY,
        block_until TEXT
    )""")
    
    conn.commit()
    print("✅ База данных инициализирована")

# ============= УРОВНИ =============

def get_user_level(user_id):
    cursor.execute("SELECT xp, level, messages FROM levels WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def create_user_level(user_id):
    cursor.execute("INSERT INTO levels (user_id, xp, level, messages) VALUES (?, 0, 1, 0)", (user_id,))
    conn.commit()
    return (0, 1, 0)

def update_user_level(user_id, xp, level, messages=None):
    if messages is not None:
        cursor.execute("UPDATE levels SET xp = ?, level = ?, messages = ? WHERE user_id = ?",
                       (xp, level, messages, user_id))
    else:
        cursor.execute("UPDATE levels SET xp = ?, level = ? WHERE user_id = ?",
                       (xp, level, user_id))
    conn.commit()

def add_xp(user_id, xp_gain):
    result = get_user_level(user_id)
    if result:
        xp, level, msgs = result
        return xp + xp_gain, level, msgs
    create_user_level(user_id)
    return xp_gain, 1, 0

def increment_messages(user_id):
    result = get_user_level(user_id)
    if result:
        xp, level, msgs = result
        cursor.execute("UPDATE levels SET messages = ? WHERE user_id = ?", (msgs + 1, user_id))
        conn.commit()
        return msgs + 1
    return 1

def get_level_leaderboard(limit=10):
    cursor.execute("SELECT user_id, level, xp FROM levels ORDER BY level DESC, xp DESC LIMIT ?", (limit,))
    return cursor.fetchall()

# ============= ЭКОНОМИКА =============

def get_cookies(user_id):
    cursor.execute("SELECT cookies FROM economy WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def add_cookie(user_id, amount=1):
    cursor.execute("INSERT INTO economy (user_id, cookies) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET cookies = cookies + ?",
                   (user_id, amount, amount))
    conn.commit()

def remove_cookie(user_id, amount=1):
    current = get_cookies(user_id)
    if current >= amount:
        cursor.execute("UPDATE economy SET cookies = cookies - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        return True
    return False

def get_cookie_leaderboard(limit=10):
    cursor.execute("SELECT user_id, cookies FROM economy ORDER BY cookies DESC LIMIT ?", (limit,))
    return cursor.fetchall()

def get_daily_claim(user_id):
    cursor.execute("SELECT daily_last_claim FROM economy WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def set_daily_claim(user_id, time_str):
    cursor.execute("INSERT INTO economy (user_id, daily_last_claim) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET daily_last_claim = ?",
                   (user_id, time_str, time_str))
    conn.commit()

def get_weekly_claim(user_id):
    cursor.execute("SELECT weekly_last_claim FROM economy WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def set_weekly_claim(user_id, time_str):
    cursor.execute("INSERT INTO economy (user_id, weekly_last_claim) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET weekly_last_claim = ?",
                   (user_id, time_str, time_str))
    conn.commit()

# ============= МАГАЗИН =============

SHOP_ITEMS = {
    "color_role": {"name": "🎨 Цветная роль", "price": 50, "description": "Возможность выбрать цвет своей роли"},
    "nick_change": {"name": "✏️ Смена ника", "price": 30, "description": "Один раз сменить ник на сервере"},
    "xp_boost": {"name": "⚡ Буст XP", "price": 100, "description": "Удвоение XP на 24 часа"},
}

def add_item(user_id, item_id, quantity=1):
    cursor.execute("INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?) ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + ?",
                   (user_id, item_id, quantity, quantity))
    conn.commit()

def get_inventory(user_id):
    cursor.execute("SELECT item_id, quantity FROM inventory WHERE user_id = ?", (user_id,))
    return cursor.fetchall()

def use_item(user_id, item_id):
    cursor.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
    result = cursor.fetchone()
    if result and result[0] > 0:
        cursor.execute("UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        conn.commit()
        cursor.execute("DELETE FROM inventory WHERE user_id = ? AND item_id = ? AND quantity <= 0", (user_id, item_id))
        conn.commit()
        return True
    return False

# ============= ПРЕДУПРЕЖДЕНИЯ =============

def add_warning(user_id, guild_id, moderator_id, reason):
    cursor.execute("INSERT INTO warnings (user_id, guild_id, moderator_id, reason, time) VALUES (?, ?, ?, ?, ?)",
                   (user_id, guild_id, moderator_id, reason, str(datetime.now())))
    conn.commit()
    return get_warning_count(user_id, guild_id)

def get_warning_count(user_id, guild_id):
    cursor.execute("SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
    return cursor.fetchone()[0]

def get_warnings(user_id, guild_id, limit=10):
    cursor.execute("SELECT reason, moderator_id, time FROM warnings WHERE user_id = ? AND guild_id = ? ORDER BY time DESC LIMIT ?",
                   (user_id, guild_id, limit))
    return cursor.fetchall()

def remove_warning(warning_id):
    cursor.execute("DELETE FROM warnings WHERE id = ?", (warning_id,))
    conn.commit()

# ============= НАПОМИНАНИЯ =============

def add_reminder(user_id, channel_id, message, remind_time):
    cursor.execute("INSERT INTO reminders (user_id, channel_id, message, remind_time) VALUES (?, ?, ?, ?)",
                   (user_id, channel_id, message, str(remind_time)))
    conn.commit()

def get_pending_reminders():
    cursor.execute("SELECT id, user_id, channel_id, message, remind_time FROM reminders")
    return cursor.fetchall()

def delete_reminder(reminder_id):
    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()

# ============= КАСТОМНЫЕ КОМАНДЫ =============

def add_custom_command(name, guild_id, response):
    cursor.execute("INSERT OR REPLACE INTO custom_commands (name, guild_id, response) VALUES (?, ?, ?)",
                   (name, guild_id, response))
    conn.commit()

def get_custom_command(name, guild_id):
    cursor.execute("SELECT response FROM custom_commands WHERE name = ? AND guild_id = ?", (name, guild_id))
    result = cursor.fetchone()
    return result[0] if result else None

def delete_custom_command(name, guild_id):
    cursor.execute("DELETE FROM custom_commands WHERE name = ? AND guild_id = ?", (name, guild_id))
    conn.commit()

def get_all_custom_commands(guild_id):
    cursor.execute("SELECT name, response FROM custom_commands WHERE guild_id = ?", (guild_id,))
    return cursor.fetchall()

# ============= БЛОКИРОВКА ЗАЯВОК =============

def is_admin_application_blocked(user_id):
    cursor.execute("SELECT block_until FROM admin_applications_block WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result and result[0]:
        block_until = datetime.fromisoformat(result[0])
        if datetime.now() < block_until:
            return True
        cursor.execute("DELETE FROM admin_applications_block WHERE user_id = ?", (user_id,))
        conn.commit()
    return False

def get_admin_application_block_remaining(user_id):
    cursor.execute("SELECT block_until FROM admin_applications_block WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result and result[0]:
        block_until = datetime.fromisoformat(result[0])
        remaining = block_until - datetime.now()
        days = remaining.days
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}д {hours}ч"
        elif hours > 0:
            return f"{hours}ч {minutes}мин"
        return f"{minutes}мин"
    return "0"

def block_admin_application(user_id, days=0, hours=0, minutes=0):
    block_until = datetime.now() + timedelta(days=days, hours=hours, minutes=minutes)
    cursor.execute("INSERT INTO admin_applications_block (user_id, block_until) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET block_until = ?",
                   (user_id, str(block_until), str(block_until)))
    conn.commit()

def unblock_admin_application(user_id):
    cursor.execute("DELETE FROM admin_applications_block WHERE user_id = ?", (user_id,))
    conn.commit()

# Инициализация
init_db()
