import os
import asyncio
import logging
from threading import Thread
from flask import Flask

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN') # Токен будет браться из настроек Render
ADMIN_ID = 780092520  # Твой ID вставлен

VIDEO_URL = "https://i.imgur.com/TX99qbn.mp4"
SUPPORT_USERNAME = "keucu"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
users_db = {}

# --- FSM ---
class DealStates(StatesGroup):
    waiting_item = State()
    waiting_type = State()
    waiting_currency = State()
    waiting_crypto = State()
    waiting_amount = State()

class ProfileStates(StatesGroup):
    waiting_requisites = State()

class AdminStates(StatesGroup):
    waiting_user_id = State()
    waiting_action = State()
    waiting_value = State()

# --- КЛАВИАТУРЫ ---
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤝 Создать сделку", callback_data="menu_create_deal")],
        [InlineKeyboardButton(text="💳 Мои реквизиты", callback_data="menu_reqs"), InlineKeyboardButton(text="👤 Мой профиль", callback_data="menu_profile")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings"), InlineKeyboardButton(text="📋 Команды", callback_data="menu_commands")],
        [InlineKeyboardButton(text="✅ Подтвердить...", callback_data="menu_confirm")],
        [InlineKeyboardButton(text="🆘 Поддержка 24/7", url=f"https://t.me/{SUPPORT_USERNAME}")]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Выдать права / Изменить данные", callback_data="admin_edit_user")]
    ])

def settings_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Изменить реквизиты", callback_data="set_req")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="set_info")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])

def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])

# --- ХЭНДЛЕРЫ ---
@dp.message(CommandStart())
async def start_cmd(message: Message):
    uid = message.from_user.id
    if uid not in users_db:
        users_db[uid] = {"balance": 0, "deals": 0, "reviews": 0, "role": "user", "requisites": "Не указаны"}
    
    text = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "🛡 Надёжный сервис для безопасных сделок!\n"
        "⚙️ Автоматизировано, быстро и без лишних хлопот!\n\n"
        "⚡ <b>Комиссия за услугу: 1%</b>\n"
        "⚡ <b>Поддержка 24/7:</b> @keucu\n\n"
        "🎁 Теперь ваши сделки под защитой! ✅"
    )
    await message.answer_video(video=VIDEO_URL, caption=text, reply_markup=main_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "back_to_menu")
async def back_to_main(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    text = "👋 <b>Главное меню</b>\n\nВыберите нужное действие ниже:"
    await cb.message.answer_video(video=VIDEO_URL, caption=text, reply_markup=main_menu(), parse_mode="HTML")
    await cb.message.delete()
    await cb.answer()

@dp.callback_query(F.data == "menu_profile")
async def profile(cb: CallbackQuery):
    uid = cb.from_user.id
    data = users_db.get(uid, {"balance": 0, "deals": 0, "reviews": 0})
    text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"💰 Баланс: {data['balance']} RUB\n"
        f"📊 Сделок: {data['deals']}\n"
        f"⭐ Отзывов: {data['reviews']}\n"
    )
    await cb.message.answer_video(video=VIDEO_URL, caption=text, reply_markup=back_menu(), parse_mode="HTML")
    await cb.message.delete()
    await cb.answer()

@dp.callback_query(F.data == "menu_commands")
async def commands(cb: CallbackQuery):
    uid = cb.from_user.id
    data = users_db.get(uid, {})
    text = (
        "📋 <b>Доступные команды и статистика:</b>\n\n"
        f"👤 Профиль: /profile\n"
        f"⚙️ Настройки: /settings\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"Сделок: {data.get('deals', 0)}\n"
        f"Отзывов: {data.get('reviews', 0)}\n"
        f"Баланс: {data.get('balance', 0)} RUB\n"
    )
    await cb.message.answer_video(video=VIDEO_URL, caption=text, reply_markup=back_menu(), parse_mode="HTML")
    await cb.message.delete()
    await cb.answer()

@dp.callback_query(F.data == "menu_confirm")
async def confirm_deal_btn(cb: CallbackQuery):
    await cb.message.answer("Для подтверждения сделки перейдите по ссылке, которую вам отправил продавец.", reply_markup=back_menu())
    await cb.answer()

