import logging
import os
import requests
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
MILLIDA_API_KEY = os.environ.get("MILLIDA_API_KEY")
MILLIDA_API = "https://millida.net/v2/hosting/api"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Вспомогательная функция для отправки команд в консоль сервера
def send_console_command(command: str):
    try:
        headers = {
            "Authorization": f"Bearer {MILLIDA_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {"command": command}
        response = requests.post(f"{MILLIDA_API}/command", headers=headers, json=data, timeout=10)
        
        if response.status_code in [200, 201]:
            return True
        else:
            logger.error(f"Millida API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Ошибка запроса к Millida API: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для управления аккаунтом.\n\n"
        "🔗 /link <ник> — привязать аккаунт\n"
        "🔑 /changepass <ник> <старый> <новый> — сменить пароль\n"
        "🚫 /block <ник> — заблокировать\n"
        "✅ /unblock <ник> — разблокировать"
    )

async def link_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /link <ник>")
        return
    nick = context.args[0]
    # Генерируем код и отправляем его в консоль (плагин должен его поймать)
    code = str(random.randint(1000, 9999))
    
    # Отправляем команду в консоль сервера, чтобы плагин сохранил код
    success = send_console_command(f"makauth linkcode {nick} {code}")
    
    if success:
        await update.message.reply_text(
            f"🔗 Код: `{code}`\nВведи в игре: `/confirm {code}`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Ошибка отправки команды на сервер.")

async def changepass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("Использование: /changepass <ник> <старый> <новый>")
        return
    nick, old, new = context.args
    
    # Отправляем команду в консоль
    success = send_console_command(f"makauth changepass {nick} {old} {new}")
    
    if success:
        await update.message.reply_text(f"✅ Команда на смену пароля для {nick} отправлена на сервер.")
    else:
        await update.message.reply_text("❌ Ошибка связи с сервером.")

async def block_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /block <ник>")
        return
    nick = context.args[0]
    
    success = send_console_command(f"makauth block {nick}")
    
    if success:
        await update.message.reply_text(f"🚫 Команда на блокировку {nick} отправлена.")
    else:
        await update.message.reply_text("❌ Ошибка связи с сервером.")

async def unblock_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /unblock <ник>")
        return
    nick = context.args[0]
    
    success = send_console_command(f"makauth unblock {nick}")
    
    if success:
        await update.message.reply_text(f"✅ Команда на разблокировку {nick} отправлена.")
    else:
        await update.message.reply_text("❌ Ошибка связи с сервером.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link_account))
    app.add_handler(CommandHandler("changepass", changepass))
    app.add_handler(CommandHandler("block", block_account))
    app.add_handler(CommandHandler("unblock", unblock_account))
    app.run_polling()

if __name__ == '__main__':
    main()
