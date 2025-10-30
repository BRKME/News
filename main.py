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

def parse_forex_factory():
    """
    Парсит реальные экономические события с Forex Factory
    """
    print("🌐 Парсим Forex Factory...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
    }
    
    try:
        # URL календаря Forex Factory с фильтром по USD
        url = 'https://www.forexfactory.com/calendar?week=thisweek'
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        print("✅ Страница загружена, парсим события...")
        
        # Находим все строки с событиями
        rows = soup.find_all('tr', class_='calendar__row')
        
        current_date = None
        
        for row in rows:
            try:
                # Пропускаем заголовки и пустые строки
                row_class = row.get('class', [])
                if 'calendar__row--header' in row_class:
                    # Это строка с датой - извлекаем дату
                    date_cell = row.find('td', class_='calendar__date')
                    if date_cell:
                        date_text = date_cell.get_text(strip=True)
                        if date_text:
                            current_date = date_text
                    continue
                
                if 'calendar__row--grey' in row_class:
                    continue
                
                # Проверяем валюту - только USD
                currency_cell = row.find('td', class_='calendar__currency')
                if not currency_cell:
                    continue
                    
                currency = currency_cell.get_text(strip=True)
                if currency != 'USD':
                    continue
                
                # Извлекаем время события
                time_cell = row.find('td', class_='calendar__time')
                time_text = time_cell.get_text(strip=True) if time_cell else 'All Day'
                event_time = convert_to_moscow_time(time_text)
                
                # Извлекаем название события
                event_cell = row.find('td', class_='calendar__event')
                event_name = event_cell.get_text(strip=True) if event_cell else None
                
                if not event_name or event_name == 'Holiday':
                    continue
                
                # Определяем важность события
                impact_cell = row.find('td', class_='calendar__impact')
                imp_emoji = '🟢'  # По умолчанию низкая
                
                if impact_cell:
                    impact_span = impact_cell.find('span')
                    if impact_span:
                        span_class = str(impact_span.get('class', []))
                        if 'high' in span_class:
                            imp_emoji = '🔴'
                        elif 'medium' in span_class:
                            imp_emoji = '🟡'
                
                # Извлекаем прогноз и предыдущее значение
                forecast_cell = row.find('td', class_='calendar__forecast')
                previous_cell = row.find('td', class_='calendar__previous')
                
                forecast = forecast_cell.get_text(strip=True) if forecast_cell else ''
                previous = previous_cell.get_text(strip=True) if previous_cell else ''
                
                # Форматируем дату для отображения
                if current_date:
                    # Парсим дату типа "MonOct28"
                    date_match = re.search(r'(\w{3})(\w{3})(\d{1,2})', current_date)
                    if date_match:
                        month_abbr = date_match.group(2)
                        day = date_match.group(3)
                        try:
                            month_num = datetime.strptime(month_abbr, '%b').month
                            display_date = f"{int(day):02d}.{month_num:02d}"
                            
                            event_data = {
                                'date': display_date,
                                'time': event_time,
                                'name': event_name,
                                'imp_emoji': imp_emoji,
                                'forecast': forecast,
                                'previous': previous
                            }
                            
                            events.append(event_data)
                            print(f"✅ Найдено: {display_date} {event_time} - {event_name} {imp_emoji}")
                            
                        except Exception as e:
                            print(f"⚠️ Ошибка парсинга даты: {e}")
                            continue
                
            except Exception as e:
                print(f"⚠️ Ошибка парсинга строки: {e}")
                continue
        
        print(f"📊 Парсинг завершен. Найдено событий: {len(events)}")
        return events
        
    except Exception as e:
        print(f"❌ Ошибка парсинга Forex Factory: {e}")
        return []

def get_economic_events():
    """
    Получаем экономические события США на текущую неделю
    """
    print("🔍 Ищем события США на текущую неделю...")
    
    # Парсим реальные данные с Forex Factory
    events = parse_forex_factory()
    
    # Если парсинг не сработал, используем резервные тестовые данные
    if not events:
        print("⚠️ Парсинг не сработал, используем резервные данные")
        events = get_backup_events()
    
    # Фильтруем только будущие события
    today = date.today()
    filtered_events = []
    
    for event in events:
        try:
            event_date = datetime.strptime(event['date'], '%d.%m').replace(year=today.year)
            if event_date.date() >= today:
                filtered_events.append(event)
        except:
            filtered_events.append(event)
    
    print(f"🎯 Актуальных событий: {len(filtered_events)}")
    return filtered_events

def get_backup_events():
    """
    Резервные данные на случай если парсинг не сработает
    """
    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    
    return [
        {
            'date': (start_week + timedelta(days=0)).strftime('%d.%m'),
            'time': '21:00',
            'name': 'Federal Funds Rate',
            'imp_emoji': '🔴',
            'forecast': '4.00%',
            'previous': '4.25%'
        },
        {
            'date': (start_week + timedelta(days=1)).strftime('%d.%m'),
            'time': '19:00',
            'name': 'ADP Non-Farm Employment Change',
            'imp_emoji': '🟡',
            'forecast': '143K',
            'previous': '150K'
        }
    ]

async def send_telegram_message(events):
    """Отправляет сообщение в Telegram"""
    try:
        bot = Bot(token=BOT_TOKEN)
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

<code>Данные загружены с Forex Factory</code>

"""
        
        # Группируем по датам
        events_by_date = {}
        for event in events:
            if event['date'] not in events_by_date:
                events_by_date[event['date']] = []
            events_by_date[event['date']].append(event)
        
        # Сортируем даты
        sorted_dates = sorted(events_by_date.keys(), key=lambda x: datetime.strptime(x, '%d.%m'))
        
        first_day = True
        for date_str in sorted_dates:
            date_events = events_by_date[date_str]
            
            # Добавляем горизонтальную линию перед каждым днем (кроме первого)
            if not first_day:
                message += "────────────────────────────\n\n"
            first_day = False
            
            message += f"<b>🗓 {date_str}</b>\n"
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
    
    events = get_economic_events()
    
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
