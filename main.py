#!/usr/bin/env python3
import asyncio
from datetime import date, datetime
import pandas as pd
import pytz
from market_calendar_tool import scrape_calendar  # Правильный импорт
from telegram import Bot

# Telegram configuration (hardcoded as requested)
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

def fetch_us_events():  # Sync функция, без async
    """Получаем события США на сегодня через market-calendar-tool"""
    try:
        today_str = date.today().strftime("%Y-%m-%d")
        result = scrape_calendar(date_from=today_str, date_to=today_str)  # Скрейпим за сегодня
        events_df = result.base  # Основной DF с событиями
        
        # Фильтр только US событий (колонка 'country' содержит 'USD' или 'United States')
        if isinstance(events_df, pd.DataFrame) and not events_df.empty:
            us_mask = events_df['country'].str.contains('USD|United States', case=False, na=False)
            events_df = events_df[us_mask]
            events = events_df.to_dict('records')
        else:
            events = []
        
        print(f"Получено US событий: {len(events)}")
        return events
    except Exception as e:
        print(f"Ошибка при получении календаря: {e}")
        return []

def convert_to_msk_time(time_str):
    """Конвертируем время из UTC (ForexFactory) в MSK (+3 часа)"""
    if pd.isna(time_str) or time_str in ['TBD', 'All Day', 'Tentative', '']:
        return 'TBD'
    
    try:
        # Парсим как HH:MM (предполагаем UTC)
        dt = datetime.strptime(str(time_str), '%H:%M')
        utc_tz = pytz.UTC
        msk_tz = pytz.timezone('Europe/Moscow')
        
        utc_dt = utc_tz.localize(dt.replace(year=date.today().year, month=date.today().month, day=date.today().day))
        msk_dt = utc_dt.astimezone(msk_tz)
        return msk_dt.strftime('%H:%M')
    except:
        return str(time_str)

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
            # Impact: строка 'high/medium/low' → эмодзи
            impact_str = str(ev.get('impact', 'medium')).lower()
            impact_map = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            impact = impact_map.get(impact_str, '🟡')
            
            message += f"{impact} <b>{time_str}</b>\n"
            message += f"   {ev.get('event', ev.get('name', 'Unknown event'))}\n"
            
            forecast = ev.get('forecast', '')
            if forecast and str(forecast).strip():
                message += f"   Прогноз: {forecast}\n"
            previous = ev.get('previous', '')
            if previous and str(previous).strip():
                message += f"   Предыдущее: {previous}\n"
    
    message += "\n💡 <i>Время из UTC в MSK (+3 ч). Данные: market-calendar-tool (ForexFactory)</i>"
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
        # Оборачиваем sync fetch в async (пакет sync)
        events = await asyncio.to_thread(fetch_us_events)
        message = format_events(events)
        print("Отправляем в Telegram...")
        await send_telegram_message(message)
    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
