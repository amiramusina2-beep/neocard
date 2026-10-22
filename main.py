import os
import random
import time
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()

ADMIN_ID = 6661291589
users = {}
blocked_users = set()
COOLDOWN_TIME = 120

def generate_unique_card():
    prefix = random.choice(["4400", "5210", "4020", "5536"])
    card_number = f"{prefix} {random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"
    exp_month = f"{random.randint(1, 12):02d}"
    exp_year = str(random.randint(2032, 2035))
    return {
        "number": card_number,
        "exp": f"{exp_month}/{exp_year}",
        "cvc": f"{random.randint(100, 999)}",
        "pin": f"{random.randint(1000, 9999)}"
    }

def get_user(user_id: int, username: str = "Игрок"):
    if user_id not in users:
        users[user_id] = {
            "name": username,
            "card": generate_unique_card(),
            "balance": 500,
            "crypto_balance": 0.0,
            "inventory": [],
            "purchases": [],
            "level": 1,
            "xp": 0,
            "freelance_cooldown": 0,
            "daily_streak": 0,
            "last_daily": 0
        }
    return users[user_id]

CASE_PRICE = 350
CASE_ITEMS = [
    {"name": "🔪 Нож | Охотник (Полевые)", "price": 1200, "chance": 4},
    {"name": "🗡️ Керамбит | Градиент (Прямо с завода)", "price": 8500, "chance": 1},
    {"name": "🔫 AK-47 | Красная линия", "price": 950, "chance": 15},
    {"name": "🔫 M4A4 | Империал", "price": 700, "chance": 20},
    {"name": "🔫 USP-S | Неонуар", "price": 450, "chance": 25},
    {"name": "🛡️ Граф-пакет (Обычный)", "price": 100, "chance": 35},
]

SHOP_ITEMS = [
    {"id": "p1", "name": "⭐ Telegram Premium (1 мес)", "price": 1500},
    {"id": "p2", "name": "🎧 Игровая гарнитура HyperX", "price": 4500},
    {"id": "p3", "name": "📱 Смартфон Flagship X", "price": 25000},
    {"id": "p4", "name": "💻 Мощный Игровой ПК RTX 4090", "price": 120000},
    {"id": "p5", "name": "🏎️ Спортивный Электрокар", "price": 450000},
    {"id": "p6", "name": "🏝️ Тропический Остров", "price": 2000000},
]

QUIZ_QUESTIONS = [
    {"q": "Какая функция в Python используется для вывода данных?", "options": ["print()", "echo()", "scan()", "write()"], "correct": 0, "reward": 300},
    {"q": "Какой протокол безопасной передачи данных?", "options": ["HTTP", "SSL/TLS", "FTP", "SSH"], "correct": 1, "reward": 350},
    {"q": "Сколько бит в одном байте?", "options": ["4", "8", "16", "32"], "correct": 1, "reward": 250}
]

def add_xp(user, amount):
    user['xp'] += amount
    if user['xp'] >= user['level'] * 300:
        user['xp'] = 0
        user['level'] += 1
        return True
    return False

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Моя NeoCard (Реквизиты)", callback_data="my_card")],
        [
            InlineKeyboardButton(text="💻 IT-Фриланс", callback_data="freelance_hub"),
            InlineKeyboardButton(text="📦 Открыть Кейс ($350)", callback_data="open_case_menu")
        ],
        [
            InlineKeyboardButton(text="📈 Криптобиржа", callback_data="crypto_hub"),
            InlineKeyboardButton(text="🧠 Умный Квиз", callback_data="start_quiz")
        ],
        [
            InlineKeyboardButton(text="🛍️ Магазин", callback_data="shop"),
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory")
        ],
        [InlineKeyboardButton(text="🎁 Ежедневный Бонус", callback_data="daily")]
    ])

def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="main_menu")]
    ])

def render_card(user):
    card = user['card']
    return (
        f"💳 ВИРТУАЛЬНАЯ КАРТА NEOCARD 💳\n"
        f"👤 Владелец: {user['name']} | Уровень: {user['level']} (XP: {user['xp']}/{user['level']*300})\n"
        f"🔢 Номер: {card['number']}\n"
        f"📅 Срок: {card['exp']} | CVC: {card['cvc']}\n"
        f"💵 Баланс: ${user['balance']} | Крипта: {user['crypto_balance']:.2f} NC\n"
        f"🎒 Предметов в инвентаре: {len(user['inventory'])} шт."
    )

def crypto_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Купить 1 NC ($100)", callback_data="crypto_buy")],
        [InlineKeyboardButton(text="📉 Продать 1 NC", callback_data="crypto_sell")],
        [InlineKeyboardButton(text="⬅️ Меню", callback_data="main_menu")]
    ])

