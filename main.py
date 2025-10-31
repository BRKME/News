#!/usr/bin/env python3
import asyncio
from datetime import date, datetime
import pytz
import requests
from bs4 import BeautifulSoup
from telegram import Bot

# -------------------- Telegram --------------------
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

# -------------------- Источник 1: TradingEconomics --------------------
def fetch_te_events():
    try:
        today_str = date.today().strftime("%Y-%m-%d")
        url = f"https://tradingeconomics.com/united-states/calendar?date={today_str}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        events = []
        table = soup.find('table', class_='table')
        if not table: return events

        rows = table.find_all('tr')[1:]
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 5: continue
            country_cell = cells[1]
            country_img = country_cell.find('img')
            if not country_img or ('us.png' not in country_img.get('src', '') and 'united-states' not in country_img.get('src', '')):
                continue

            time_cell = cells[0].text.strip()
            event_cell = cells[2].text.strip()
            forecast_cell = cells[3].text.strip() if len(cells) > 3 else ''
            previous_cell = cells[4].text.strip() if len(cells) > 4 else ''
            impact_cell = cells[2].find('span', class_='pull-right')
            impact = 'high' if impact_cell and 'bull' in impact_cell.get('class', []) else 'medium' if impact_cell else 'low'

            events.append({
                'time': time_cell,
                'event': event_cell,
                'forecast': forecast_cell,
                'previous': previous_cell,
                'impact': impact
            })
        if events: print(f"✅ TradingEconomics: {len(events)} событий")
        return events
    except Exception as e:
        print(f"❌ TE ошибка: {e}")
        return []

# -------------------- Источник 2: MarketCalendarTool --------------------
def fetch_mct_events():
    try:
        from market_calendar_tool import MarketCalendarTool
        cal = MarketCalendarTool()
        events = cal.get_events('US', date.today(), date.today())
        formatted = []
        for e in events:
            formatted.append({
                'time': e.get('time', 'TBD'),
                'event': e.get('name', 'Unknown'),
                'forecast': e.get('forecast', ''),
                'previous': e.get('previous', ''),
                'impact': e.get('impact', 'medium')
            })
        if formatted: print(f"✅ MarketCalendarTool: {len(formatted)} событий")
        return formatted
    except Exception as e:
        print(f"❌ MCT ошибка: {e}")
        return []

# -------------------- Вспомогательные функции --------------------
def convert_to_msk_time(time_str):
    if time_str in ['TBD', 'All Day', 'Tentative', '']:
        return 'TBD'
    try:
        dt = datetime.strptime(time_str, '%I:%M %p')
        est_tz = pytz.timezone('US/Eastern')
        msk_tz = pytz.timezone('Europe/Moscow')
        est_dt = est_tz.localize(dt.replace(year=date.today().year, month=date.today().month, day=date.today().day))
        msk_dt = est_dt.astimezone(msk_tz)
        return msk_dt.strftime('%H:%M')
    except:
        return time_str

def format_events(events):
    if not events:
        return "📅 <b>Сегодня экономических событий США нет.</b>"
    
    msk_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(msk_tz).time()
    filtered = []
    for ev in events:
        ev['time'] = convert_to_msk_time(ev.get('time', '00:00'))
        try:
            if datetime.strptime(ev['time'], '%H:%M').time() >= now:
                filtered.append(ev)
        except:
            filtered.append(ev)
    filtered.sort(key=lambda ev: datetime.strptime(ev.get('time', '00:00'), '%H:%M'))

    message = "📅 <b>ЭКОНОМИЧЕСКИЕ СОБЫТИЯ США 🇺🇸</b>\n\n"
    for ev in filtered:
        impact_map = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        impact = impact_map.get(ev.get('impact', 'medium'))
        message += f"{impact} <b>{ev['time']}</b> {ev['event']}\n"
        if ev.get('forecast'): message += f"   Прогноз: {ev['forecast']}\n"
        if ev.get('previous'): message += f"   Предыдущее: {ev['previous']}\n"

    message += "\n💡 Данные: TradingEconomics + MarketCalendarTool"
    return message

async def send_telegram_message(text):
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')
        print("✅ Сообщение отправлено в Telegram")
    except Exception as e:
        print(f"❌ Telegram ошибка: {e}")

# -------------------- Main --------------------
async def main():
    events = fetch_te_events()
    if not events:
        events = fetch_mct_events()

    message = format_events(events)
    print(message)
    await send_telegram_message(message)

if __name__ == "__main__":
    asyncio.run(main())
