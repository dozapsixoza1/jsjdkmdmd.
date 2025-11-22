import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton

# =========================
#   НАСТРОЙКИ БОТА
# =========================
BOT_TOKEN = "8026258910:AAFk_rMamY3IB3-AaLkHEuzVSXuM1pT19Cw"
ADMIN_ID = 7504103313   # Твой Telegram ID
CHATS_FILE = "allowed_chats.txt"


# =========================
#   РАБОТА С ЧАТАМИ
# =========================

def load_chats():
    """Загрузка разрешённых чатов."""
    if not os.path.exists(CHATS_FILE):
        return []
    with open(CHATS_FILE, "r") as f:
        return [int(x.strip()) for x in f.readlines() if x.strip().isdigit()]


def save_chat(chat_id: int):
    """Добавление чата в файл."""
    chats = load_chats()
    if chat_id not in chats:
        with open(CHATS_FILE, "a") as f:
            f.write(str(chat_id) + "\n")


def remove_chat(chat_id: int):
    """Удаление чата из файла."""
    chats = load_chats()
    if chat_id in chats:
        chats.remove(chat_id)
        with open(CHATS_FILE, "w") as f:
            for c in chats:
                f.write(str(c) + "\n")


ALLOWED_CHATS = load_chats()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилища
USER_FORMS = {}
WARNS = {}

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📩 Подать заявку")],
        [KeyboardButton(text="📜 Правила"), KeyboardButton(text="ℹ Информация")],
        [KeyboardButton(text="✉ Связаться с админом")]
    ],
    resize_keyboard=True
)


# =========================
#   ФУНКЦИЯ ПРОВЕРКИ ЧАТА
# =========================
async def check_chat(message: Message):
    """Бот работает только в разрешённых чатах."""
    if message.chat.type == "private":
        return True
    if message.chat.id not in ALLOWED_CHATS:
        return False
    return True


# =========================
#   КОМАНДЫ ДЛЯ АДМИНА
# =========================