@dp.message(Command("msg"))
async def admin_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав администратора.")
        return
    text_to_send = message.text.replace("/msg", "").strip()
    if not text_to_send:
        await message.answer("⚠️ Введите текст для рассылки!")
        return
    count = 0
    for uid in users.keys():
        try:
            await bot.send_message(uid, f"📢 Сообщение от администрации:\n\n{text_to_send}")
            count += 1
        except Exception:
            pass
    await message.answer(f"✅ Рассылка завершена. Получателей: {count}")

@dp.message(Command("sup"))
async def support_request(message: types.Message):
    user_id = message.from_user.id
    text = message.text.replace("/sup", "").strip()
    if not text:
        await message.answer("⚠️ Напишите ваше сообщение после команды /sup")
        return
    user = get_user(user_id, message.from_user.first_name)
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"sup_accept_{user_id}"),
            InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"sup_ban_{user_id}")
        ]
    ])
    await bot.send_message(ADMIN_ID, f"📩 Тикет от {user['name']} (ID: {user_id}):\n{text}", reply_markup=admin_kb)
    await message.answer("✅ Отправлено в поддержку!")

@dp.callback_query(F.data.startswith("sup_"))
async def admin_support_actions(cb: types.CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("❌ Доступ запрещен", show_alert=True)
        return
    parts = cb.data.split("_")
    action, target_id = parts[1], int(parts[2])
    if action == "accept":
        await bot.send_message(target_id, "✅ Ваше обращение одобрено админом!")
        await cb.message.edit_text(cb.message.text + "\n\n[Одобрено ✅]")
    elif action == "ban":
        blocked_users.add(target_id)
        await bot.send_message(target_id, "🚫 Вы заблокированы.")
        await cb.message.edit_text(cb.message.text + "\n\n[Заблокирован 🚫]")
    await cb.answer("Готово!")

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    if message.from_user.id in blocked_users:
        await message.answer("❌ Вы заблокированы администратором.")
        return
    user = get_user(message.from_user.id, message.from_user.first_name)
    await message.answer(f"⚡ Здорово, {user['name']}!\n\n{render_card(user)}", reply_markup=main_kb())

@dp.callback_query()
async def callbacks(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    if user_id in blocked_users:
        await cb.answer("❌ Вы заблокированы!", show_alert=True)
        return

    user = get_user(user_id, cb.from_user.first_name)
    data = cb.data
    now = time.time()

    if data == "main_menu":
        await cb.message.edit_text(text=f"🏠 Главное меню\n\n{render_card(user)}", reply_markup=main_kb())
    elif data == "my_card":
        await cb.message.edit_text(text=render_card(user), reply_markup=main_kb())
    elif data == "open_case_menu":
        text = f"📦 ОТКРЫТИЕ КЕЙСОВ\n💰 Цена: ${CASE_PRICE}\n💵 Баланс: ${user['balance']}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🎁 Открыть кейс (${CASE_PRICE})", callback_data="do_open_case")],
            [InlineKeyboardButton(text="⬅️ Меню", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text=text, reply_markup=kb)
    elif data == "do_open_case":
        if user['balance'] < CASE_PRICE:
            await cb.answer("❌ Недостаточно средств!", show_alert=True)
            return
        user['balance'] -= CASE_PRICE
        dropped = random.choices(CASE_ITEMS, weights=[i["chance"] for i in CASE_ITEMS], k=1)[0]
        user['inventory'].append(dropped)
        add_xp(user, 50)
        text = f"🎉 Выпало: {dropped['name']} (${dropped['price']})\n💵 Баланс: ${user['balance']}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 Еще", callback_data="do_open_case")],
            [InlineKeyboardButton(text="⬅️ Меню", callback_data="main_menu")]
        ])
        await cb.message.edit_text(text=text, reply_markup=kb)
    elif data == "start_quiz":
        q = random.choice(QUIZ_QUESTIONS)
        user['current_quiz'] = q
        kb = [[InlineKeyboardButton(text=opt, callback_data=f"q_ans_{i}")] for i, opt in enumerate(q['options'])]
        kb.append([InlineKeyboardButton(text="⬅️ Меню", callback_data="main_menu")])
        await cb.message.edit_text(f"🧠 Квиз: {q['q']}", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    elif data.startswith("q_ans_"):
        idx = int(data.split("_")[2])
        q = user.get('current_quiz')
        if q and idx == q['correct']:
            user['balance'] += q['reward']
            add_xp(user, 40)
            await cb.message.edit_text(f"✅ Верно! +${q['reward']}\n💵 Баланс: ${user['balance']}", reply_markup=back_kb())
        else:
            await cb.message.edit_text(f"❌ Неверно!\n💵 Баланс: ${user['balance']}", reply_markup=back_kb())
    elif data == "inventory":
        inv = "\n".join([f"• {i['name']} (${i['price']})" for i in user['inventory']]) if user['inventory'] else "🎒 Пусто."
        await cb.message.edit_text(f"🎒 Инвентарь:\n\n{inv}", reply_markup=back_kb())
    elif data == "shop":
        kb = [[InlineKeyboardButton(text=f"{i['name']} — ${i['price']}", callback_data=f"buy_{i['id']}")] for i in SHOP_ITEMS]
        kb.append([InlineKeyboardButton(text="⬅️ Меню", callback_data="main_menu")])
        await cb.message.edit_text("🛍️ Магазин:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    elif data.startswith("buy_"):
        item = next((i for i in SHOP_ITEMS if i['id'] == data.split("_")[1]), None)
        if item and user['balance'] >= item['price']:
            user['balance'] -= item['price']
            user['purchases'].append(item['name'])
            await cb.answer("🎉 Куплено!", show_alert=True)
            await cb.message.edit_text(f"🎁 Успешно куплено: {item['name']}!", reply_markup=back_kb())
        else:
            await cb.answer("❌ Не хватает денег!", show_alert=True)
    elif data == "daily":
        if now - user['last_daily'] < 86400:
            left = int(86400 - (now - user['last_daily']))
            h, m = divmod(left // 60, 60)
            await cb.answer(f"⏳ Бонус будет доступен через {h}ч {m}м!", show_alert=True)
            return
        user['last_daily'] = now
        user['daily_streak'] += 1
        reward = 300 * user['daily_streak']
        user['balance'] += reward
        add_xp(user, 30)
        await cb.message.edit_text(f"🎁 Бонус забран! Стрик: {user['daily_streak']} дн.\n💰 Получено: +${reward}\n💵 Баланс: ${user['balance']}", reply_markup=back_kb())
    elif data == "freelance_hub":
        if now < user['freelance_cooldown']:
            left = int(user['freelance_cooldown'] - now)
            m, s = divmod(left, 60)
            await cb.answer(f"⏳ Проект в работе! Подожди еще {m}м {s}с.", show_alert=True)
            return
        user['freelance_cooldown'] = now + COOLDOWN_TIME
        success = random.random() < (0.65 + user['level'] * 0.03)
        if success:
            earned = random.randint(80, 200) * user['level']
            user['balance'] += earned
            levelup = add_xp(user, 60)
            text = f"✅ Проект сдан!\n💰 Награда: +${earned}\n💵 Баланс: ${user['balance']}"
            if levelup:
                text += f"\n🔥 Поздравляем! Уровень повышен до {user['level']}!"
            await cb.message.edit_text(text, reply_markup=back_kb())
        else:
            await cb.message.edit_text("❌ Заказ прогорел! Клиент завернул код.", reply_markup=back_kb())
    elif data == "crypto_hub":
        await cb.message.edit_text(f"📈 Криптобиржа NeoCoin (NC)\n💰 Твой баланс крипты: {user['crypto_balance']:.2f} NC\n💵 Твои USD: ${user['balance']}", reply_markup=crypto_keyboard())
    elif data == "crypto_buy":
        if user['balance'] >= 100:
            user['balance'] -= 100
            user['crypto_balance'] += 1.0
            await cb.answer("Куплено 1 NC!", show_alert=True)
            await cb.message.edit_text(f"📈 Криптобиржа NeoCoin (NC)\n💰 Твой баланс крипты: {user['crypto_balance']:.2f} NC\n💵 Твои USD: ${user['balance']}", reply_markup=crypto_keyboard())
        else:
            await cb.answer("❌ Нужно минимум $100!", show_alert=True)
    elif data == "crypto_sell":
        if user['crypto_balance'] >= 1.0:
            rate = random.randint(70, 160)
            user['crypto_balance'] -= 1.0
            user['balance'] += rate
            await cb.answer(f"Продано за ${rate}!", show_alert=True)
            await cb.message.edit_text(f"📈 Криптобиржа NeoCoin (NC)\n💰 Твой баланс крипты: {user['crypto_balance']:.2f} NC\n💵 Твои USD: ${user['balance']}", reply_markup=crypto_keyboard())
        else:
            await cb.answer("❌ У тебя нет крипты NC!", show_alert=True)

@app.on_event("startup")
async def on_startup():
    webhook_path = f"/webhook/{TOKEN}"
    full_url = f"{WEBHOOK_URL}{webhook_path}"
    await bot.set_webhook(full_url)

@app.post(f"/webhook/{{token}}")
async def handle_webhook(token: str, request: Request):
    if token != TOKEN:
        return {"error": "Invalid token"}
    update = types.Update(**await request.json())
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/")
async def index():
    return {"status": "NeoCard Bot is running 24/7!"}
