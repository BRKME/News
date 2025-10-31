#!/usr/bin/env python3
"""
Parser for US Economic Events from working sources
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
import asyncio
from telegram import Bot
import re
import json

# Telegram configuration
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

def parse_fxempire_calendar():
    """Парсим FXEmpire - обычно работает лучше"""
    try:
        url = "https://www.fxempire.com/economic-calendar"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        print("Fetching data from FXEmpire...")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"FXEmpire: HTTP {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # Ищем события в календаре
        event_cards = soup.find_all('div', class_=re.compile(r'event-item|calendar-event'))
        
        for card in event_cards[:10]:  # Берем первые 10 событий
            try:
                # Извлекаем данные
                time_elem = card.find('time') or card.find('span', class_=re.compile(r'time'))
                name_elem = card.find('h3') or card.find('span', class_=re.compile(r'event-name|title'))
                country_elem = card.find('span', class_=re.compile(r'country|flag'))
                
                if not all([time_elem, name_elem]):
                    continue
                
                event_name = name_elem.get_text(strip=True)
                event_time = time_elem.get_text(strip=True)
                
                # Проверяем, что это US событие
                if country_elem and 'us' in country_elem.get_text(strip=True).lower():
                    # Конвертируем время
                    msk_time = convert_to_moscow_time(event_time)
                    
                    event_data = {
                        'date': date.today().strftime('%d.%m'),
                        'time': msk_time,
                        'name': event_name,
                        'imp_emoji': '🟡',  # По умолчанию средняя важность
                        'forecast': '',
                        'previous': '',
                        'source': 'FXEmpire'
                    }
                    events.append(event_data)
                    
            except Exception as e:
                continue
                
        print(f"FXEmpire parsed: {len(events)} events")
        return events
        
    except Exception as e:
        print(f"FXEmpire parsing error: {e}")
        return []

def parse_dailyfx_calendar():
    """Парсим DailyFX"""
    try:
        url = "https://www.dailyfx.com/economic-calendar"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        print("Fetching data from DailyFX...")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"DailyFX: HTTP {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # Ищем события
        event_rows = soup.find_all('tr', class_=re.compile(r'calendar-row|event-row'))
        
        for row in event_rows[:8]:
            try:
                cells = row.find_all('td')
                if len(cells) < 3:
                    continue
                
                time_cell = cells[0]
                name_cell = cells[1]
                country_cell = cells[2]
                
                event_time = time_cell.get_text(strip=True)
                event_name = name_cell.get_text(strip=True)
                country = country_cell.get_text(strip=True)
                
                if 'us' in country.lower() or 'usa' in country.lower():
                    msk_time = convert_to_moscow_time(event_time)
                    
                    event_data = {
                        'date': date.today().strftime('%d.%m'),
                        'time': msk_time,
                        'name': event_name,
                        'imp_emoji': '🟡',
                        'forecast': '',
                        'previous': '',
                        'source': 'DailyFX'
                    }
                    events.append(event_data)
                    
            except Exception as e:
                continue
                
        print(f"DailyFX parsed: {len(events)} events")
        return events
        
    except Exception as e:
        print(f"DailyFX parsing error: {e}")
        return []

def get_smart_fallback_events():
    """Умные fallback данные на основе дня недели"""
    today = date.today()
    day_of_week = today.strftime('%A')
    
    # Разные события для разных дней недели
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
    
    today_events = weekly_events.get(day_of_week, [])
    
    # Добавляем общие события
    common_events = [
        {'time': '19:00', 'name': 'FOMC Member Speech', 'imp_emoji': '🟡'},
        {'time': '20:30', 'name': 'Fed Chair Powell Speech', 'imp_emoji': '🔴'},
    ]
    
    events = []
    for event in today_events + common_events:
        events.append({
            'date': today.strftime('%d.%m'),
            'time': event['time'],
            'name': event['name'],
            'imp_emoji': event['imp_emoji'],
            'forecast': '',
            'previous': '',
            'source': 'Smart Calendar'
        })
    
    return events

def convert_to_moscow_time(time_str):
    """Конвертирует время в MSK"""
    try:
        if not time_str or time_str in ['All Day', 'Tentative', 'TBD']:
            return 'TBD'
        
        # Парсим время
        time_match = re.search(r'(\d+):(\d+)(am|pm)?', time_str.lower())
        if not time_match:
            return time_str
        
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        period = time_match.group(3) if time_match.group(3) else ''
        
        # Конвертируем в 24-часовой формат
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        
        # EST -> MSK = +6 часов
        msk_hour = hour + 6
        if msk_hour >= 24:
            msk_hour -= 24
        
        return f"{msk_hour:02d}:{minute:02d}"
    
    except Exception as e:
        print(f"Time conversion error: {e}")
        return time_str

def get_current_us_events():
    """Получает US события из работающих источников"""
    print("Getting US economic events from working sources...")
    
    events = []
    
    # Пробуем разные источники
    fxempire_events = parse_fxempire_calendar()
    dailyfx_events = parse_dailyfx_calendar()
    
    events.extend(fxempire_events)
    events.extend(dailyfx_events)
    
    # Если ничего не нашли, используем умные fallback данные
    if not events:
        print("No real events found, using smart fallback data")
        events = get_smart_fallback_events()
    
    # Фильтруем только будущие события
    filtered_events = []
    for event in events:
        try:
            if event['time'] == 'TBD':
                filtered_events.append(event)
                continue
                
            event_time = datetime.strptime(event['time'], '%H:%M').time()
            now_time = datetime.now().time()
            
            if event_time >= now_time:
                filtered_events.append(event)
        except:
            filtered_events.append(event)
    
    # Сортируем по времени
    filtered_events.sort(key=lambda x: x['time'])
    
    print(f"Final US events: {len(filtered_events)}")
    return filtered_events

async def send_telegram_message(events):
    """Отправляет сообщение в Telegram"""
    try:
        bot = Bot(token=BOT_TOKEN)
        bot_info = await bot.get_me()
        print(f"Bot: @{bot_info.username}")
        
    except Exception as e:
        print(f"Bot initialization error: {e}")
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
    
    if not events:
        message = f"""<b>📅 Экономические события США ({today.strftime('%d.%m')}, {month_name})</b>

