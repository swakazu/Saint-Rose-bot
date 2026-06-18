import discord
from discord import app_commands
from datetime import datetime, timedelta

import database as db
from utils import is_admin

def setup_economy_commands(bot):
    
    @bot.tree.command(name="печенька", description="Дать печеньку участнику")
    @app_commands.describe(member="Участник", amount="Количество печенек")
    async def give_cookie(interaction: discord.Interaction, member: discord.Member, amount: int = 1):
        if member == interaction.user:
            return await interaction.response.send_message("🍪 Нельзя дать печеньку самому себе!", ephemeral=True)
        
        if amount < 1 or amount > 100:
            return await interaction.response.send_message("❌ Можно дать от 1 до 100 печенек", ephemeral=True)
        
        db.add_cookie(member.id, amount)
        embed = discord.Embed(
            title="🍪 Печенька выдана!",
            description=f"{interaction.user.mention} дал {amount} 🍪 {member.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Всего у {member.display_name}: {db.get_cookies(member.id)} печенек")
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="топпеченек", description="Топ по печенькам на сервере")
    async def cookie_leaderboard(interaction: discord.Interaction):
        top = db.get_cookie_leaderboard(10)
        
        if not top:
            return await interaction.response.send_message("🍪 Никто ещё не получал печеньки...", ephemeral=True)
        
        embed = discord.Embed(title="🍪 Топ печенек", color=discord.Color.gold())
        for i, (uid, cookies) in enumerate(top, 1):
            member = interaction.guild.get_member(uid)
            name = member.display_name if member else f"Пользователь {uid}"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            embed.add_field(name=medal, value=f"{name} — {cookies} 🍪", inline=False)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="уровень", description="Показать уровень участника")
    @app_commands.describe(member="Участник (опционально)")
    async def show_level(interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        result = db.get_user_level(target.id)
        
        if not result:
            xp, level, messages = 0, 1, 0
        else:
            xp, level, messages = result
        
        required_xp = int(100 * level * 1.5)
        progress = int((xp / required_xp) * 100) if required_xp > 0 else 0
        
        embed = discord.Embed(
            title=f"📊 Уровень {target.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Уровень", value=level, inline=True)
        embed.add_field(name="XP", value=f"{xp}/{required_xp}", inline=True)
        embed.add_field(name="Прогресс", value=f"{progress}%", inline=True)
        embed.add_field(name="💬 Сообщений", value=messages, inline=True)
        embed.add_field(name="🍪 Печенек", value=db.get_cookies(target.id), inline=True)
        embed.add_field(name="⚠️ Предупреждений", value=db.get_warning_count(target.id, interaction.guild_id), inline=True)
        
        if target.avatar:
            embed.set_thumbnail(url=target.avatar.url)
        
        await interaction.response.send_message(embed=embed, ephemeral=(member is not None))

    @bot.tree.command(name="ежедневно", description="Получить ежедневную награду")
    async def daily(interaction: discord.Interaction):
        last_claim = db.get_daily_claim(interaction.user.id)
        
        if last_claim:
            last_time = datetime.fromisoformat(last_claim)
            next_claim = last_time + timedelta(hours=24)
            if datetime.now() < next_claim:
                remaining = next_claim - datetime.now()
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                return await interaction.response.send_message(
                    f"⏰ Ежедневная награда будет доступна через {hours}ч {minutes}мин", 
                    ephemeral=True
                )
        
        reward = 15
        db.add_cookie(interaction.user.id, reward)
        db.set_daily_claim(interaction.user.id, str(datetime.now()))
        
        embed = discord.Embed(
            title="🎁 Ежедневная награда!",
            description=f"Вы получили {reward} 🍪 печенек!\nВсего печенек: {db.get_cookies(interaction.user.id)}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="еженедельно", description="Получить еженедельную награду")
    async def weekly(interaction: discord.Interaction):
        last_claim = db.get_weekly_claim(interaction.user.id)
        
        if last_claim:
            last_time = datetime.fromisoformat(last_claim)
            next_claim = last_time + timedelta(days=7)
            if datetime.now() < next_claim:
                remaining = next_claim - datetime.now()
                days = remaining.days
                hours = int((remaining.total_seconds() % 86400) // 3600)
                return await interaction.response.send_message(
                    f"⏰ Еженедельная награда будет доступна через {days}д {hours}ч", 
                    ephemeral=True
                )
        
        reward = 75
        db.add_cookie(interaction.user.id, reward)
        db.set_weekly_claim(interaction.user.id, str(datetime.now()))
        
        embed = discord.Embed(
            title="🎁 Еженедельная награда!",
            description=f"Вы получили {reward} 🍪 печенек!\nВсего печенек: {db.get_cookies(interaction.user.id)}",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="магазин", description="Показать магазин предметов")
    async def shop(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 Магазин Saint-Rose",
            description="Купить предметы можно командой `/купить <предмет>`",
            color=discord.Color.gold()
        )
        
        for item_id, item in db.SHOP_ITEMS.items():
            embed.add_field(
                name=f"{item['name']} — {item['price']} 🍪",
                value=item['description'],
                inline=False
            )
        
        embed.set_footer(text=f"Ваш баланс: {db.get_cookies(interaction.user.id)} 🍪")
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="купить", description="Купить предмет в магазине")
    @app_commands.describe(item="Название предмета")
    async def buy(interaction: discord.Interaction, item: str):
        # Поиск предмета
        found_item = None
        for item_id, item_data in db.SHOP_ITEMS.items():
            if item.lower() in item_id.lower() or item.lower() in item_data['name'].lower():
                found_item = (item_id, item_data)
                break
        
        if not found_item:
            return await interaction.response.send_message("❌ Предмет не найден! Используйте `/магазин` для списка", ephemeral=True)
        
        item_id, item_data = found_item
        price = item_data['price']
        
        cookies = db.get_cookies(interaction.user.id)
        
        if cookies < price:
            return await interaction.response.send_message(f"❌ Недостаточно печенек! Нужно: {price}, у вас: {cookies}", ephemeral=True)
        
        db.remove_cookie(interaction.user.id, price)
        db.add_item(interaction.user.id, item_id)
        
        embed = discord.Embed(
            title="✅ Покупка совершена!",
            description=f"Вы купили **{item_data['name']}** за {price} 🍪\nОсталось печенек: {db.get_cookies(interaction.user.id)}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="инвентарь", description="Показать свой инвентарь")
    async def inventory(interaction: discord.Interaction):
        items = db.get_inventory(interaction.user.id)
        
        if not items:
            return await interaction.response.send_message("📦 Ваш инвентарь пуст!", ephemeral=True)
        
        embed = discord.Embed(
            title="📦 Инвентарь",
            description="Ваши предметы:",
            color=discord.Color.blue()
        )
        
        for item_id, quantity in items:
            item_data = db.SHOP_ITEMS.get(item_id, {"name": item_id, "description": "?"})
            embed.add_field(
                name=f"{item_data['name']} x{quantity}",
                value=item_data['description'],
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @bot.tree.command(name="датьпеченьку", description="Дать печеньку через модальное окно (админ)")
    async def give_cookie_modal_admin(interaction: discord.Interaction):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Только администрация!", ephemeral=True)
        
        # Используем модалку из admin_panel
        from commands.admin_panel import GiveCookieModal
        await interaction.response.send_modal(GiveCookieModal())