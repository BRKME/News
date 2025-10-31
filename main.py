import sys
import asyncio
import pkg_resources
import datetime
import pytz
import requests
from loguru import logger
from market_calendar_tool import MarketCalendar
from telegram import Bot
from telegram.error import TelegramError


# === 🔍 Проверка зависимостей ===
required_packages = {
    "requests": ">=2.32.3",
    "beautifulsoup4": ">=4.12.3",
    "python-telegram-bot": "==20.7",
    "pytz": "==2023.3",
    "market-calendar-tool": ">=0.2.2",
    "loguru": ">=0.7.2"
}

def check_dependencies():
    for package, version_spec in required_packages.items():
        try:
            pkg_resources.require(f"{package}{version_spec}")
        except pkg_resources.DistributionNotFound:
            print(f"❌ Пакет {package} не найден. Установи: pip install {package}{version_spec}")
            sys.exit(1)
        except pkg_resources.VersionConflict as e:
            print(f"⚠️ Версия пакета {package} несовместима ({e}).")
            print(f"   Требуется: {version_spec}")
            print(f"   Исправь через: pip install '{package}{version_spec}'")
            sys.exit(1)

check_dependencies()


# === ⚙️ Конфигурация ===
TELEGRAM_TOKEN = "ТОКЕН_БОТА"
TELEGRAM_CHAT_ID = "ID_ЧАТА"
TIMEZONE = pytz.timezone("Europe/London")
EXCHANGES = ["NYSE", "NASDAQ", "LSE", "JPX"]


# === 📅 Получение календаря торгов ===
async def get_market_schedule():
    try:
        mc = MarketCalendar()
        results = {}

        for exchange in EXCHANGES:
            logger.info(f"📡 Получаем данные для {exchange}")
            calendar = await mc.get(exchange, start_date="today", end_date="+5d")
            next_open = None

            for row in calendar.itertuples():
                if getattr(row, "is_open", False):
                    next_open = getattr(row, "date")
                    break

            results[exchange] = next_open

        return results

    except Exception as e:
        logger.error(f"Ошибка при получении данных календаря: {e}")
        return None


# === ✉️ Отправка уведомления в Telegram ===
async def send_telegram_message(message: str):
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="HTML")
        logger.info("✅ Сообщение успешно отправлено в Telegram")
    except TelegramError as e:
        logger.error(f"Ошибка Telegram API: {e}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")


# === 🚀 Основная логика ===
async def main():
    logger.info("=== Запуск проверки торговых дней ===")

    schedule = await get_market_schedule()
    if not schedule:
        logger.error("❌ Не удалось получить календарь торгов.")
        return

    today = datetime.datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    message_lines = [f"📊 <b>Торговый календарь на {today}</b>\n"]

    for exchange, next_open in schedule.items():
        if next_open:
            message_lines.append(f"🏦 {exchange}: следующий торговый день — <b>{next_open}</b>")
        else:
            message_lines.append(f"🏦 {exchange}: нет данных ❌")

    message = "\n".join(message_lines)
    await send_telegram_message(message)


if __name__ == "__main__":
    asyncio.run(main())
