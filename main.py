import asyncio
from datetime import datetime, timedelta
from market_calendar_tool import MarketCalendar
from telegram import Bot

# === Telegram configuration ===
BOT_TOKEN = "8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8"
CHAT_ID = "350766421"

# === Main logic ===
async def fetch_us_events():
    """Парсинг реальных экономических событий США через MarketCalendar"""
    mc = MarketCalendar()
    today = datetime.utcnow().date()
    end_date = today + timedelta(days=1)
    try:
        events_df = await mc.calendar(
            country="united states",
            start_date=today.isoformat(),
            end_date=end_date.isoformat()
        )
        return events_df
    except Exception as e:
        print(f"[ERROR] Ошибка получения данных: {e}")
        return None


async def format_events(events_df):
    """Форматирование списка событий для Telegram"""
    if events_df is None or events_df.empty:
        return "⚠️ No US events found today."

    result_lines = ["🇺🇸 *US Economic Events Today:*"]
    for _, row in events_df.iterrows():
        time = row.get("date", "") or "N/A"
        event = row.get("event", "Unnamed Event")
        importance = row.get("importance", "")
        result_lines.append(f"🕒 {time} — {event} ({importance})")

    return "\n".join(result_lines)


async def send_to_telegram(message: str):
    """Отправка сообщения в Telegram"""
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        print("[OK] Сообщение успешно отправлено в Telegram")
    except Exception as e:
        print(f"[ERROR] Ошибка отправки в Telegram: {e}")


async def main():
    print("=" * 60)
    print("US ECONOMIC EVENTS - REAL DATA PARSER")
    print("=" * 60)
    print("Fetching real data...")

    events = await fetch_us_events()
    message = await format_events(events)
    await send_to_telegram(message)


if __name__ == "__main__":
    asyncio.run(main())
