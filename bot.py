import os
import re
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = -1002245865369   # Твой канал

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()


# =========================
# МЕНЮ
# =========================
def main_menu():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📅 Показать расписание", callback_data="show_schedule"))
    keyboard.add(types.InlineKeyboardButton("🔧 Помощь", callback_data="help"))
    return keyboard

@dp.message_handler(commands=["start", "menu"])
async def start_cmd(message: types.Message):
    await message.answer(
        "Меню бота 👇\nВыберите действие:",
        reply_markup=main_menu()
    )


# =========================
# ПАРСИНГ РАСПИСАНИЯ
# =========================

# ищем строки вида "09:30 до 13:30"
pattern = r"(\d{2}:\d{2})\s*до\s*(\d{2}:\d{2})"

# Храним расписание здесь
schedule_list = []


# =========================
# Запуск уведомления
# =========================
async def send_notification(start_time):
    await bot.send_message(
        CHANNEL_ID,
        f"⚠️ *Нагадування!* ⚡️\n"
        f"Через 10 хвилин почнеться відключення світла.\n"
        f"⏰ Початок: *{start_time}*",
        parse_mode="Markdown"
    )


def schedule_event(start_time):
    now = datetime.now()
    event_time = datetime.strptime(start_time, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )

    # якщо час вже минув – на завтра
    if event_time < now:
        event_time += timedelta(days=1)

    notify_time = event_time - timedelta(minutes=10)

    scheduler.add_job(
        send_notification,
        "date",
        run_date=notify_time,
        args=[start_time]
    )

    schedule_list.append(start_time)


# =========================
# ОБРАБОТКА сообщений из канала
# =========================
@dp.message_handler(content_types=["text"])
async def handle_messages(message: types.Message):

    # Обрабатываем только канал
    if message.chat.id != CHANNEL_ID:
        return

    text = message.text

    matches = re.findall(pattern, text)

    if matches:
        schedule_list.clear()

        for start, end in matches:
            schedule_event(start)

        await bot.send_message(
            CHANNEL_ID,
            f"📥 Знайдено часові проміжки!\n"
            f"Бот надішле нагадування за 10 хвилин до кожного відключення ⚡️"
        )


# =========================
# МЕНЮ CALLBACK
# =========================
@dp.callback_query_handler(lambda c: True)
async def callbacks(callback: types.CallbackQuery):
    if callback.data == "show_schedule":
        if schedule_list:
            text = "📅 Розклад сьогодні:\n"
            for t in schedule_list:
                text += f"• {t}\n"
        else:
            text = "⛔️ Розклад порожній. Додайте повідомлення в канал."
        await callback.message.answer(text)

    elif callback.data == "help":
        await callback.message.answer(
            "🔧 *Допомога*\n\n"
            "Бот автоматично шукає часи у форматі:\n"
            "`09:30 до 13:30`\n"
            "та надсилає нагадування за 10 хвилин.",
            parse_mode="Markdown"
        )

    await callback.answer()


# =========================
# СТАРТ
# =========================
if __name__ == "__main__":
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)
