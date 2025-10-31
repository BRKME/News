#!/usr/bin/env python3
import asyncio
from datetime import date, datetime
import pytz
import requests
from bs4 import BeautifulSoup
from telegram import Bot

# Telegram configuration (hardcoded as requested)
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

def fetch_us_events():
    """Скрейпим события США с TradingEconomics (исправленный парсер)"""
    try:
        today_str = date.today().strftime("%Y-%m-%d")
        url = f"https://tradingeconomics.com/united-states/calendar?date={today_str}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        events = []
        
        # Находим таблицу календаря и строки <tr>
        table = soup.find('table', class_='table')
        if not table:
            return events
        
        rows = table.find_all('tr')[1:]  # Пропускаем header
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 5:
                continue
            
            # Фильтр по стране: img с флагом США (src содержит 'us.png' или 'united-states')
            country_cell = cells[1]  # Вторая td — страна
            country_img = country_cell.find('img')
            if not country_img or 'us.png' not in country_img.get('src', '') and 'united-states' not in country_img.get('src', ''):
                continue
            
            time_cell = cells[0].text.strip()  # Первая td — время (e.g., "01:30 PM")
            event_cell = cells[2].text.strip()  # Третья — событие
            forecast_cell = cells[3].text.strip() if len(cells) > 3 else ''  # Четвёртая — прогноз
            previous_cell = cells[4].text.strip() if len(cells) > 4 else ''  # Пятая — предыдущее
            impact_cell = cells[2].find('span', class_='pull-right')  # Impact в event-cell (bull/bear icons)
            impact = 'high' if impact_cell and 'bull' in impact_cell.get('class', []) else 'medium' if impact_cell else 'low'
            
            events.append({
                'time': time_cell,
                'event': event_cell,
                'forecast': forecast_cell,
                'previous': previous_cell,
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
        # Парсим 12h формат (e.g., "01:30 PM")
        dt = datetime.strptime(time_str, '%I:%M %p')
        est_tz = pytz.timezone('US/Eastern')
        msk_tz = pytz.timezone('Europe/Moscow')
        
        est_dt = est_tz.localize(dt.replace(year=date.today().year, month=date.today().month, day=date.today().day))
        msk_dt = est_dt.astimezone(msk_tz)
        return msk_dt.strftime('%H:%M')
    except ValueError:
        try:
            # Fallback на 24h
            dt = datetime.strptime(time_str, '%H:%M')
            hour = dt.hour + 8
            if hour >= 24:
                hour -= 24
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
                ev['time'] = time_str
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
