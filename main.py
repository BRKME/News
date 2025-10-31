#!/usr/bin/env python3
"""
Реальный парсер US экономических событий для Telegram
Использует market-calendar-tool
"""

from market_calendar_tool import MarketCalendar
import asyncio
from telegram import Bot
from datetime import date, datetime, time as dt_time

# Telegram configuration
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

def convert_to_moscow_time(time_str):
    """
    Конвертирует время в MSK (плюс 6 часов к EST)
    """
    try:
        if not time_str or time_str in ['All Day', 'Tentative', 'TBD']:
            return 'TBD'
        
        # Формат времени: 'HH:MM' или 'HH:MMam/pm'
        import re
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
    
    except Exception as e:
        print(f"Time conversion error: {e}")
        return time_str

def get_us_events():
    """
    Получаем US экономические события на сегодня
    """
    today = date.today()
    mc = MarketCalendar(sites=['ForexFactory'])
    
    # Получаем календарь на сегодня
    df = mc.scrape(start=today, end=today)
    
    if df.empty:
        return df
    
    # Фильтруем только US события
    df_us = df[df['country'].str.lower() == 'us'].copy()
    
    # Конвертируем время в MSK
    df_us['msk_time'] = df_us['time'].apply(convert_to_moscow_time)
    
    # Сортируем по времени
    df_us.sort_values('msk_time', inplace=True)
    
    return df_us

def format_events(events_df):
    """
    Форматируем DataFrame событий для Telegram
    """
    if events_df.empty:
        return "🤷‍♂️ На сегодня нет экономических событий США."
    
    today = date.today()
    message = f"<b>📅 ЭКОНОМИЧЕСКИЕ СОБЫТИЯ США 🇺🇸</b>\n<b>📆 Дата: {today.strftime('%d.%m.%Y')}</b>\n<b>⏰ Время московское (MSK)</b>\n\n"
    
    for _, row in events_df.iterrows():
        importance = row.get('importance', '🟡')
        event_name = row['event']
        time_msk = row['msk_time']
        site = row.get('site', 'Unknown')
        
        message += f"{importance} <b>{time_msk}</b> {event_name}\n"
        message += f"<i>Источник: {site}</i>\n"
        message += "────────────────────\n"
    
    return message

async def send_telegram(message):
    """
    Отправляем сообщение в Telegram
    """
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        print("✅ Message sent to Telegram!")
    except Exception as e:
        print(f"❌ Telegram sending error: {e}")

def main():
    events_df = get_us_events()
    message = format_events(events_df)
    asyncio.run(send_telegram(message))

if __name__ == "__main__":
    main()
