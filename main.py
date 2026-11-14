import logging
import random
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from mcrcon import MCRcon

# --- НАСТРОЙКИ (берутся из переменных окружения BotHost) ---
TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
RCON_HOST = os.environ.get("RCON_HOST")
RCON_PORT = 25575
RCON_PASSWORD = os.environ.get("RCON_PASSWORD")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранилище кодов: {code: telegram_id}
codes = {}

# --- ЛОГИКА БОТА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Генерируем длинный случайный код (8 символов)
    code = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))
    codes[code] = user_id
    
    await update.message.reply_text(
        f"Привет! Твой код для регистрации: `{code}`\n\n"
        f"1. Зайди на сервер.\n"
        f"2. Введи в чат: `/registerbot {code}`\n"
        f"3. После этого напиши сюда: `/confirm {code}`",
        parse_mode='Markdown'
    )

async def registerbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Эта функция на сервере не используется, она нужна только для плагина.
    pass

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи код: /confirm ТВОЙ_КОД")
        return
    
    code = context.args[0]
    user_id = update.effective_user.id
    
    if code not in codes or codes[code] != user_id:
        await update.message.reply_text("Неверный код или он не принадлежит тебе.")
        return

    # В реальном боте нужно запросить ник игрока, но для теста
    # мы просто выдадим печку игроку с ником Makakawo777 (замени на свой ник)
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            # ВАЖНО: Замени Makakawo777 на свой ник в игре
            resp = mcr.command("give Makakawo777 furnace 1")
            await update.message.reply_text(f"Успешно! Печка выдана. Ответ сервера: {resp}")
            
            # Удаляем код, чтобы его нельзя было использовать повторно
            del codes[code]
    except Exception as e:
        logger.error(f"Ошибка RCON: {e}")
        await update.message.reply_text(f"Ошибка RCON: {e}")

def main():
    # Проверяем, что все переменные загружены
    if not TELEGRAM_TOKEN or not RCON_HOST or not RCON_PASSWORD:
        logger.error("Не все переменные окружения заданы! Проверьте BOT_TOKEN, RCON_HOST, RCON_PASSWORD на BotHost.")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    
    print("Бот запущен и готов к работе!")
    app.run_polling()

if __name__ == '__main__':
    main()
