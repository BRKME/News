#!/usr/bin/env python3
"""
US Economic Events Parser with Telegram notifications
"""

import asyncio
from datetime import datetime, date, time, timedelta
import re

# Telegram
from telegram import Bot

# Market calendar tool
from market_calendar_tool import get_calendar, get_events

# -----------------------------
# Telegram configuration
# -----------------------------
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

# -----------------------------
# Time conversion
# -----------------------------
def convert_est_to_msk(est_time_str: str) -> str:
    """Convert HH:MM EST to MSK"""
    try:
        match = re.match(r'(\d+):(\d+)(am|pm)?', est_time_str.lower())
        if not match:
            return est_time_str
        hour, minute, period = int(match.group(1)), int(match.group(2)), match.group(3)
        if period == 'pm' and hour != 12:
            hour += 12
        if period == 'am' and hour == 12:
            hour = 0
        msk_hour = (hour + 6) % 24
        return f"{msk_hour:02d}:{minute:02d}"
    except:
        return est_time_str

# -----------------------------
# Fetch events from Market Calendar
# -----------------------------
async def fetch_us_events():
    """Fetch US economic events"""
    try:
        # Получаем календарь США
        calendar = await get_calendar('US')
        # Получаем события на сегодня
        events = await get_events(calendar, date.today())
        us_events = []
        for e in events:
            us_events.append({
                'time': convert_est_to_msk(e['time']),
                'name': e['name'],
                'imp_emoji': '🟡',  # Можно добавить реальный уровень важности
                'source': 'MarketCalendarTool'
            })
        return us_events
    except Exception as exc:
        print(f"Error fetching events: {exc}")
        return []

# -----------------------------
# Send message to Telegram
# -----------------------------
async def send_telegram(events):
    bot = Bot(token=BOT_TOKEN)

    today = date.today().strftime('%d.%m.%Y')
    if not events:
        message = f"<b>📅 US Economic Events ({today})</b>\n\n🤷‍♂️ No events today."
    else:
        message = f"<b>📅 US Economic Events ({today})</b>\n\n"
        for e in events:
            message += f"{e['imp_emoji']} <b>{e['time']}</b> - {e['name']} (<i>{e['source']}</i>)\n"

    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        print("✅ Message sent to Telegram")
    except Exception as exc:
        print(f"❌ Telegram send error: {exc}")

# -----------------------------
# Simulation for testing
# -----------------------------
async def test_simulation():
    """Fake events for simulation"""
    fake_events = [
        {'time': '14:30', 'name': 'Redbook Sales Data', 'imp_emoji': '🟢', 'source': 'Simulation'},
        {'time': '15:00', 'name': 'CB Consumer Confidence', 'imp_emoji': '🔴', 'source': 'Simulation'},
        {'time': '16:00', 'name': 'API Crude Oil Stocks', 'imp_emoji': '🟡', 'source': 'Simulation'},
    ]
    await send_telegram(fake_events)

# -----------------------------
# Main
# -----------------------------
async def main():
    print("Fetching US economic events...")
    events = await fetch_us_events()
    
    if not events:
        print("No events fetched. Using simulation for testing...")
        await test_simulation()
    else:
        for i, e in enumerate(events, 1):
            print(f"{i}. {e['time']} {e['imp_emoji']} {e['name']} ({e['source']})")
        await send_telegram(events)

if __name__ == "__main__":
    asyncio.run(main())
