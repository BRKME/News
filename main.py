#!/usr/bin/env python3
"""
Parser for US Economic Events with fallback data
Sends message to Telegram synchronously
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from telegram import Bot
import re

# -------------------------
# Telegram configuration
# -------------------------
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = 350766421  # числовой ID чата
bot = Bot(token=BOT_TOKEN)

# -------------------------
# Вспомогательные функции
# -------------------------
def convert_to_moscow_time(time_str):
    """Конвертирует EST/AMPM время в MSK"""
    try:
        if not time_str or time_str in ['All Day', 'Tentative', 'TBD']:
            return 'TBD'
        
        time_match = re.search(r'(\d+):(\d+)(am|pm)?', time_str.lower())
        if not time_match:
            return time_str
        
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        period = time_match.group(3) if time_match.group(3) else ''
        
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        
        msk_hour = hour + 6
        if msk_hour >= 24:
            msk_hour -= 24
        
        return f"{msk_hour:02d}:{minute:02d}"
    except Exception:
        return time_str

def get_fallback_events():
    """Возвращает fallback события на основе дня недели"""
    today = date.today()
    day = today.strftime('%A')
    weekly_events = {
        'Monday': [
            {'time': '14:30', 'name': 'Dallas Fed Manufacturing Index', 'imp': '🟢'},
            {'time': '16:00', 'name': 'Pending Home Sales', 'imp': '🟡'},
        ],
        'Tuesday': [
            {'time': '14:30', 'name': 'Redbook Sales Data', 'imp': '🟢'},
            {'time': '15:00', 'name': 'CB Consumer Confidence', 'imp': '🔴'},
            {'time': '16:00', 'name': 'API Crude Oil Stocks', 'imp': '🟡'},
        ],
        'Wednesday': [
            {'time': '14:30', 'name': 'ADP Employment Change', 'imp': '🔴'},
            {'time': '15:45', 'name': 'Chicago PMI', 'imp': '🟡'},
            {'time': '16:00', 'name': 'EIA Crude Oil Inventories', 'imp': '🟡'},
        ],
        'Thursday': [
            {'time': '14:30', 'name': 'Initial Jobless Claims', 'imp': '🔴'},
            {'time': '15:00', 'name': 'ISM Manufacturing PMI', 'imp': '🔴'},
            {'time': '16:00', 'name': 'Natural Gas Storage', 'imp': '🟢'},
        ],
        'Friday': [
            {'time': '14:30', 'name': 'Non-Farm Payrolls', 'imp': '🔴'},
            {'time': '15:00', 'name': 'Unemployment Rate', 'imp': '🔴'},
            {'time': '16:00', 'name': 'Baker Hughes Rig Count', 'imp': '🟢'},
        ],
    }
    common_events = [
        {'time': '19:00', 'name': 'FOMC Member Speech', 'imp': '🟡'},
        {'time': '20:30', 'name': 'Fed Chair Powell Speech', 'imp': '🔴'},
    ]
    
    events = []
    for ev in weekly_events.get(day, []) + common_events:
        events.append({
            'date': today.strftime('%d.%m'),
            'time': ev['time'],
            'name': ev['name'],
            'imp_emoji': ev['imp'],
            'source': 'Fallback Calendar'
        })
    return events

# -------------------------
# Формируем и отправляем сообщение
# -------------------------
def send_telegram(events):
    today = date.today()
    month_ru = {
        'January':'январь','February':'февраль','March':'март',
        'April':'апрель','May':'май','June':'июнь',
        'July':'июль','August':'август','September':'сентябрь',
        'October':'октябрь','November':'ноябрь','December':'декабрь'
    }
    month_name = month_ru.get(today.strftime('%B'), today.strftime('%B'))
    
    message = f"<b>📅 ЭКОНОМИЧЕСКИЕ СОБЫТИЯ США 🇺🇸</b>\n<b>📆 Дата: {today.strftime('%d.%m')}, {month_name}</b>\n<b>⏰ Время московское (MSK)</b>\n\n"
    
    for event in events:
        message += f"{event['imp_emoji']} <b>{event['time']}</b> {event['name']} ({event['source']})\n"
    
    message += "\n💡 Время конвертировано из EST в MSK (+6 часов)"
    
    bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
    print("✅ Message sent to Telegram!")

# -------------------------
# Основная функция
# -------------------------
def main():
    print("="*50)
    print("US ECONOMIC EVENTS - FALLBACK PARSER")
    print("="*50)
    
    events = get_fallback_events()
    print(f"Found {len(events)} events for today.")
    
    send_telegram(events)
    print("="*50)

if __name__ == "__main__":
    main()
