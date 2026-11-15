import logging
import os
import requests
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
PLUGIN_API = "http://127.0.0.1:8081"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    tg_id = update.effective_chat.id
    code = str(random.randint(1000, 9999))
    try:
        requests.post(f"{PLUGIN_API}/link", json={"player": nick, "tg_id": tg_id}, timeout=5)
        await update.message.reply_text(f"🔗 Код: `{code}`\nВведи в игре: `/confirm {code}`", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def changepass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("Использование: /changepass <ник> <старый> <новый>")
        return
    nick, old, new = context.args
    try:
        res = requests.post(f"{PLUGIN_API}/changepass", json={"player": nick, "old": old, "new": new}, timeout=5)
        if res.status_code == 200:
            await update.message.reply_text("✅ Пароль изменен!")
        else:
            await update.message.reply_text("❌ Неверный старый пароль.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def block_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /block <ник>")
        return
    nick = context.args[0]
    try:
        requests.post(f"{PLUGIN_API}/block", json={"player": nick}, timeout=5)
        await update.message.reply_text(f"🚫 {nick} заблокирован.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def unblock_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /unblock <ник>")
        return
    nick = context.args[0]
    try:
        requests.post(f"{PLUGIN_API}/unblock", json={"player": nick}, timeout=5)
        await update.message.reply_text(f"✅ {nick} разблокирован.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

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
