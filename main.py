#!/usr/bin/env python3
"""
US Economic Events Telegram Notifier
Всегда отправляет события: реальные или fallback
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import asyncio
from telegram import Bot
import re

# Telegram configuration
BOT_TOKEN = 'YOUR_BOT_TOKEN'
CHAT_ID = 'YOUR_CHAT_ID'

def convert_to_moscow_time(time_str):
    """Конвертирует время EST -> MSK (+6 часов)"""
    try:
        if not time_str or time_str in ['All Day', 'Tentative', 'TBD']:
            return 'TBD'

        time_match = re.search(r'(\d+):(\d+)(am|pm)?', time_str.lower())
        if not time_match:
            return time_str

        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        period = time_match.group(3) or ''

        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0

        msk_hour = (hour + 6) % 24
        return f"{msk_hour:02d}:{minute:02d}"
    except:
        return time_str

def get_fallback_events():
    """Fallback события на каждый день"""
    today = date.today()
    weekly_events = {
        'Monday': [
            {'time': '14:30', 'name': 'Dallas Fed Manufacturing Index', 'imp_emoji': '🟢'},
            {'time': '16:00', 'name': 'Pending Home Sales', 'imp_emoji': '🟡'},
        ],
        'Tuesday': [
            {'time': '14:30', 'name': 'Redbook Sales Data', 'imp_emoji': '🟢'},
            {'time': '15:00', 'name': 'CB Consumer Confidence', 'imp_emoji': '🔴'},
            {'time': '16:00', 'name': 'API Crude Oil Stocks', 'imp_emoji': '🟡'},
        ],
        'Wednesday': [
            {'time': '14:30', 'name': 'ADP Employment Change', 'imp_emoji': '🔴'},
            {'time': '15:45', 'name': 'Chicago PMI', 'imp_emoji': '🟡'},
            {'time': '16:00', 'name': 'EIA Crude Oil Inventories', 'imp_emoji': '🟡'},
        ],
        'Thursday': [
            {'time': '14:30', 'name': 'Initial Jobless Claims', 'imp_emoji': '🔴'},
            {'time': '15:00', 'name': 'ISM Manufacturing PMI', 'imp_emoji': '🔴'},
            {'time': '16:00', 'name': 'Natural Gas Storage', 'imp_emoji': '🟢'},
        ],
        'Friday': [
            {'time': '14:30', 'name': 'Non-Farm Payrolls', 'imp_emoji': '🔴'},
            {'time': '15:00', 'name': 'Unemployment Rate', 'imp_emoji': '🔴'},
            {'time': '16:00', 'name': 'Baker Hughes Rig Count', 'imp_emoji': '🟢'},
        ]
    }

    events = []
    day_events = weekly_events.get(date.today().strftime('%A'), [])
    common_events = [
        {'time': '19:00', 'name': 'FOMC Member Speech', 'imp_emoji': '🟡'},
        {'time': '20:30', 'name': 'Fed Chair Powell Speech', 'imp_emoji': '🔴'},
    ]
    for e in day_events + common_events:
        events.append({
            'date': date.today().strftime('%d.%m'),
            'time': e['time'],
            'name': e['name'],
            'imp_emoji': e['imp_emoji'],
            'source': 'Fallback'
        })
    return events

def get_us_events():
    """Пробуем реальный парсинг, иначе fallback"""
    # Пока парсер отключаем, всегда fallback
    events = get_fallback_events()
    return events

async def send_telegram(events):
    """Отправка сообщения в Telegram"""
    bot = Bot(token=BOT_TOKEN)

    today = date.today()
    month_ru = {
        'January':'январь','February':'февраль','March':'март','April':'апрель',
        'May':'май','June':'июнь','July':'июль','August':'август',
        'September':'сентябрь','October':'октябрь','November':'ноябрь','December':'декабрь'
    }
    month_name = month_ru.get(today.strftime('%B'), today.strftime('%B'))

    message = f"<b>📅 ЭКОНОМИЧЕСКИЕ СОБЫТИЯ США 🇺🇸</b>\n<b>📆 Дата: {today.strftime('%d.%m')}, {month_name}</b>\n<b>⏰ Время московское (MSK)</b>\n\n"

    for event in events:
        message += f"{event['imp_emoji']} <b>{event['time']}</b>\n   {event['name']}\n   <i>Источник: {event['source']}</i>\n\n"

    message += "💡 Время конвертировано из EST в MSK (+6 часов)"

    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        print("✅ Message sent to Telegram!")
        return True
    except Exception as e:
        print(f"❌ Telegram sending error: {e}")
        return False

def main():
    events = get_us_events()
    print(f"Found {len(events)} events for today.")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_telegram(events))

if __name__ == "__main__":
    main()
