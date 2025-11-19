   import os
import re
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ----------------------------
# CONFIG
# ----------------------------
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = -1002245865369  # твой канал

bot = Bot(TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

scheduler = AsyncIOScheduler()

# шаблон "09:30 до 13:30"
pattern = r"(\d{2}:\d{2})\s*до\s*(\d{2}:\d{2})"

schedule_list = []


# ----------------------------
# Меню
# ----------------------------
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Показать расписание", callback_data="show_schedule")],
        [InlineKeyboardButton(text="🔧 Помощь", callback_data="help")],
    ])


@router.message(Command("start"))
@router.message(Command("menu"))
async def cmd_start(message: Message):
    await message.answer("Меню бота 👇", reply_markup=main_menu())


# ----------------------------
# Уведомления
# ----------------------------
async def send_notification(start_time: str):
    await bot.send_message(
        CHANNEL_ID,
        f"⚠️ *Нагадування!*\n"
        f"Незабаром можливо відключення світла згідно графіка.\n"
        f"⏰ Початок: *{start_time}*",
        parse_mode=ParseMode.MARKDOWN
    )


def schedule_event(start_time: str):
    now = datetime.now()

    event_time = datetime.strptime(start_time, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )

    # Если время прошло — на завтра
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


# ----------------------------
# Обработка сообщений из канала
# ----------------------------
@router.message()
async def parse_channel(message: Message):
    # работаем только с каналом
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
            f"Бот надішле нагадування за 10 хвилин ⚡️"
        )


# ----------------------------
# Callbacks
# ----------------------------
@router.callback_query()
async def callbacks(callback: CallbackQuery):

    if callback.data == "show_schedule":
        if schedule_list:
            text = "📅 Поточне розклад:\n"
            for t in schedule_list:
                text += f"• {t}\n"
        else:
            text = "⛔️ Розклад порожній."

        await callback.message.answer(text)

    elif callback.data == "help":
        await callback.message.answer(
            "🔧 *Допомога*\n\n"
            "Бот шукає строки типу `09:30 до 13:30`\n"
            "і надсилає нагадування за 10 хвилин.",
            parse_mode=ParseMode.MARKDOWN
        )

    await callback.answer()


# ----------------------------
# Запуск
# ----------------------------
async def main():
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
