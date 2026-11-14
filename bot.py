import logging
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
MILLIDA_API_KEY = os.environ.get("MILLIDA_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Базовый URL строго по документации (без слэша на конце)
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
        # Формируем URL правильно: API_BASE + "/command"
        url = f"{API_BASE}/command"
        
        headers = {
            "Authorization": f"Bearer {MILLIDA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {"command": f"botconfirm {code}"}
        
        logger.info(f"Отправка запроса на {url} с ключом: {MILLIDA_API_KEY[:15]}...")
        
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        logger.info(f"Ответ: {response.status_code} - {response.text[:300]}")
        
        if response.status_code == 200:
            await update.message.reply_text(
                f"Код {code} подтвержден! Теперь зайди в игру и введи:\n"
                f"`/botaccept {code}`",
                parse_mode='Markdown'
            )
        else:
            # Показываем ответ сервера в Telegram для отладки
            await update.message.reply_text(
                f"Ошибка Millida: {response.status_code}\n"
                f"Ответ: {response.text[:200]}"
            )
            
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