@dp.callback_query(F.data == "menu_reqs")
async def show_requisites(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    reqs = users_db.get(uid, {}).get("requisites", "Не указаны")
    await cb.message.answer(
        f"💳 <b>Ваши реквизиты:</b>\n<code>{reqs}</code>\n\n"
        f"Отправьте новый текст, чтобы изменить их.", 
        reply_markup=back_menu(), parse_mode="HTML"
    )
    await state.set_state(ProfileStates.waiting_requisites)
    await cb.message.delete()
    await cb.answer()

@dp.message(ProfileStates.waiting_requisites)
async def save_requisites(message: Message, state: FSMContext):
    uid = message.from_user.id
    users_db[uid]["requisites"] = message.text
    await message.answer(f"✅ Реквизиты сохранены!\n\n<code>{message.text}</code>", reply_markup=back_menu(), parse_mode="HTML")
    await state.clear()

@dp.callback_query(F.data == "menu_settings")
async def settings(cb: CallbackQuery):
    await cb.message.answer("⚙️ <b>Настройки</b>\nВыберите действие:", reply_markup=settings_menu(), parse_mode="HTML")
    await cb.message.delete()
    await cb.answer()

@dp.callback_query(F.data == "set_req")
async def settings_req(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Введите новые реквизиты:", reply_markup=back_menu())
    await state.set_state(ProfileStates.waiting_requisites)
    await cb.message.delete()
    await cb.answer()

@dp.callback_query(F.data == "set_info")
async def settings_info(cb: CallbackQuery):
    await cb.message.answer("ℹ️ <b>Инструкция:</b>\n\n1. Нажмите «Создать сделку»\n2. Укажите товар\n3. Отправьте ссылку покупателю\n4. Подтвердите выполнение.", reply_markup=back_menu(), parse_mode="HTML")
    await cb.message.delete()
    await cb.answer()

@dp.callback_query(F.data == "menu_create_deal")
async def create_deal(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer_video(video=VIDEO_URL, caption="Что вы предлагаете? (Например: 10 Персиков) 👇", reply_markup=back_menu())
    await state.set_state(DealStates.waiting_item)
    await cb.message.delete()
    await cb.answer()

@dp.message(DealStates.waiting_item)
async def process_item(message: Message, state: FSMContext):
    await state.update_data(item=message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Подарки", callback_data="type_gift")],
        [InlineKeyboardButton(text="➡️ Другие товары", callback_data="type_other")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])
    await message.answer_video(video=VIDEO_URL, caption="? Выберите тип сделки!", reply_markup=kb)
    await state.set_state(DealStates.waiting_type)

@dp.callback_query(F.data.startswith("type_"))
async def process_type(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await cb.message.answer_video(
        video=VIDEO_URL,
        caption="💰 Выберите валюту:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🪙 Криптовалюта", callback_data="curr_crypto")],
            [InlineKeyboardButton(text="💵 Валюта", callback_data="curr_fiat")],
            [InlineKeyboardButton(text="⭐ Звезды", callback_data="curr_stars")],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
        ])
    )
    await state.set_state(DealStates.waiting_currency)
    await cb.answer()

@dp.callback_query(F.data == "curr_crypto")
async def process_crypto(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await cb.message.answer_video(
        video=VIDEO_URL,
        caption="Выберите криптовалюту:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 USDT", callback_data="crypto_usdt"), InlineKeyboardButton(text="💎 TON", callback_data="crypto_ton")],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
        ])
    )
    await state.set_state(DealStates.waiting_crypto)
    await cb.answer()

