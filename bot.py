import re
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message

API_TOKEN = "8208867869:AAHsSu-TgJsjoXMkdyRMQQON37Z3em2Dw3A"
CHANNEL_ID = -1002245865369  # ID каналу svitlobot_kiltseva14

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Щоб не дублювати повідомлення
processed_messages = set()

# Витягуємо часи відключення
def extract_times(text):
    times = re.findall(r'з (\d{1,2}:\d{2}) до (\d{1,2}:\d{2})', text)
    result = []
    for start, end in times:
        start_dt = datetime.strptime(start, "%H:%M").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )
        result.append(start_dt)
    return result

# Планування повідомлення
async def schedule_alerts(times):
    for start_time in times:
        alert_time = start_time - timedelta(minutes=10)
        now = datetime.now()
        wait_seconds = (alert_time - now).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
            await bot.send_message(CHANNEL_ID, f"⚡ Увага! Світло вимкнуть о {start_time.strftime('%H:%M')}")

# Ловимо нові повідомлення в каналі
@dp.channel_post_handler()
async def handle_channel_post(message: Message):
    if message.chat.id == CHANNEL_ID:
        if message.message_id in processed_messages:
            return
        processed_messages.add(message.message_id)
        times = extract_times(message.text)
        if times:
            asyncio.create_task(schedule_alerts(times))

# Запуск бота
async def main():
    print("Бот запущено...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
