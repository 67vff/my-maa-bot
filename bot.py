import logging
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
MILLIDA_API_KEY = os.environ.get("MILLIDA_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ИСПРАВЛЕННЫЙ АДРЕС API (подсказка от поддержки Millida)
API_BASE = "https://api.millida.net/v2/hosting/api"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Введи код, который получил в игре командой /registerbot.\n"
        "Отправь его так: /confirm ТВОЙ_КОД\n\n"
        "Также доступна команда /disableprotection для отключения антибота."
    )

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи код: /confirm ТВОЙ_КОД")
        return
    
    code = context.args[0]
    
    if not MILLIDA_API_KEY:
        await update.message.reply_text("Ошибка: API ключ Millida не настроен в переменных окружения.")
        return

    try:
        url = f"{API_BASE}/command"
        headers = {
            "Authorization": f"Bearer {MILLIDA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {"command": f"botconfirm {code}"}
        
        logger.info(f"Отправка запроса на {url} с командой botconfirm {code}")
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            await update.message.reply_text(
                f"✅ Код `{code}` подтвержден!\n\n"
                f"Теперь зайди в игру и введи:\n"
                f"`/botaccept {code}`",
                parse_mode='Markdown'
            )
        elif response.status_code == 401:
            await update.message.reply_text(
                "❌ Ошибка 401 (Unauthorized).\n"
                "Возможные причины:\n"
                "1. Неверный API-ключ (проверь MILLIDA_API_KEY).\n"
                "2. У ключа нет права 'Защита' (protection).\n"
                "3. Ключ создан в старом разделе (пересоздай в 'Игроки и доступ' -> 'API-ключи')."
            )
        else:
            await update.message.reply_text(
                f"❌ Ошибка Millida: {response.status_code}\n"
                f"Ответ: {response.text[:300]}"
            )
            
    except requests.exceptions.Timeout:
        await update.message.reply_text("❌ Превышено время ожидания ответа от Millida.")
    except Exception as e:
        logger.error(f"Ошибка запроса: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def disable_protection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not MILLIDA_API_KEY:
        await update.message.reply_text("Ошибка: API ключ не настроен.")
        return

    try:
        url = f"{API_BASE}/antibot"
        headers = {
            "Authorization": f"Bearer {MILLIDA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {"preset": "off"}
        
        logger.info(f"Отправка запроса на {url} для отключения защиты")
        response = requests.put(url, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            await update.message.reply_text("✅ Защита (антибот) успешно отключена!")
        elif response.status_code == 401:
            await update.message.reply_text(
                "❌ Ошибка 401 (Unauthorized).\n"
                "Убедись, что у API-ключа есть право 'protection' (Защита)."
            )
        else:
            await update.message.reply_text(
                f"Статус: {response.status_code}\n"
                f"Ответ: {response.text[:300]}"
            )
    except Exception as e:
        logger.error(f"Ошибка запроса: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")

def main():
    if not TELEGRAM_TOKEN or not MILLIDA_API_KEY:
        logger.error("Не заданы BOT_TOKEN или MILLIDA_API_KEY в переменных окружения!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CommandHandler("disableprotection", disable_protection))
    
    logger.info("Бот запущен и готов к работе!")
    app.run_polling()

if __name__ == '__main__':
    main()