@dp.callback_query(F.data.startswith("crypto_"))
async def process_amount_prompt(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await cb.message.answer_video(video=VIDEO_URL, caption="Введите сумму в USD (например: 123.4) 👇", reply_markup=back_menu())
    await state.set_state(DealStates.waiting_amount)
    await cb.answer()

@dp.message(DealStates.waiting_amount)
async def finish_deal(message: Message, state: FSMContext):
    data = await state.get_data()
    item = data.get('item')
    amount = message.text
    
    uid = message.from_user.id
    users_db[uid]["deals"] += 1
    
    link = f"https://t.me/{(await bot.get_me()).username}?start=deal_{uid}"
    text = (
        f"⭐ <b>Сделка создана!</b>\n\n"
        f"<b>Товар:</b> {item}\n"
        f"<b>Сумма:</b> {amount} USD\n\n"
        f"🔗 <b>Ссылка для покупателя:</b>\n{link}"
    )
    await message.answer_video(video=VIDEO_URL, caption=text, reply_markup=back_menu(), parse_mode="HTML")
    await state.clear()

@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    uid = message.from_user.id
    data = users_db.get(uid, {"balance": 0, "deals": 0, "reviews": 0})
    text = f"👤 <b>Профиль</b>\n\n🆔 ID: <code>{uid}</code>\n💰 Баланс: {data['balance']}\n📊 Сделок: {data['deals']}\n⭐ Отзывов: {data['reviews']}"
    await message.answer(text, reply_markup=back_menu(), parse_mode="HTML")

@dp.message(Command("settings"))
async def cmd_settings(message: Message):
    await message.answer("⚙️ <b>Настройки</b>\nВыберите действие:", reply_markup=settings_menu(), parse_mode="HTML")

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🛠 <b>Админ-панель</b>\nВыберите действие:", reply_markup=admin_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "admin_edit_user")
async def admin_edit_user(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Введите <b>ID пользователя</b>:\n(Узнать ID можно у @userinfobot)", reply_markup=back_menu())
    await state.set_state(AdminStates.waiting_user_id)
    await cb.answer()

@dp.message(AdminStates.waiting_user_id)
async def admin_get_user(message: Message, state: FSMContext):
    try:
        target_id = int(message.text)
        if target_id not in users_db:
            users_db[target_id] = {"balance": 0, "deals": 0, "reviews": 0, "role": "user", "requisites": "Не указаны"}
            
        await state.update_data(target_id=target_id)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Изменить баланс", callback_data="act_balance")],
            [InlineKeyboardButton(text="📊 Изменить кол-во сделок", callback_data="act_deals")],
            [InlineKeyboardButton(text="⭐ Изменить отзывы", callback_data="act_reviews")],
            [InlineKeyboardButton(text="🛡 Выдать права Админа", callback_data="act_role")],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
        ])
        await message.answer(f"Пользователь {target_id}. Что изменить?", reply_markup=kb)
        await state.set_state(AdminStates.waiting_action)
    except ValueError:
        await message.answer("Ошибка! Введите числовой ID.")

@dp.callback_query(AdminStates.waiting_action, F.data.startswith("act_"))
async def admin_choose_action(cb: CallbackQuery, state: FSMContext):
    action = cb.data.split("_")[1]
    await state.update_data(action=action)
    
    if action == "role":
        data = await state.get_data()
        target_id = data['target_id']
        users_db[target_id]['role'] = "admin"
        await cb.message.answer(f"✅ Пользователю {target_id} выданы права администратора.", reply_markup=back_menu())
        await state.clear()
    else:
        await cb.message.answer("Введите новое значение (число):", reply_markup=back_menu())
        await cb.answer()

@dp.message(AdminStates.waiting_action)
async def admin_set_value(message: Message, state: FSMContext):
    data = await state.get_data()
    target_id = data['target_id']
    action = data['action']
    
    try:
        value = float(message.text)
        if action == "balance":
            users_db[target_id]["balance"] = value
        elif action == "deals":
            users_db[target_id]["deals"] = int(value)
        elif action == "reviews":
            users_db[target_id]["reviews"] = int(value)
            
        await message.answer(f"✅ Данные пользователя {target_id} обновлены!\n{action}: {value}", reply_markup=back_menu())
        await state.clear()
    except ValueError:
        await message.answer("Ошибка! Введите число.")

# --- ЗАПУСК ДЛЯ RENDER (FLASK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_bot():
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    # Запускаем бота в фоне
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    
    # Запускаем Flask, чтобы Render видел активный сервер
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
