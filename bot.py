import sqlite3
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = "8525829777:AAH9NyB7CEJk-zjxpgrPRvGv6QE0JWd59hg"
GROUP_ID = -1003992648575  # group id

ADMIN_ID = 103603233  # sening telegram id

EMPLOYEES = [123456789]  # ruxsat berilganlar

# States
PHONE, SERVICE = range(2)

services = [["Remont", "Diagnostika"], ["O‘rnatish"]]

# DB
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS data (user_id, phone, service, time)")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in EMPLOYEES:
        await update.message.reply_text("❌ Ruxsat yo‘q")
        return ConversationHandler.END
    await update.message.reply_text("📞 Telefon raqam kiriting:")
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    if not phone.isdigit() or len(phone) != 9:
        await update.message.reply_text("❌ 9 xonali raqam kiriting")
        return PHONE
    context.user_data["phone"] = phone

    keyboard = ReplyKeyboardMarkup(services, resize_keyboard=True)
    await update.message.reply_text("🛠 Xizmat tanlang:", reply_markup=keyboard)
    return SERVICE

async def service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    phone = context.user_data["phone"]
    service = update.message.text
    time = datetime.now().strftime("%Y-%m-%d %H:%M")

    cursor.execute("INSERT INTO data VALUES (?, ?, ?, ?)", (user, phone, service, time))
    conn.commit()

    text = f"""📋 Yangi mijoz

👤 Xodim: {user}
📞 Tel: {phone}
🛠 Xizmat: {service}
🕒 Vaqt: {time}
"""

    await context.bot.send_message(chat_id=GROUP_ID, text=text)
    await update.message.reply_text("✅ Saqlandi")

    return ConversationHandler.END

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    import pandas as pd
    df = pd.read_sql_query("SELECT * FROM data", conn)
    file = "report.xlsx"
    df.to_excel(file, index=False)

    await update.message.reply_document(open(file, "rb"))

app = ApplicationBuilder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
        SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, service)],
    },
    fallbacks=[]
)

app.add_handler(conv)
app.add_handler(CommandHandler("report", report))

app.run_polling()
