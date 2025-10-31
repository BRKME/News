#!/usr/bin/env python3
import asyncio
from datetime import date, datetime
import pandas as pd
import pytz
import requests
from bs4 import BeautifulSoup
from telegram import Bot

# Telegram configuration (hardcoded as requested)
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

def fetch_us_events():
    """Скрейпим события США с TradingEconomics"""
    try:
        today_str = date.today().strftime("%Y-%m-%d")
        url = f"https://tradingeconomics.com/united-states/calendar?date={today_str}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        events = []
        
        # Парсим таблицу (структура TradingEconomics: rows с классом 'calendar__row')
        rows = soup.find_all('tr', class_='calendar__row')
        for row in rows:
            country = row.find('span', class_='calendar__country')
            if country and ('United States' in country.text or 'USD' in country.text):
                time_el = row.find('time', class_='calendar__time')
                event_el = row.find('span', class_='calendar__event')
                forecast_el = row.find('span', class_='calendar__forecast')
                previous_el = row.find('span', class_='calendar__previous')
                impact_el = row.find('span', class_='calendar__impact')
                
                time = time_el.text.strip() if time_el else 'TBD'
                event = event_el.text.strip() if event_el else 'Unknown'
                forecast = forecast_el.text.strip() if forecast_el else ''
                previous = previous_el.text.strip() if previous_el else ''
                impact = impact_el.get('data-impact', 'medium') if impact_el else 'medium'  # high/medium/low
                
                events.append({
                    'time': time,
                    'event': event,
                    'forecast': forecast,
                    'previous': previous,
                    'impact': impact
                })
        
        print(f"Получено US событий: {len(events)}")
        return events
    except Exception as e:
        print(f"Ошибка скрейпинга: {e}")
        return []

def convert_to_msk_time(time_str):
    """Конвертируем время из EST в MSK (+8 часов)"""
    if time_str in ['TBD', 'All Day', 'Tentative', '']:
        return 'TBD'
    
    try:
        # Парсим как HH:MM AM/PM
        dt = datetime.strptime(time_str, '%I:%M %p')
        est_tz = pytz.timezone('US/Eastern')
        msk_tz = pytz.timezone('Europe/Moscow')
        
        est_dt = est_tz.localize(dt.replace(year=date.today().year, month=date.today().month, day=date.today().day))
        msk_dt = est_dt.astimezone(msk_tz)
        return msk_dt.strftime('%H:%M')
    except:
        try:
            dt = datetime.strptime(time_str, '%H:%M')
            # Если 24h формат, +8 часов просто
            hour = dt.hour + 8
            if hour >= 24: hour -= 24
            return f"{hour:02d}:{dt.minute:02d}"
        except:
            return time_str

def format_events(events):
    """Форматируем список событий в текст для Telegram"""
    if not events:
        return "📅 <b>Сегодня экономических событий США нет.</b>\n\n💡 <i>Обычно важные: NFP, CPI, FOMC, ВВП.</i>"
    
    # Фильтруем будущие события и сортируем по времени
    msk_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(msk_tz).time()
    
    filtered_events = []
    for ev in events:
        time_str = convert_to_msk_time(ev.get('time', '00:00'))
        try:
            event_time = datetime.strptime(time_str, '%H:%M').time()
            if event_time >= now:
                ev['time'] = time_str  # Обновляем на MSK
                filtered_events.append(ev)
        except:
            ev['time'] = time_str
            filtered_events.append(ev)
    
    filtered_events.sort(key=lambda ev: datetime.strptime(ev.get('time', '00:00'), '%H:%M'))
    
    if not filtered_events:
        return "📅 <b>Сегодня нет предстоящих событий США.</b>"
    
    today = date.today()
    month_ru = {
        'January': 'январь', 'February': 'февраль', 'March': 'март', 'April': 'апрель', 'May': 'май', 'June': 'июнь',
        'July': 'июль', 'August': 'август', 'September': 'сентябрь', 'October': 'октябрь', 'November': 'ноябрь', 'December': 'декабрь'
    }
    month_en = today.strftime('%B')
    month_name = month_ru.get(month_en, month_en)
    
    message = f"""📅 <b>ЭКОНОМИЧЕСКИЕ СОБЫТИЯ США 🇺🇸</b>
📆 <b>Дата: {today.strftime('%d.%m')}, {month_name}</b>
⏰ <b>Время московское (MSK)</b>

"""
    
    # Группируем по времени
    events_by_time = {}
    for ev in filtered_events:
        time_key = ev.get('time', 'TBD')
        if time_key not in events_by_time:
            events_by_time[time_key] = []
        events_by_time[time_key].append(ev)
    
    sorted_times = sorted(events_by_time.keys(), key=lambda t: datetime.strptime(t, '%H:%M') if t != 'TBD' else datetime.max)
    
    for i, time_str in enumerate(sorted_times):
        time_events = events_by_time[time_str]
        if i > 0:
            message += "────────────────────\n\n"
        
        for ev in time_events:
            impact_map = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            impact = impact_map.get(ev.get('impact', 'medium'), '🟡')
            
            message += f"{impact} <b>{time_str}</b>\n"
            message += f"   {ev.get('event', 'Unknown event')}\n"
            
            forecast = ev.get('forecast', '')
            if forecast:
                message += f"   Прогноз: {forecast}\n"
            previous = ev.get('previous', '')
            if previous:
                message += f"   Предыдущее: {previous}\n"
    
    message += "\n💡 <i>Время из EST в MSK (+8 ч). Данные: TradingEconomics</i>"
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
    print("=== US ECONOMIC EVENTS BOT ===")
    print(f"Дата: {date.today().strftime('%d.%m.%Y')}")
    
    try:
        events = await asyncio.to_thread(fetch_us_events)
        message = format_events(events)
        print("Отправляем в Telegram...")
        await send_telegram_message(message)
    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
