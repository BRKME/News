#!/usr/bin/env python3
import asyncio
from datetime import datetime, date
import pytz
import feedparser
from telegram import Bot

# Telegram configuration
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

# RSS URL для календаря Investing.com
RSS_URL = 'https://www.investing.com/rss/financial-calendar.rss'

def fetch_rss_events():
    """Получаем события из RSS Investing.com"""
    try:
        feed = feedparser.parse(RSS_URL)
        events = []

        msk_tz = pytz.timezone('Europe/Moscow')
        today = date.today()

        for entry in feed.entries:
            # Дата события в RSS
            if hasattr(entry, 'published_parsed'):
                event_date = datetime(*entry.published_parsed[:6])
            else:
                continue

            # Берём только события на сегодня
            if event_date.date() != today:
                continue

            # Время конвертируем в MSK
            est_tz = pytz.timezone('US/Eastern')
            est_dt = est_tz.localize(event_date)
            msk_dt = est_dt.astimezone(msk_tz)
            time_str = msk_dt.strftime('%H:%M')

            events.append({
                'time': time_str,
                'title': entry.title
            })

        return sorted(events, key=lambda x: x['time'])
    except Exception as e:
        print(f"Ошибка получения RSS: {e}")
        return []

def format_events(events):
    """Форматируем события для Telegram"""
    if not events:
        return "📅 Сегодня экономических событий США нет."

    message = f"📅 <b>ЭКОНОМИЧЕСКИЕ СОБЫТИЯ США 🇺🇸</b>\n"
    message += f"📆 <b>Дата: {date.today().strftime('%d.%m.%Y')}</b>\n"
    message += "⏰ <b>Время московское (MSK)</b>\n\n"

    for ev in events:
        message += f"🟢 <b>{ev['time']}</b> — {ev['title']}\n"

    message += "\n💡 Данные: Investing.com RSS"
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
    print("=== US ECONOMIC EVENTS BOT (RSS) ===")
    try:
        events = await asyncio.to_thread(fetch_rss_events)
        message = format_events(events)
        print(message)
        await send_telegram_message(message)
    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
