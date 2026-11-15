import logging
import os
import requests
import threading
import random
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
PLUGIN_API = "http://127.0.0.1:8081" # Порт плагина

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_app = None

@app.route('/send_link_code', methods=['POST'])
def send_link_code():
    data = request.json
    player = data.get('player')
    code = data.get('code')
    tg_id = data.get('tg_id')
    print(f"[BOT] Код для {player}: {code}")
    return jsonify({"ok": True})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для управления аккаунтом.\n\n"
        "🔗 /link <ник> — привязать аккаунт (выдаст код для ввода в игре)\n"
        "🔑 /changepass <ник> <старый> <новый> — сменить пароль\n"
        "🚫 /block <ник> — заблокировать аккаунт\n"
        "✅ /unblock <ник> — разблокировать аккаунт"
    )

async def link_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /link <ник>")
        return
    nick = context.args[0]
    tg_id = update.effective_chat.id
    code = str(random.randint(1000, 9999))
    
    # В реальности бот должен отправить запрос плагину, чтобы тот сохранил код.
    # Пока просто выводим код игроку.
    await update.message.reply_text(
        f"🔗 Код для привязки: `{code}`\n\n"
        f"Зайди в игру и введи: `/confirm {code}`",
        parse_mode='Markdown'
    )

async def changepass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("Использование: /changepass <ник> <старый> <новый>")
        return
    nick, old_pass, new_pass = context.args
    try:
        res = requests.post(f"{PLUGIN_API}/changepass", json={
            "player": nick, "old": old_pass, "new": new_pass
        }, timeout=5)
        if res.status_code == 200:
            await update.message.reply_text(f"✅ Пароль для {nick} изменен!")
        else:
            await update.message.reply_text(f"❌ Ошибка: Неверный старый пароль.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка связи с сервером: {e}")

async def block_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /block <ник>")
        return
    nick = context.args[0]
    try:
        requests.post(f"{PLUGIN_API}/block", json={"player": nick}, timeout=5)
        await update.message.reply_text(f"🚫 Аккаунт {nick} заблокирован.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def unblock_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /unblock <ник>")
        return
    nick = context.args[0]
    try:
        requests.post(f"{PLUGIN_API}/unblock", json={"player": nick}, timeout=5)
        await update.message.reply_text(f"✅ Аккаунт {nick} разблокирован.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

def run_bot():
    global bot_app
    bot_app = Application.builder().token(TELEGRAM_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("link", link_account))
    bot_app.add_handler(CommandHandler("changepass", changepass))
    bot_app.add_handler(CommandHandler("block", block_account))
    bot_app.add_handler(CommandHandler("unblock", unblock_account))
    bot_app.run_polling()

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)).start()
    run_bot()
