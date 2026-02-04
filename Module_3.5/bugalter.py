import sqlite3
import os
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("API")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

conn = sqlite3.connect("chat.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS companies (
    user_id INTEGER,
    company_name TEXT,
    tax_system TEXT,
    context TEXT
)
""")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте! Я бухгалтерский ассистент.\n"
        "Могу помочь с налогами, отчётностью, сроками и документами.\n"
        "Если у вас несколько компаний, просто укажите, про какую речь."
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("DELETE FROM companies WHERE user_id = ?", (update.message.from_user.id,))
    conn.commit()
    await update.message.reply_text("Контекст для вашей компании очищен.")

async def companies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT company_name FROM companies WHERE user_id = ?", (update.message.from_user.id,))
    rows = cursor.fetchall()
    if rows:
        await update.message.reply_text("Ваши компании:\n" + "\n".join([r[0] for r in rows]))
    else:
        await update.message.reply_text("Пока нет сохранённых компаний.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if "ИП" in text or "ТОО" in text:
        company_name = text.split("ИП")[-1].strip() if "ИП" in text else text.split("ТОО")[-1].strip()
        cursor.execute("INSERT OR REPLACE INTO companies(user_id, company_name, context) VALUES (?,?,?)",
                       (user_id, company_name, ""))
        conn.commit()
        await update.message.reply_text(f"Запомнил компанию: {company_name}")
        return

    cursor.execute("SELECT company_name, context FROM companies WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        await update.message.reply_text("Сначала укажите, про какую компанию идёт речь.")
        return

    company_name, context_text = row

    prompt = f"""
Вы бухгалтерский ассистент для компании {company_name}.
Контекст: {context_text}
Вопрос пользователя: {text}
Дай короткий безопасный ответ, если не уверен — предупреди.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0.2
    )
    answer = response.choices[0].message.content

    new_context = context_text + f"\nВопрос: {text} | Ответ: {answer}"
    cursor.execute("UPDATE companies SET context = ? WHERE user_id = ?", (new_context, user_id))
    conn.commit()

    await update.message.reply_text(answer)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CommandHandler("companies", companies))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен...")
app.run_polling()