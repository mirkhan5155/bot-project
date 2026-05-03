import sqlite3
from datetime import datetime
import pandas as pd

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# ================= CONFIG =================
TOKEN = "8525829777:AAHa4J2Lq2K6JEsv3T6yjJYFLGHLDs3zc8w"

ADMIN_ID = 103603233
ALLOWED_USERS = [123456789]

GROUP_ID = -1003992648575

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    phone TEXT,
    service TEXT,
    time TEXT
)
""")

conn.commit()

# ================= STATES =================
PHONE, SERVICE = range(2)

services_keyboard = ReplyKeyboardMarkup(
    [["Remont", "Diagnostika"], ["O‘rnatish"]],
    resize_keyboard=True
)

# ================= CHECK =================
def is_allowed(user_id: int):
    return user_id == ADMIN_ID or user_id in ALLOWED_USERS

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text("❌ Ruxsat yo‘q")
        return ConversationHandler.END

    await update.message.reply_text("📞 Telefon raqam kiriting (9 xonali):")
    return PHONE

# ================= PHONE =================
async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text

    if not phone.isdigit() or len(phone) != 9:
        await update.message.reply_text("❌ 9 xonali raqam kiriting")
        return PHONE

    context.user_data["phone"] = phone

    await update.message.reply_text("🛠 Xizmat tanlang:", reply_markup=services_keyboard)
    return SERVICE

# ================= SERVICE =================
async def service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    phone = context.user_data["phone"]
    service = update.message.text
    time = datetime.now().strftime("%Y-%m-%d %H:%M")

    cursor.execute(
        "INSERT INTO logs (user_id, phone, service, time) VALUES (?, ?, ?, ?)",
        (user_id, phone, service, time)
    )
    conn.commit()

    text = f"""
📋 Yangi mijoz

👤 ID: {user_id}
📞 Tel: {phone}
🛠 Xizmat: {service}
🕒 Vaqt: {time}
"""

    await context.bot.send_message(chat_id=GROUP_ID, text=text)
    await update.message.reply_text("✅ Saqlandi")

    return ConversationHandler.END

# ================= ADMIN PANEL =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = ReplyKeyboardMarkup(
        [["📊 Report", "👥 Users"]],
        resize_keyboard=True
    )

    await update.message.reply_text("🔧 Admin panel:", reply_markup=keyboard)

# ================= REPORT =================
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    df = pd.read_sql_query("SELECT * FROM logs", conn)

    filename = f"report_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"
    df.to_excel(filename, index=False)

    await update.message.reply_document(open(filename, "rb"))

# ================= RUN =================
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
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("report", report))

if __name__ == "__main__":
    app.run_polling()
