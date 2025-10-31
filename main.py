#!/usr/bin/env python3
import asyncio
from datetime import date, datetime
import pandas as pd
import pytz
from market_calendar_tool import MarketCalendarTool
from telegram import Bot

# Telegram configuration (hardcoded as requested)
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

async def fetch_us_events():
    """Получаем события США на сегодня через MarketCalendarTool"""
    try:
        mct = MarketCalendarTool()
        today_str = date.today().strftime("%Y-%m-%d")
        events_df = mct.get_calendar(  # Синхронный вызов, оборачиваем в thread
            country="United States",
            start_date=today_str,
            end_date=today_str
        )
        
        # Конвертируем DataFrame в список dict, если это DataFrame
        if isinstance(events_df, pd.DataFrame) and not events_df.empty:
            events = events_df.to_dict('records')
        else:
            events = []
        
        print(f"Получено событий: {len(events)}")
        return events
    except Exception as e:
        print(f"Ошибка при получении календаря: {e}")
        return []

def convert_to_msk_time(time_str):
    """Конвертируем время из EST в MSK (+8 часов в октябре, без DST)"""
    if time_str in ['TBD', 'All Day', 'Tentative', '']:
        return 'TBD'
    
    try:
        # Парсим как HH:MM
        dt = datetime.strptime(time_str, '%H:%M')
        est_tz = pytz.timezone('US/Eastern')
        msk_tz = pytz.timezone('Europe/Moscow')
        
        est_dt = est_tz.localize(dt.replace(year=date.today().year, month=date.today().month, day=date.today().day))
        msk_dt = est_dt.astimezone(msk_tz)
        return msk_dt.strftime('%H:%M')
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
                ev['time'] = time_str  # Обновляем время на MSK
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
        time_key = ev['time']
        if time_key not in events_by_time:
            events_by_time[time_key] = []
        events_by_time[time_key].append(ev)
    
    sorted_times = sorted(events_by_time.keys(), key=lambda t: datetime.strptime(t, '%H:%M'))
    
    for i, time_str in enumerate(sorted_times):
        time_events = events_by_time[time_str]
        if i > 0:
            message += "────────────────────\n\n"
        
        for ev in time_events:
            impact_map = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            impact = impact_map.get(ev.get('impact', 'medium').lower(), '🟡')
            
            message += f"{impact} <b>{time_str}</b>\n"
            message += f"   {ev.get('event', ev.get('name', 'Unknown event'))}\n"
            
            forecast = ev.get('forecast', '')
            if forecast:
                message += f"   Прогноз: {forecast}\n"
            previous = ev.get('previous', '')
            if previous:
                message += f"   Предыдущее: {previous}\n"
    
    message += "\n💡 <i>Время из EST в MSK (+8 ч). Данные: market-calendar-tool</i>"
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
        # Оборачиваем sync fetch в async thread
        events = await asyncio.to_thread(fetch_us_events)
        message = format_events(events)
        print("Отправляем в Telegram...")
        await send_telegram_message(message)
    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
