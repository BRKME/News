#!/usr/bin/env python3
import asyncio
from telegram import Bot

# Telegram configuration
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

async def send_telegram_message():
    """Отправка сообщения с ссылкой на календарь"""
    message = "📅 <b>Экономический календарь</b>\n\n"
    message += "<a href='https://tradingeconomics.com/calendar'>📊 Полный календарь событий</a>"
    
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
