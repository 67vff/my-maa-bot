import logging
import os
import random
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ (задаются на BotHost) =====
TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
MILLIDA_API_KEY = os.environ.get("MILLIDA_API_KEY")

# Адрес API Millida (как сказала поддержка)
API_BASE = "https://api.millida.net/v2/hosting/api"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ===== ОТПРАВКА КОМАНДЫ В КОНСОЛЬ СЕРВЕРА =====
def send_console_command(command: str) -> bool:
    if not MILLIDA_API_KEY:
        logger.error("MILLIDA_API_KEY не задан!")
        return False

    try:
        headers = {
            "Authorization": f"Bearer {MILLIDA_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {"command": command}

        logger.info(f"Отправка команды в консоль: {command}")
        response = requests.post(
            f"{API_BASE}/command",
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code in (200, 201):
            logger.info("Команда успешно отправлена")
            return True

        logger.error(f"Ошибка Millida API: {response.status_code} - {response.text}")
        return False

    except Exception as e:
        logger.error(f"Ошибка запроса к Millida API: {e}")
        return False


# ===== КОМАНДЫ БОТА =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для управления аккаунтом.\n\n"
        "🔑 /changepass <ник> <старый> <новый> — сменить пароль\n"
        "🚫 /block <ник> — заблокировать игрока\n"
        "✅ /unblock <ник> — разблокировать игрока"
    )


async def changepass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text(
            "Использование: /changepass <ник> <старый> <новый>"
        )
        return

    nick, old, new = context.args
    success = send_console_command(f"makauth changepass {nick} {old} {new}")

    if success:
        await update.message.reply_text(
            f"✅ Команда на смену пароля для {nick} отправлена на сервер."
        )
    else:
        await update.message.reply_text(
            "❌ Ошибка связи с API Millida. Проверьте ключ и права."
        )


async def block_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /block <ник>")
        return

    nick = context.args[0]
    success = send_console_command(f"makauth block {nick}")

    if success:
        await update.message.reply_text(f"🚫 Игрок {nick} заблокирован.")
    else:
        await update.message.reply_text("❌ Ошибка связи с API Millida.")


async def unblock_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /unblock <ник>")
        return

    nick = context.args[0]
    success = send_console_command(f"makauth unblock {nick}")

    if success:
        await update.message.reply_text(f"✅ Игрок {nick} разблокирован.")
    else:
        await update.message.reply_text("❌ Ошибка связи с API Millida.")


# ===== ЗАПУСК =====
def main():
    if not TELEGRAM_TOKEN:
        logger.error("Не задан BOT_TOKEN!")
        return
    if not MILLIDA_API_KEY:
        logger.error("Не задан MILLIDA_API_KEY!")
        return

    logger.info("Бот запущен! Используется API Millida.")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("changepass", changepass))
    app.add_handler(CommandHandler("block", block_account))
    app.add_handler(CommandHandler("unblock", unblock_account))

    app.run_polling()


if __name__ == "__main__":
    main()
