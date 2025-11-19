import os
import re
from datetime import datetime, timedelta
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web
from dotenv import load_dotenv

# ----------------------------
# Налаштування
# ----------------------------
load_dotenv()  # якщо хочеш локально тестувати через .env

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 3000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
CHANNEL_ID = -1002245865369  # змінити на твій канал

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не задано у змінних середовища")
if not WEBHOOK_URL:
    raise ValueError("❌ WEBHOOK_URL не задано у змінних середовища")

WEBHOOK_PATH = f"/webhook/{TOKEN}"

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)
scheduler = AsyncIOScheduler()

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
# Нагадування
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
    if event_time < now:
        event_time += timedelta(days=1)

    notify_time = event_time - timedelta(minutes=10)
    scheduler.add_job(send_notification, "date", run_date=notify_time, args=[start_time])
    schedule_list.append(start_time)

# ----------------------------
# Обробка повідомлень з каналу
# ----------------------------
@router.message()
async def parse_channel(message: Message):
    if message.chat.id != CHANNEL_ID:
        return

    matches = re.findall(pattern, message.text or "")
    if matches:
        schedule_list.clear()
        for start, _ in matches:
            schedule_event(start)

        await bot.send_message(
            CHANNEL_ID,
            "📥 Знайдено часові проміжки!\nБот надішле нагадування за 10 хвилин ⚡️"
        )

# ----------------------------
# Callbacks
# ----------------------------
@router.callback_query()
async def callbacks(callback: CallbackQuery):
    if callback.data == "show_schedule":
        text = "📅 Поточне розклад:\n" + "\n".join(f"• {t}" for t in schedule_list) if schedule_list else "⛔️ Розклад порожній."
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
# Webhook
# ----------------------------
async def handle_webhook(request):
    update = await request.json()
    await dp.feed_update(update)
    return web.Response(status=200)

async def on_startup(app):
    scheduler.start()
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    print(f"✅ Webhook встановлено: {WEBHOOK_URL + WEBHOOK_PATH}")

async def on_cleanup(app):
    await bot.delete_webhook()
    print("🛑 Webhook видалено")

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT)
