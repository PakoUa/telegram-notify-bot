import re
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import BaseFilter

API_TOKEN = "8208867869:AAHsSu-TgJsjoXMkdyRMQQON37Z3em2Dw3A"
CHANNEL_ID = -1002245865369  # ID каналу svitlobot_kiltseva14

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

processed_messages = set()  # для унікальності повідомлень

# -------------------------------
# Скидання Webhook та старих оновлень
# -------------------------------
async def reset_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook видалено, старі оновлення очищені")
    await bot.session.close()

# -------------------------------
# Парсинг часу відключень
# -------------------------------
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

# -------------------------------
# Відправка попереджень за 10 хв
# -------------------------------
async def schedule_alerts(times):
    for start_time in times:
        alert_time = start_time - timedelta(minutes=10)
        wait_seconds = (alert_time - datetime.now()).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
            await bot.send_message(
                CHANNEL_ID,
                f"⚡ Увага! Світло вимкнуть о {start_time.strftime('%H:%M')}"
            )

# -------------------------------
# Фільтр для каналу
# -------------------------------
class ChannelMessageFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.id == CHANNEL_ID and message.sender_chat is not None

# -------------------------------
# Обробка нових повідомлень
# -------------------------------
@dp.message(ChannelMessageFilter())
async def handle_channel_message(message: types.Message):
    if message.message_id in processed_messages:
        return
    processed_messages.add(message.message_id)
    times = extract_times(message.text)
    if times:
        asyncio.create_task(schedule_alerts(times))

# -------------------------------
# Основний запуск бота
# -------------------------------
async def main():
    # Скидаємо Webhook і старі оновлення перед стартом polling
    await reset_bot()
    print("Бот запущено, слухаємо нові повідомлення...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
