#!/usr/bin/env python3
import asyncio
from telegram import Bot
from datetime import datetime, timedelta

# Telegram configuration
TELEGRAM_BOT_TOKEN = "8323539910:AAG6DYij-FuqT7q-ovsBNNgEnWH2V6FXhoM"
TELEGRAM_CHAT_ID = "-1003445906500"

def get_russian_date():
    """Получение текущей даты на русском языке"""
    now = datetime.now()
    
    # Дни недели на русском
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    # Месяцы на русском
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", 
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    
    day_name = days[now.weekday()]
    day = now.day
    month_name = months[now.month - 1]
    
    # Получаем номер недели в году
    week_number = now.isocalendar()[1]
    
    return f"{day_name} {day} {month_name}, неделя {week_number}"

async def send_telegram_message():
    """Отправка сообщения с ссылкой на календарь"""
    current_date = get_russian_date()
    
    message = "#Экономика #Календарь\n\n"
    message += f"<b>{current_date}</b>\n\n"
    message += "<a href='https://tradingeconomics.com/calendar'>📊 Полный календарь событий</a>\n\n"
    message += "<i>Московское время UTC + 3</i>"
    
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        print("✅ Сообщение отправлено в Telegram")
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

async def main():
    print("=== ECONOMIC CALENDAR BOT ===")
    await send_telegram_message()

if __name__ == "__main__":
    asyncio.run(main())
