import logging
import os
import requests
from flask import Flask, request, jsonify
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
MILLIDA_API_KEY = os.environ.get("MILLIDA_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "https://api.millida.net/v2/hosting/api"
app = Flask(__name__)
bot_app = None

# --- HTTP СЕРВЕР ДЛЯ ПЛАГИНА ---
@app.route('/send_2fa', methods=['POST'])
def send_2fa():
    data = request.json
    chat_id = data.get('chat_id')
    player = data.get('player')
    code = data.get('code')
    ip = data.get('ip')

    if not chat_id:
        return jsonify({"ok": False, "error": "No chat_id"}), 400

    # Получаем город по IP (через ip-api.com)
    city = "Unknown"
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=city,country", timeout=3)
        if res.status_code == 200:
            info = res.json()
            city = f"{info.get('city', '?')}, {info.get('country', '?')}"
    except:
        pass

    text = f"🔐 Запрос на вход\nИгрок: {player}\nIP: {ip}\nГород: {city}\nКод: {code}"
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm:{player}:{code}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"deny:{player}:{code}")]
    ]
    
    # Отправляем сообщение в Telegram
    bot_app.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return jsonify({"ok": True})

# --- TELEGRAM БОТ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для 2FA. Введи /link <ник> чтобы привязать аккаунт.")

async def link_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /link <ник>")
        return
    nick = context.args[0]
    chat_id = update.effective_chat.id
    
    # Отправляем запрос на сервер плагина для привязки
    try:
        # Плагин должен иметь эндпоинт /link, который обновляет БД
        # Для простоты, плагин может сам присылать запрос боту, но здесь мы просто говорим что нужно сделать
        await update.message.reply_text(f"Аккаунт {nick} привязан к TG! (В реальности нужно дернуть API плагина)")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")
    action = data[0]
    player = data[1]
    code = data[2]

    if action == "confirm":
        await query.edit_message_text(text=f"✅ Вход для {player} подтвержден!")
        # Здесь нужно дернуть API плагина, чтобы он пустил игрока
        # POST http://127.0.0.1:8080/confirm_2fa (player, code)
    else:
        await query.edit_message_text(text=f"❌ Вход для {player} отклонен.")

def run_bot():
    global bot_app
    bot_app = Application.builder().token(TELEGRAM_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("link", link_account))
    bot_app.add_handler(CallbackQueryHandler(button_handler))
    bot_app.run_polling()

if __name__ == '__main__':
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=lambda: app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)).start()
    # Запускаем бота
    run_bot()
