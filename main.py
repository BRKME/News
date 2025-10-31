from telegram import Bot

BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = 350766421  # или -100XXXXXX для группы
bot = Bot(token=BOT_TOKEN)

message = "Тестовое сообщение 🟢"

print(f"Sending to chat_id={CHAT_ID}...")
bot.send_message(chat_id=CHAT_ID, text=message)
print("✅ Message sent (check Telegram!)")
