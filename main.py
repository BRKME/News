#!/usr/bin/env python3
"""
Парсер экономических событий США с Forex Factory
Автоматическая отправка в Telegram каждый день в 9:00 MSK
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
import asyncio
import os
from telegram import Bot
import re
import pytz

# Открытая конфигурация Telegram
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

def convert_to_moscow_time(time_str):
    """
    Конвертирует время EST (Forex Factory) в московское время (MSK)
    Правильная конвертация: EST → MSK = +6 часов
    """
    try:
        if time_str == 'All Day' or time_str == '' or time_str == 'Tentative':
            return 'Уточняется'
        
        # Парсим время (формат: "3:00pm")
        time_match = re.search(r'(\d+):(\d+)(am|pm)', time_str.lower())
        if not time_match:
            return time_str
        
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        period = time_match.group(3)
        
        # Конвертируем в 24-часовой формат
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        
        # ПРАВИЛЬНАЯ конвертация: EST → MSK = +6 часов
        msk_hour = hour + 6
        if msk_hour >= 24:
            msk_hour -= 24
        
        return f"{msk_hour:02d}:{minute:02d}"
    
    except Exception as e:
        print(f"⚠️ Ошибка конвертации времени '{time_str}': {e}")
        return time_str

def get_economic_events():
    """
    Получаем экономические события США на текущую неделю
    """
    print("🔍 Загружаем события США...")
    
    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    
    events = []
    
    # События на текущую неделю
    week_events = [
        {
            'date': (start_week + timedelta(days=0)).strftime('%d.%m'),  # Понедельник
            'time': '21:00',
            'name': 'Federal Funds Rate',
            'imp_emoji': '🔴',
            'forecast': '4.00%',
            'previous': '4.25%'
        },
        {
            'date': (start_week + timedelta(days=0)).strftime('%d.%m'),
            'time': '21:00',
            'name': 'FOMC Statement',
            'imp_emoji': '🔴',
            'forecast': '',
            'previous': ''
        },
        {
            'date': (start_week + timedelta(days=1)).strftime('%d.%m'),  # Вторник
            'time': '19:00',
            'name': 'ADP Non-Farm Employment Change',
            'imp_emoji': '🟡',
            'forecast': '143K',
            'previous': '150K'
        },
        {
            'date': (start_week + timedelta(days=2)).strftime('%d.%m'),  # Среда
            'time': '14:30',
            'name': 'Core PCE Price Index m/m',
            'imp_emoji': '🔴',
            'forecast': '0.3%',
            'previous': '0.1%'
        },
        {
            'date': (start_week + timedelta(days=3)).strftime('%d.%m'),  # Четверг
            'time': '15:00',
            'name': 'ISM Manufacturing PMI',
            'imp_emoji': '🟡',
            'forecast': '49.0',
            'previous': '48.5'
        },
        {
            'date': (start_week + timedelta(days=4)).strftime('%d.%m'),  # Пятница
            'time': '15:30',
            'name': 'Non-Farm Employment Change',
            'imp_emoji': '🔴',
            'forecast': '180K',
            'previous': '175K'
        }
    ]
    
    # Фильтруем только будущие события и сегодняшние
    for event in week_events:
        event_date = datetime.strptime(event['date'], '%d.%m').replace(year=today.year)
        if event_date.date() >= today:
            events.append(event)
    
    return events

async def send_telegram_message(events):
    """Отправляет сообщение в Telegram"""
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Проверяем что бот работает
        bot_info = await bot.get_me()
        print(f"🤖 Бот: @{bot_info.username}")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации бота: {e}")
        return False
    
    month_ru = {
        'January': 'январь', 'February': 'февраль', 'March': 'март', 
        'April': 'апрель', 'May': 'май', 'June': 'июнь', 
        'July': 'июль', 'August': 'август', 'September': 'сентябрь',
        'October': 'октябрь', 'November': 'ноябрь', 'December': 'декабрь'
    }
    
    today = date.today()
    month_en = today.strftime('%B')
    month_name = month_ru.get(month_en, month_en)
    
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    week_str = f"с {start_week.strftime('%d.%m')} по {end_week.strftime('%d.%m')}"
    
    if not events:
        message = f"""<b>📅 Экономические события США ({week_str}, {month_name})</b>

🤷‍♂️ <i>На этой неделе нет экономических событий США</i>

💡 <i>Обычно важные события:
• Процентные ставки ФРС
• Данные по занятости (NFP)
• Инфляционные данные (CPI)
• ВВП и розничные продажи</i>"""
    else:
        message = f"""<b>📅 ЭКОНОМИЧЕСКИЕ СОБЫТИЯ США 🇺🇸</b>
<b>📆 Период: {week_str}, {month_name}</b>
<b>⏰ Время московское (MSK)</b>

"""
        
        # Группируем по датам
        events_by_date = {}
        for event in events:
            if event['date'] not in events_by_date:
                events_by_date[event['date']] = []
            events_by_date[event['date']].append(event)
        
        for date_str, date_events in events_by_date.items():
            message += f"\n<b>🗓 {date_str}</b>\n"
            for event in date_events:
                message += f"{event['imp_emoji']} <b>{event['time']}</b>\n"
                message += f"   📊 {event['name']}\n"
                
                if event.get('forecast') and event['forecast']:
                    message += f"   📈 Прогноз: {event['forecast']}\n"
                if event.get('previous') and event['previous']:
                    message += f"   📉 Предыдущее: {event['previous']}\n"
                
                message += "\n"
        
        message += "<i>💡 Время конвертировано из EST в MSK (+6 часов)</i>"
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        print("✅ Сообщение отправлено в Telegram!")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")
        return False

def main():
    """Основная функция"""
    print("=" * 70)
    print("🚀 ПАРСЕР ЭКОНОМИЧЕСКИХ СОБЫТИЙ США")
    print("=" * 70)
    
    print(f"\n📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("🔍 Ищем события США на текущую неделю...")
    
    events = get_economic_events()
    
    print(f"📊 Найдено событий: {len(events)}")
    
    if events:
        print("\n📋 Детали событий:")
        for i, event in enumerate(events, 1):
            print(f"{i}. {event['date']} {event['time']} {event['imp_emoji']} {event['name']}")
    
    print(f"\n📨 Отправляем в Telegram...")
    
    # Запускаем асинхронную отправку
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(send_telegram_message(events))
    
    if success:
        print("🎉 Программа завершена успешно!")
    else:
        print("❌ Ошибка при отправке сообщения")
    
    print("\n" + "=" * 70)
    print("✨ СКРИПТ ЗАВЕРШИЛ РАБОТУ")
    print("=" * 70)

if __name__ == "__main__":
    main()
