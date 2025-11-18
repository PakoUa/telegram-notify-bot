import re
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

TIME_REGEX = r"(\d{1,2}:\d{2})"

async def schedule_notifications(message: types.Message):
    text = message.text
    times = re.findall(TIME_REGEX, text)
    if not times:
        return

    now = datetime.now()

    for t in times:
        event_time = datetime.strptime(t, "%H:%M").replace(
            year=now.year,
            month=now.month,
            day=now.day
        )

        if event_time < now:
            event_time += timedelta(days=1)

        notify_time = event_time - timedelta(minutes=10)

        scheduler.add_job(
            send_notification,
            trigger=DateTrigger(run_date=notify_time),
            kwargs={"event_time": t},
        )

async def send_notification(event_time: str):
    await bot.send_message(
        CHANNEL_ID,
        f"⏰ Через 10 минут событие в {event_time}!"
    )

@dp.message()
async def catch_new_messages(message: types.Message):
    # Автоматическое отслеживание новых сообщений
    if message.chat.id == int(CHANNEL_ID):
        if message.text:
            await schedule_notifications(message)

async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
