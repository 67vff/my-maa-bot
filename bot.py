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
        # Формируем URL правильно (без лишних слэшей)
        url = f"{API_BASE}/command"
        
        headers = {
            "Authorization": f"Bearer {MILLIDA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Отправляем команду
        data = {"command": f"botconfirm {code}"}
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        # Логируем ответ для отладки
        logger.info(f"API ответ: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            await update.message.reply_text(
                f"Код {code} подтвержден! Теперь зайди в игру и введи:\n"
                f"`/botaccept {code}`",
                parse_mode='Markdown'
            )
        elif response.status_code == 401:
            await update.message.reply_text(
                "Ошибка 401: Ключ не принят. Проверь, что ключ скопирован без пробелов и у него есть право «Консоль и команды»."
            )
        else:
            await update.message.reply_text(f"Ошибка API: {response.status_code}. Ответ: {response.text[:100]}")
            
    except Exception as e:
        logger.error(f"Ошибка запроса: {e}")
        await update.message.reply_text(f"Ошибка подключения: {e}")

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