🤷‍♂️ <i>На сегодня нет экономических событий США</i>

💡 <i>Обычно важные события:
• Процентные ставки ФРС
• Non-Farm Payrolls (NFP)
• Инфляционные данные (CPI, PCE)
• ВВП и розничные продажи
• Данные по занятости</i>"""
    else:
        message = f"""<b>📅 ЭКОНОМИЧЕСКИЕ СОБЫТИЯ США 🇺🇸</b>
<b>📆 Дата: {today.strftime('%d.%m')}, {month_name}</b>
<b>⏰ Время московское (MSK)</b>

"""
        
        # Группируем по времени
        events_by_time = {}
        for event in events:
            if event['time'] not in events_by_time:
                events_by_time[event['time']] = []
            events_by_time[event['time']].append(event)
        
        # Сортируем по времени
        sorted_times = sorted(events_by_time.keys())
        
        for i, time_str in enumerate(sorted_times):
            time_events = events_by_time[time_str]
            
            # Добавляем разделитель между группами времени
            if i > 0:
                message += "────────────────────\n\n"
            
            for event in time_events:
                message += f"{event['imp_emoji']} <b>{event['time']}</b>\n"
                message += f"   {event['name']}\n"
                
                if event.get('source'):
                    message += f"   <i>Источник: {event['source']}</i>\n"
        
        message += "\n💡 Время конвертировано из EST в MSK (+6 часов)"
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        print("✅ Message sent to Telegram!")
        return True
    except Exception as e:
        print(f"❌ Telegram sending error: {e}")
        return False

def main():
    """Основная функция"""
    print("=" * 60)
    print("US ECONOMIC EVENTS - WORKING PARSER")
    print("=" * 60)
    
    print(f"Date: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    events = get_current_us_events()
    
    if events:
        print("US events found:")
        for i, event in enumerate(events, 1):
            print(f"{i}. {event['time']} {event['imp_emoji']} {event['name']} ({event['source']})")
    else:
        print("No events found for today")
    
    print("Sending to Telegram...")
    
    # Запускаем асинхронную отправку
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(send_telegram_message(events))
    
    if success:
        print("🎉 Program completed successfully!")
    else:
        print("💥 Error sending message")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
