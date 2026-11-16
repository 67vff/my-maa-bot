import logging
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- НАСТРОЙКИ (берутся из переменных окружения BotHost) ---
TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
MILLIDA_API_KEY = os.environ.get("MILLIDA_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BASE_URL = "https://millida.net"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-тестировщик.\n"
        "Введи /confirm ТВОЙ_КОД — я сам проверю все форматы API Millida и скажу, какой сработал."
    )

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи код: /confirm ТВОЙ_КОД")
        return
    
    code = context.args[0]
    if not MILLIDA_API_KEY:
        await update.message.reply_text("Ошибка: MILLIDA_API_KEY не задан на сервере.")
        return

    await update.message.reply_text("⏳ Проверяю 12 вариантов подключения к API Millida...")

    cmd = f"makaauth botconfirm {code}"
    key = MILLIDA_API_KEY.strip()
    
    ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0"}
    h_bearer = {**ua, "Authorization": f"Bearer {key}", "Accept": "application/json"}
    h_xapi = {**ua, "X-Api-Key": key, "Accept": "application/json"}
    h_key = {**ua, "Api-Key": key, "Accept": "application/json"}

    # Список всех возможных вариантов (название, метод, URL, заголовки, json, data/params)
    variants = [
        ("1. POST JSON action=command", "POST", BASE_URL, h_bearer, {"action": "command", "command": cmd}, None),
        ("2. POST JSON type=command", "POST", BASE_URL, h_bearer, {"type": "command", "command": cmd}, None),
        ("3. POST JSON cmd", "POST", BASE_URL, h_bearer, {"cmd": cmd}, None),
        ("4. POST Form action=command", "POST", BASE_URL, h_bearer, None, {"action": "command", "command": cmd}),
        ("5. GET params action=command", "GET", BASE_URL, h_bearer, None, {"action": "command", "command": cmd}),
        ("6. GET key+command в ссылке", "GET", BASE_URL, ua, None, {"key": key, "action": "command", "command": cmd}),
        ("7. GET api_key+command в ссылке", "GET", BASE_URL, ua, None, {"api_key": key, "command": cmd}),
        ("8. POST /console (Bearer)", "POST", f"{BASE_URL}/console", h_bearer, {"command": cmd}, None),
        ("9. POST /server/command (Bearer)", "POST", f"{BASE_URL}/server/command", h_bearer, {"command": cmd}, None),
        ("10. POST /send (Bearer)", "POST", f"{BASE_URL}/send", h_bearer, {"command": cmd}, None),
        ("11. POST /command (X-Api-Key)", "POST", f"{BASE_URL}/command", h_xapi, {"command": cmd}, None),
        ("12. POST /command (Api-Key)", "POST", f"{BASE_URL}/command", h_key, {"command": cmd}, None),
    ]

    report = []
    for name, method, url, headers, json_body, payload in variants:
        try:
            if method == "POST":
                if json_body:
                    r = requests.post(url, headers=headers, json=json_body, timeout=5)
                else:
                    r = requests.post(url, headers=headers, data=payload, timeout=5)
            else:
                r = requests.get(url, headers=headers, params=payload, timeout=5)
            
            # Если сервер принял запрос!
            if r.status_code in (200, 201, 204):
                await update.message.reply_text(
                    f"✅ НАЙДЕН РАБОЧИЙ ВАРИАНТ!\n"
                    f"Сработал: *{name}*\n\n"
                    f"Команда уже отправлена на сервер! Заходи в игру и вводи:\n"
                    f"`/botaccept {code}`",
                    parse_mode='Markdown'
                )
                return
            
            # Сокращаем ответ для отчёта
            if "<html" in r.text.lower() or "<!doctype" in r.text.lower():
                short_text = "HTML-заглушка (защита/404)"
            else:
                short_text = r.text[:70].replace("\n", " ") or "пусто"
                
            report.append(f"{name} -> *{r.status_code}* ({short_text})")
        except Exception as e:
            report.append(f"{name} -> Ошибка: {type(e).__name__}")

    await update.message.reply_text(
        "❌ Ни один из 12 вариантов не сработал. Вот отчёт:\n\n" + "\n".join(report),
        parse_mode='Markdown'
    )

def main():
    if not TELEGRAM_TOKEN or not MILLIDA_API_KEY:
        logger.error("Критическая ошибка: не заданы BOT_TOKEN или MILLIDA_API_KEY!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    
    logger.info("Бот-тестировщик запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
