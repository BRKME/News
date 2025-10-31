#!/usr/bin/env python3
"""
US Economic Events Parser using market-calendar-tool
"""

import asyncio
from datetime import date
from telegram import Bot
from market_calendar_tool import get_calendar
import pandas as pd

# ------------------ Telegram configuration ------------------
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

# ------------------ Function to fetch US events ------------------
async def fetch_us_events():
    today_str = date.today().strftime("%Y-%m-%d")
    try:
        df: pd.DataFrame = await get_calendar(
            country="united states",
            start_date=today_str,
            end_date=today_str
        )
        # Фильтруем только будущие события по времени (если есть колонка 'time')
        events = []
        now = pd.Timestamp.now()
        for _, row in df.iterrows():
            time_str = str(row.get("time", "TBD"))
            name = row.get("event", "Unknown event")
            if time_str != "TBD":
                try:
                    event_time = pd.to_datetime(f"{today_str} {time_str}")
                    if event_time >= now:
                        events.append({"time": event_time.strftime("%H:%M"), "name": name})
                except:
                    events.append({"time": "TBD", "name": name})
            else:
                events.append({"time": "TBD", "name": name})
        return events
    except Exception as e:
        print(f"Error fetching US events: {e}")
        return []

# ------------------ Function to send Telegram message ------------------
async def send_telegram_message(events):
    bot = Bot(token=BOT_TOKEN)
    if not events:
        message = f"📅 Экономические события США ({date.today().strftime('%d.%m.%Y')})\n\n" \
                  "🤷‍♂️ На сегодня нет событий."
    else:
        message = f"📅 ЭКОНОМИЧЕСКИЕ СОБЫТИЯ США ({date.today().strftime('%d.%m.%Y')})\n\n"
        for ev in events:
            message += f"⏰ {ev['time']} - {ev['name']}\n"
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
        print("✅ Message sent to Telegram!")
    except Exception as e:
        print(f"❌ Telegram sending error: {e}")

# ------------------ Main ------------------
async def main():
    print(f"Fetching US events for {date.today().strftime('%d.%m.%Y')}...")
    events = await fetch_us_events()
    print(f"Found {len(events)} events")
    for ev in events:
        print(f"{ev['time']} - {ev['name']}")
    print("Sending to Telegram...")
    await send_telegram_message(events)

if __name__ == "__main__":
    asyncio.run(main())
