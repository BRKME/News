#!/usr/bin/env python3
import asyncio
from datetime import date
from market_calendar_tool import MarketCalendarTool
from telegram import Bot

# Telegram configuration
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

async def fetch_us_events():
    """Получаем события США на сегодня через MarketCalendarTool"""
    try:
        mct = MarketCalendarTool()
        today_str = date.today().strftime("%Y-%m-%d")
        events = await mct.get_calendar(
            country="United States",
            start_date=today_str,
            end_date=today_str
        )
        return events
    except Exception as e:
        print(f"Ошибка при получении календаря: {e}")
        return []

def format_events(events):
    """Форматируем список событий в текст для Telegram"""
    if not events:
        return "📅 Сегодня экономических событий США нет."
    
    message = "📅 <b>Экономические события США на сегодня</b>\n\n"
    for ev in events:
        time = ev.get('time', 'TBD')
        name = ev.get('name', 'Unknown event')
        impact = ev.get('impact', '🟡')
        message += f"{impact} <b>{time}</b> — {name}\n"
    return message

async def send_telegram_message(text):
    """Отправка сообщения в Telegram"""
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')
        print("✅ Сообщение отправлено в Telegram")
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

async def main():
    print("Получаем события США...")
    events = await fetch_us_events()
    message = format_events(events)
    print("Отправляем в Telegram...")
    await send_telegram_message(message)

if __name__ == "__main__":
    asyncio.run(main())
