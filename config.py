import logging
import sqlite3
import os

TOKEN = os.getenv("TOKEN")

WELCOME_CHANNEL_ID = 1510678225058267157
LOG_CHANNEL_ID = 1510678500028321972
TICKET_CATEGORY_ID = 1511091999468687651
MUTE_ROLE_ID = 1511086391893819482
OWNER_ID = 1510685758724374649
GUILD_ID = 1510638426016448602
PRIVATE_VOICE_CREATE_CHANNEL_ID = 1515757876780732427  
PRIVATE_VOICE_CATEGORY_ID = 1515757790482927841  
PRIVATE_VOICE_DELETE_TIMEOUT = 30

BOT_NAME = "Saint-Rose"

ADMIN_ROLES_IN_ORDER = [
    "Владелец", "Со-Владелец", "Зам. Владельца", "Saint-Rose Team",
    "Управляющий", "Менеджер", "Зам. Менеджера", "Старший куратор",
    "Куратор", "Высший администратор", "Старший администратор"
]

XP_PER_MESSAGE_MIN = 5
XP_PER_MESSAGE_MAX = 15
LEVEL_UP_MULTIPLIER = 1.5
BASE_XP_NEEDED = 100

MAX_CLEAR_MESSAGES = 100

COLORS = {
    "red": 0xFF0000,    
    "green": 0x00FF00,
    "blue": 0x3498db,
    "yellow": 0xFFD700,
    "orange": 0xFFA500,
    "purple": 0x9B59B6,
    "gold": 0xF1C40F,
}

BAD_WORDS = ["дурак", "идиот", "тупой", "дебил", "кретин", "шлюха", "мать", "папа", "бабушка", "сын", "дочь", "дедушка"]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(BOT_NAME)
