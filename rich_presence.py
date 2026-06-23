# rich_presence.py
from pypresence import Presence
import time
from datetime import datetime

# ========== НАСТРОЙКИ ==========
# Зарегистрируй приложение на https://discord.com/developers/applications
# и скопируй APPLICATION ID
CLIENT_ID = "1509126223177977896"  # 👈 ВСТАВЬ СЮДА

# Ссылки на Discord и Telegram
DISCORD_LINK = "https://discord.gg/saintroseproject"
TELEGRAM_LINK = "https://t.me/saintroseproject"

# ========== ПОДКЛЮЧЕНИЕ ==========
RPC = Presence(CLIENT_ID)
RPC.connect()

print("✅ Подключено к Discord!")

# ========== УСТАНОВКА СТАТУСА ==========
RPC.update(
    # Основной текст - "Играет в SR"
    details="Saint-Rose",
    
    # Дополнительная информация - вторая строка
    state="SaintRose | Connect 46.174.49.224:27015",
    
    # Картинка (должна быть загружена в Art Assets)
    large_image="saint_rose_logo",  # Название картинки
    large_text="Saint-Rose Project",
    
    # Маленькая картинка (опционально)
    small_image="sr_icon",
    small_text="Saint-Rose",
    
    # ========== КНОПКИ ==========
    buttons=[
        {"label": "Discord", "url": DISCORD_LINK},
        {"label": "Telegram", "url": TELEGRAM_LINK}
    ],
    
    # Таймер (время начала "игры")
    start=int(time.time()),
    
    # Время окончания (опционально)
    # end=int(time.time()) + 3600,  # Через час закончится
)

print("✅ Статус установлен!")
print("📡 Нажми Ctrl+C для выхода")

# ========== ДЕРЖИМ СКРИПТ ЗАПУЩЕННЫМ ==========
try:
    while True:
        time.sleep(15)
except KeyboardInterrupt:
    print("\n❌ Отключено")
    RPC.close()
