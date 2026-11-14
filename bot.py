import logging
import random
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from mcrcon import MCRcon

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
RCON_HOST = os.environ.get("RCON_HOST")
RCON_PORT = 25575
RCON_PASSWORD = os.environ.get("RCON_PASSWORD")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище: code -> telegram_id
codes = {}

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
    user_id = update.effective_user.id
    
    # В этой версии бот не генерирует код, а принимает его от игрока
    # и отправляет команду /botconfirm на сервер через RCON
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command(f"botconfirm {code}")
            if "Код подтвержден" in resp or "confirmed" in resp.lower():
                await update.message.reply_text(
                    f"Код {code} подтвержден! Теперь зайди в игру и введи:\n"
                    f"`/botaccept {code}`",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"Ошибка: код {code} не найден на сервере. Проверь правильность.")
    except Exception as e:
        logger.error(f"Ошибка RCON: {e}")
        await update.message.reply_text(f"Ошибка RCON: {e}")

def main():
    if not TELEGRAM_TOKEN or not RCON_HOST or not RCON_PASSWORD:
        logger.error("Не все переменные окружения заданы!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    print("Бот запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
