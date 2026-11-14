import logging
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
MILLIDA_API_KEY = os.environ.get("MILLIDA_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "https://millida.net/v2/hosting/api"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Введи код, который получил в игре командой /registerbot.\n"
        "Отправь его так: /confirm ТВОЙ_КОД"
    )

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи код: /confirm ТВОЙ_КОД")
        return
    
    code = context.args[0]
    
    if not MILLIDA_API_KEY:
        await update.message.reply_text("Ошибка: API ключ Millida не настроен.")
        return

    try:
        url = f"{API_BASE}/command"
        headers = {
            "Authorization": f"Bearer {MILLIDA_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {"command": f"botconfirm {code}"}
        
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        # Отправляем ответ сервера прямо в Telegram, чтобы увидеть, что не так
        await update.message.reply_text(
            f"Ответ сервера:\n"
            f"Код: {response.status_code}\n"
            f"Текст: {response.text[:200]}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

def main():
    if not TELEGRAM_TOKEN or not MILLIDA_API_KEY:
        logger.error("Не заданы BOT_TOKEN или MILLIDA_API_KEY!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    print("Бот запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
