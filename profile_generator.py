import discord
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import aiohttp
from datetime import datetime
import os

# Создаём папку для шрифтов если нет
os.makedirs("assets", exist_ok=True)

async def get_avatar_bytes(user: discord.User) -> bytes:
    """Получает аватар пользователя в байтах"""
    avatar_url = user.display_avatar.with_format("png").url
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as resp:
            return await resp.read()

async def generate_profile_image(
    user: discord.User,
    level: int,
    xp: int,
    next_xp: int,
    cookies: int,
    warns: int,
    messages: int,
    join_date: datetime,
    rank: int = None,
    top_percent: float = None
) -> io.BytesIO:
    """
    Генерирует красивую картинку профиля
    """
    # Создаём изображение
    img = Image.new('RGBA', (1000, 500), color=(30, 30, 40, 255))
    draw = ImageDraw.Draw(img)
    
    # Загружаем шрифты (с запасными вариантами)
    font_paths = [
        "assets/arial.ttf",
        "assets/Roboto-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    
    title_font = None
    text_font = None
    small_font = None
    
    for path in font_paths:
        try:
            title_font = ImageFont.truetype(path, 48)
            text_font = ImageFont.truetype(path, 28)
            small_font = ImageFont.truetype(path, 20)
            break
        except:
            continue
    
    if title_font is None:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Рисуем градиентный фон
    for i in range(500):
        ratio = i / 500
        r = int(40 + 20 * ratio)
        g = int(40 + 15 * ratio)
        b = int(60 + 25 * ratio)
        draw.line([(0, i), (1000, i)], fill=(r, g, b))
    
    # Рисуем декоративную рамку
    draw.rectangle([(10, 10), (990, 490)], outline=(255, 215, 0, 150), width=3)
    
    # Аватар
    avatar_bytes = await get_avatar_bytes(user)
    avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    avatar_img = avatar_img.resize((150, 150), Image.Resampling.LANCZOS)
    
    # Маска для круглого аватара
    mask = Image.new('L', (150, 150), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, 150, 150), fill=255)
    
    img.paste(avatar_img, (40, 175), mask)
    
    # Рисуем обводку вокруг аватара
    draw.ellipse((38, 173, 192, 327), outline=(255, 215, 0), width=4)
    
    # Имя пользователя
    name = user.display_name[:25] + ("..." if len(user.display_name) > 25 else "")
    draw.text((220, 175), name, fill=(255, 255, 255), font=title_font)
    
    # Тег
    draw.text((220, 230), f"@{user.name}", fill=(180, 180, 200), font=small_font)
    draw.text((220, 260), f"ID: {user.id}", fill=(150, 150, 170), font=small_font)
    
    # Уровень и XP
    xp_percent = int((xp / next_xp) * 100) if next_xp > 0 else 0
    
    # XP Bar
    bar_x, bar_y = 220, 310
    bar_width, bar_height = 400, 25
    draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], 
                   fill=(50, 50, 70), outline=(100, 100, 120), width=1)
    
    fill_width = int((xp_percent / 100) * bar_width)
    draw.rectangle([(bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height)], 
                   fill=(100, 200, 100))
    
    draw.text((bar_x + 5, bar_y - 5), f"Уровень {level} | XP: {xp}/{next_xp} ({xp_percent}%)",
              fill=(200, 200, 220), font=small_font)
    
    # Статистика (левая колонка)
    y_offset = 370
    stats_left = [
        f"🍪 Печенек: {cookies}",
        f"📊 Ранг: #{rank if rank else '?'}" if rank else f"📊 Топ: {top_percent}%" if top_percent else "📊 Ранг: не в топе",
    ]
    
    for stat in stats_left:
        draw.text((220, y_offset), stat, fill=(255, 215, 0) if "Печенек" in stat else (200, 200, 220), 
                  font=text_font if "Печенек" in stat else small_font)
        y_offset += 35
    
    # Статистика (правая колонка)
    stats_right = [
        f"⚠️ Предупреждений: {warns}",
        f"💬 Сообщений: {messages}",
        f"📅 На сервере: {(datetime.now() - join_date).days} дн."
    ]
    
    x_offset = 600
    y_offset = 370
    for stat in stats_right:
        color = (255, 100, 100) if "Предупреждений" in stat and warns > 0 else (200, 200, 220)
        draw.text((x_offset, y_offset), stat, fill=color, font=small_font)
        y_offset += 35
    
    # Нижняя полоса с ником и датой
    draw.line([(20, 470), (980, 470)], fill=(255, 215, 0, 100), width=1)
    draw.text((40, 475), f"Saint-Rose • Профиль сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}", 
              fill=(150, 150, 170), font=small_font)
    
    # Сохраняем в байтовый буфер
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return buffer