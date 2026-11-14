import logging
import random
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
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

# Шаги для диалога
WAITING_FOR_NICK = 1

# Хранилище кодов: {code: telegram_id}
codes = {}
# Хранилище для временного сохранения ника
user_nicks = {}

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

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи код: /confirm ТВОЙ_КОД")
        return
    
    code = context.args[0]
    user_id = update.effective_user.id
    
    if code not in codes or codes[code] != user_id:
        await update.message.reply_text("Неверный код или он не принадлежит тебе.")
        return

    # Запоминаем код и переходим к ожиданию ника
    context.user_data['code'] = code
    await update.message.reply_text("Код принят! Теперь напиши свой игровой ник (например, Makakawo777):")
    return WAITING_FOR_NICK

async def receive_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nick = update.message.text.strip()
    code = context.user_data.get('code')
    
    if not code:
        await update.message.reply_text("Что-то пошло не так. Начни заново: /start")
        return ConversationHandler.END

    try:
        # Подключаемся к серверу и выдаем печку
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command(f"give {nick} furnace 1")
            await update.message.reply_text(f"Успешно! Печка выдана игроку {nick}. Ответ сервера: {resp}")
            
            # Удаляем код
            if code in codes:
                del codes[code]
    except Exception as e:
        logger.error(f"Ошибка RCON: {e}")
        await update.message.reply_text(f"Ошибка RCON: {e}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

def main():
    if not TELEGRAM_TOKEN or not RCON_HOST or not RCON_PASSWORD:
        logger.error("Не все переменные окружения заданы! Проверьте BOT_TOKEN, RCON_HOST, RCON_PASSWORD на BotHost.")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Обработчик диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("confirm", confirm)],
        states={
            WAITING_FOR_NICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_nick)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    
    print("Бот запущен и готов к работе!")
    app.run_polling()

if __name__ == '__main__':
    main()