@dp.message(Command("addchat"))
async def add_chat(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    chat_id = message.chat.id
    save_chat(chat_id)

    global ALLOWED_CHATS
    ALLOWED_CHATS = load_chats()

    await message.answer(f"✅ Чат {chat_id} добавлен в список разрешённых.")


@dp.message(Command("removechat"))
async def remove_chat_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    chat_id = message.chat.id
    remove_chat(chat_id)

    global ALLOWED_CHATS
    ALLOWED_CHATS = load_chats()

    await message.answer(f"❌ Чат {chat_id} удалён из списка.")


@dp.message(Command("listchats"))
async def list_chats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    chats = load_chats()
    if not chats:
        return await message.answer("❗ Нет добавленных чатов.")

    text = "📋 Разрешённые чаты:\n\n"
    for c in chats:
        text += f"• `{c}`\n"

    await message.answer(text, parse_mode="Markdown")


# =========================
#   START
# =========================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 Привет! Я бот чата. Выбери действие:", reply_markup=main_menu)


# =========================
#   АВТОПРИВЕТСТВИЕ
# =========================

@dp.chat_member()
async def welcome(event):
    if event.new_chat_member and event.new_chat_member.user.id != bot.id:
        await bot.send_message(
            event.chat.id,
            f"👋 Привет, {event.new_chat_member.user.first_name}!\nЧтобы подать заявку — нажми /start"
        )


# =========================
#   ПРАВИЛА
# =========================

@dp.message(F.text == "📜 Правила")
async def rules(message: Message):
    if not await check_chat(message):
        return

    await message.answer(
        "📜 *Правила чата:*\n"
        "1. Не спамить.\n"
        "2. Не рекламировать.\n"
        "3. Уважать участников.",
        parse_mode="Markdown"
    )


# =========================
#   ИНФОРМАЦИЯ
# =========================

@dp.message(F.text == "ℹ Информация")
async def info_chat(message: Message):
    if not await check_chat(message):
        return

    await message.answer("ℹ Чат создан для общения. Ты можешь подать заявку на модератора.")


# =========================
#   СВЯЗЬ С АДМИНОМ
# =========================

@dp.message(F.text == "✉ Связаться с админом")
async def contact_admin(message: Message):
    await message.answer(f"✉ Пиши админу: tg://user?id={ADMIN_ID}")


# =========================
#   ЗАЯВКА
# =========================

@dp.message(F.text == "📩 Подать заявку")
async def start_form(message: Message):
    if not await check_chat(message):
        return

    USER_FORMS[message.from_user.id] = {"step": 1}

    await message.answer("✏ Введи своё имя:")


@dp.message()
async def process_form(message: Message):
    user_id = message.from_user.id

    if user_id not in USER_FORMS:
        return

    step = USER_FORMS[user_id]["step"]

    # Имя
    if step == 1:
        USER_FORMS[user_id]["name"] = message.text
        USER_FORMS[user_id]["step"] = 2
        return await message.answer("🎂 Введи возраст:")

    # Возраст
    if step == 2:
        USER_FORMS[user_id]["age"] = message.text
        USER_FORMS[user_id]["step"] = 3
        return await message.answer("🔗 Введи контакт (Telegram/VK):")

    # Контакт
    if step == 3:
        USER_FORMS[user_id]["contact"] = message.text
        USER_FORMS[user_id]["step"] = 4
        return await message.answer("🛠 На какую должность хочешь? (модератор/админ/редактор)")

    # Должность
    if step == 4:
        USER_FORMS[user_id]["role"] = message.text
        USER_FORMS[user_id]["step"] = 5
        return await message.answer("📚 Опиши свой опыт:")

    # Опыт
    if step == 5:
        USER_FORMS[user_id]["exp"] = message.text
        USER_FORMS[user_id]["step"] = 6
        return await message.answer("💬 Почему выбрать именно тебя?")

    # Причина
    if step == 6:
        USER_FORMS[user_id]["reason"] = message.text

        form = USER_FORMS[user_id]
        del USER_FORMS[user_id]

        text = (
            "📩 *Новая заявка:*\n\n"
            f"👤 Имя: {form['name']}\n"
            f"🎂 Возраст: {form['age']}\n"
            f"🔗 Контакт: {form['contact']}\n"
            f"🛠 Должность: {form['role']}\n"
            f"📚 Опыт: {form['exp']}\n"
            f"💬 Причина: {form['reason']}\n"
            f"🆔 ID: `{user_id}`"
        )

        await bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
        await message.answer("✅ Заявка отправлена!")


# =========================
#   ПРЕДУПРЕЖДЕНИЯ
# =========================

@dp.message(Command("warn"))
async def warn(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.reply_to_message:
        return await message.answer("⚠ Используй команду, отвечая на сообщение.")

    user_id = message.reply_to_message.from_user.id
    WARNS[user_id] = WARNS.get(user_id, 0) + 1

    await message.answer(f"⚠ Предупреждение ({WARNS[user_id]}/3)")

    if WARNS[user_id] >= 3:
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.answer("🚫 Пользователь забанен.")


@dp.message(Command("unwarn"))
async def unwarn(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.reply_to_message:
        return await message.answer("Используй команду ответом.")

    user_id = message.reply_to_message.from_user.id
    WARNS[user_id] = max(WARNS.get(user_id, 0) - 1, 0)

    await message.answer(f"🔄 Предупреждение снижено. Сейчас: {WARNS[user_id]}")


# =========================
#   ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ
# =========================

@dp.message(Command("info"))
async def info_cmd(message: Message):
    if not message.reply_to_message:
        return await message.answer("Ответь на сообщение пользователя.")

    user = message.reply_to_message.from_user
    warns = WARNS.get(user.id, 0)

    await message.answer(
        f"📌 Информация:\n"
        f"👤 {user.full_name}\n"
        f"🆔 {user.id}\n"
        f"⚠ Предупреждений: {warns}"
    )


# =========================
#   ЗАПУСК
# =========================

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
