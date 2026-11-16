import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
MILLIDA_API_KEY = os.environ.get("MILLIDA_API_KEY")
API_BASE = "https://api.millida.net/v2/hosting/api"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def send_console_command(command: str):
    if not MILLIDA_API_KEY: return False
    try:
        headers = {"Authorization": f"Bearer {MILLIDA_API_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{API_BASE}/command", headers=headers, json={"command": command}, timeout=10)
        if response.status_code in [200, 201]:
            return True
        else:
            logger.error(f"Ошибка Millida API: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Ошибка API: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для управления аккаунтом.\n\n"
        "🔗 /link <ник> — привязать аккаунт (выдаст код для ввода в игре)\n"
        "🔑 /changepass <ник> <старый> <новый> — сменить пароль\n"
    )

async def link_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /link <ник>")
        return
    nick = context.args[0]
    tg_id = update.effective_chat.id
    
    # Отправляем команду в консоль сервера, чтобы плагин выдал код
    success = send_console_command(f"makauth link {nick} {tg_id}")
    
    if success:
        await update.message.reply_text(f"🔗 Запрос на привязку для {nick} отправлен! Проверьте игру.")
    else:
        await update.message.reply_text("❌ Ошибка связи с сервером.")

async def changepass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("Использование: /changepass <ник> <старый> <новый>")
        return
    nick, old, new = context.args
    
    if send_console_command(f"makauth changepass {nick} {old} {new}"):
        await update.message.reply_text(f"✅ Команда на смену пароля для `{nick}` отправлена.", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Ошибка связи с сервером.")

# Кнопки для бана/разбана (выдаются вручную или после привязки)
async def send_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /panel <ник>")
        return
    nick = context.args[0]
    
    keyboard = [
        [InlineKeyboardButton("🚫 Заблокировать", callback_data=f"block:{nick}")],
        [InlineKeyboardButton("✅ Разблокировать", callback_data=f"unblock:{nick}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Управление аккаунтом `{nick}`:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    action = data[0]
    nick = data[1]
    
    if action == "block":
        if send_console_command(f"makauth block {nick}"):
            await query.edit_message_text(f"🚫 Аккаунт `{nick}` заблокирован!", parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ Ошибка блокировки.")

    elif action == "unblock":
        if send_console_command(f"makauth unblock {nick}"):
            await query.edit_message_text(f"✅ Аккаунт `{nick}` разблокирован!", parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ Ошибка разблокировки.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link_account))
    app.add_handler(CommandHandler("changepass", changepass))
    app.add_handler(CommandHandler("panel", send_buttons)) # Панель управления
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == '__main__':
    main()
