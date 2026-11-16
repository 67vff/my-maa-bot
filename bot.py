import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ (BotHost) =====
TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
MILLIDA_API_KEY = os.environ.get("MILLIDA_API_KEY")

# API Millida (как сказала поддержка)
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
        logger.info(f"Отправка команды: {command}")
        response = requests.post(
            f"{API_BASE}/command",
            headers=headers,
            json={"command": command},
            timeout=10
        )
        if response.status_code in (200, 201):
            logger.info("Команда успешно отправлена")
            return True
        logger.error(f"Ошибка Millida API: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        logger.error(f"Ошибка запроса к API: {e}")
        return False


# ===== КОМАНДЫ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для управления аккаунтом.\n\n"
        "🔗 /link <ник> — привязать аккаунт\n"
        "🔑 /changepass <ник> <старый> <новый> — сменить пароль\n"
        "🚫 /block <ник> — заблокировать игрока\n"
        "✅ /unblock <ник> — разблокировать игрока\n"
        "🎛 /panel <ник> — панель с кнопками"
    )


async def link_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /link <ник>")
        return
    nick = context.args[0]
    tg_id = update.effective_chat.id

    success = send_console_command(f"makauth link {nick} {tg_id}")
    if success:
        await update.message.reply_text(
            f"🔗 Запрос на привязку для {nick} отправлен!\n"
            f"Зайдите в игру и введите: /confirm <код>"
        )
    else:
        await update.message.reply_text("❌ Ошибка связи с сервером.")


async def changepass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("Использование: /changepass <ник> <старый> <новый>")
        return
    nick, old, new = context.args

    if send_console_command(f"makauth changepass {nick} {old} {new}"):
        await update.message.reply_text(f"✅ Команда на смену пароля для {nick} отправлена.")
    else:
        await update.message.reply_text("❌ Ошибка связи с сервером.")


async def block_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /block <ник>")
        return
    nick = context.args[0]

    if send_console_command(f"makauth block {nick}"):
        await update.message.reply_text(f"🚫 Игрок {nick} заблокирован.")
    else:
        await update.message.reply_text("❌ Ошибка связи с сервером.")


async def unblock_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /unblock <ник>")
        return
    nick = context.args[0]

    if send_console_command(f"makauth unblock {nick}"):
        await update.message.reply_text(f"✅ Игрок {nick} разблокирован.")
    else:
        await update.message.reply_text("❌ Ошибка связи с сервером.")


async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /panel <ник>")
        return
    nick = context.args[0]

    keyboard = [
        [InlineKeyboardButton("🚫 Заблокировать", callback_data=f"block:{nick}")],
        [InlineKeyboardButton("✅ Разблокировать", callback_data=f"unblock:{nick}")]
    ]
    await update.message.reply_text(
        f"🎛 Управление аккаунтом {nick}:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, nick = query.data.split(":", 1)

    if action == "block":
        if send_console_command(f"makauth block {nick}"):
            await query.edit_message_text(f"🚫 Аккаунт {nick} заблокирован!")
        else:
            await query.edit_message_text("❌ Ошибка блокировки.")

    elif action == "unblock":
        if send_console_command(f"makauth unblock {nick}"):
            await query.edit_message_text(f"✅ Аккаунт {nick} разблокирован!")
        else:
            await query.edit_message_text("❌ Ошибка разблокировки.")


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
    app.add_handler(CommandHandler("link", link_account))
    app.add_handler(CommandHandler("changepass", changepass))
    app.add_handler(CommandHandler("block", block_account))
    app.add_handler(CommandHandler("unblock", unblock_account))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
