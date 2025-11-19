import re
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import BaseFilter

API_TOKEN = "8208867869:AAHsSu-TgJsjoXMkdyRMQQON37Z3em2Dw3A"
CHANNEL_ID = -1002245865369  # ID каналу svitlobot_kiltseva14

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

processed_messages = set()  # щоб не дублювати повідомлення

# Парсимо часи відключення
def extract_times(text: str):
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

# Відправляємо повідомлення за 10 хв до відключення
async def schedule_alerts(times):
    for start_time in times:
        alert_time = start_time - timedelta(minutes=10)
        now = datetime.now()
        wait_seconds = (alert_time - now).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
            await bot.send_message(
                CHANNEL_ID,
                f"⚡ Увага! Світло вимкнуть о {start_time.strftime('%H:%M')}"
            )

# Фільтр для каналів
class ChannelMessageFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.id == CHANNEL_ID and message.sender_chat is not None

# Обробка нових повідомлень у каналі
@dp.message(ChannelMessageFilter())
async def handle_channel_message(message: types.Message):
    if message.message_id in processed_messages:
        return
    processed_messages.add(message.message_id)
    times = extract_times(message.text)
    if times:
        asyncio.create_task(schedule_alerts(times))

# Перевірка останніх повідомлень на випадок пропуску
async def check_recent_messages():
    last_checked = 0
    while True:
        async for message in bot.get_chat_history(CHANNEL_ID, limit=10):
            if message.message_id > last_checked:
                last_checked = message.message_id
                if message.message_id not in processed_messages:
                    processed_messages.add(message.message_id)
                    times = extract_times(message.text)
                    if times:
                        asyncio.create_task(schedule_alerts(times))
        await asyncio.sleep(600)  # перевірка раз на 10 хв

# Запуск бота
async def main():
    asyncio.create_task(check_recent_messages())
    print("Бот запущено...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
