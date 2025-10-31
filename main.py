#!/usr/bin/env python3
import asyncio
import feedparser
from datetime import datetime
import pytz
from telegram import Bot

# ---------------- Telegram Configuration ----------------
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

# ---------------- RSS Feed Configuration ----------------
RSS_URL = "https://www.investing.com/rss/financial-calendar"

# ---------------- Functions ----------------
def fetch_us_events():
    """
    Получаем события США из RSS Investing.com
    """
    try:
        feed = feedparser.parse(RSS_URL)
        events = []

        for entry in feed.entries:
            title = entry.title
            summary = entry.summary
            link = entry.link
            # Попробуем фильтровать только США
            if 'US' in title or 'United States' in title:
                # В RSS нет точного времени, берём опубликованное время
                published = entry.get('published', '')
                if published:
                    try:
                        dt = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %Z')
                        est_tz = pytz.timezone('US/Eastern')
                        dt_est = est_tz.localize(dt)
                        msk_tz = pytz.timezone('Europe/Moscow')
                        dt_msk = dt_est.astimezone(msk_tz)
                        time_str = dt_msk.strftime('%H:%M')
                    except Exception:
                        time_str = published
                else:
                    time_str = 'TBD'

                events.append({
                    'time': time_str,
                    'event': title,
                    'summary': summary,
                    'link': link
                })
        return events
    except Exception as e:
        print(f"Ошибка при получении RSS: {e}")
        return []

def format_events(events):
    """
    Форматируем список событий для Telegram
    """
    if not events:
        return "📅 Сегодня экономических событий США нет."

    events.sort(key=lambda x: x.get('time', 'TBD'))

    message = "📅 <b>ЭКОНОМИЧЕСКИЕ СОБЫТИЯ США 🇺🇸</b>\n\n"
    for ev in events:
        message += f"⏰ <b>{ev.get('time')}</b>\n"
        message += f"   {ev.get('event')}\n"
        if ev.get('summary'):
            message += f"   {ev.get('summary')}\n"
        if ev.get('link'):
            message += f"   🔗 <a href='{ev.get('link')}'>Подробнее</a>\n"
        message += "────────────────────\n"

    return message

async def send_telegram_message(text):
    """
    Отправка сообщения в Telegram
    """
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML', disable_web_page_preview=False)
        print("✅ Сообщение отправлено в Telegram")
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

# ---------------- Main ----------------
async def main():
    print("=== US ECONOMIC EVENTS BOT ===")
    events = await asyncio.to_thread(fetch_us_events)
    message = format_events(events)
    await send_telegram_message(message)

if __name__ == "__main__":
    asyncio.run(main())
