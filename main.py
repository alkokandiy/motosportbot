import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import yagmail

# === CONFIG ===
BOT_TOKEN = "7783334945:AAGEbgppd4jWEjBzGONpPrD6qGlIO29EQ-Q"
ADMIN_EMAIL = "buckybyte@gmail.com"
GMAIL_USER = "someoneunknown1133@gmail.com"
GMAIL_APP_PASSWORD = "lgut bkks zjda fkky "

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === EMAIL SETUP ===
yag = yagmail.SMTP(GMAIL_USER, GMAIL_APP_PASSWORD)

# === STATE ===
user_state = {}

roles = {
    "Researcher 📚": "Researcher",
    "Translator 🌍": "Translator",
    "Editor 📝": "Editor",
    "Video Editor 🎥": "Video Editor",
    "Social Media Manager 📱": "Social Media Manager"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💬 Savol berish", callback_data='ask')],
        [InlineKeyboardButton("💡 Mavzu taklif qilish", callback_data='suggest')],
        [InlineKeyboardButton("❗ Xatolik haqida xabar berish", callback_data='mistake')],
        [InlineKeyboardButton("📋 Jamoaga qo'shilishga ariza berish", callback_data='apply')]
    ]
    await update.message.reply_text("Assalomu alaykum, nima qilmoqchisiz?", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data in ['ask', 'suggest', 'mistake']:
        user_state[user_id] = data
        label = {
            'ask': "Savolingizni yozing:",
            'suggest': "Taklifingizni yozing:",
            'mistake': "Xatolik haqida yozing:"
        }[data]
        await query.message.reply_text(label)
    elif data == 'apply':
        user_state[user_id] = {'applying': True, 'step': 1}
        role_buttons = [[InlineKeyboardButton(name, callback_data=f'role_{key}')] for key, name in roles.items()]
        await query.message.reply_text("Qaysi rolda ishlamoqchisiz?", reply_markup=InlineKeyboardMarkup(role_buttons))
    elif data.startswith('role_'):
        role_name = data.split('_', 1)[1]
        user_state[user_id] = {'role': role_name, 'step': 1}
        await query.message.reply_text("Rezyumeni yuboring (file yoki matn).")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "NoUsername"
    message = update.message.text or ""
    doc = update.message.document

    if user_id not in user_state:
        return

    state = user_state[user_id]

    # Feedback Handling
    if state in ['ask', 'suggest', 'mistake']:
        subject = {
            'ask': 'QUESTION',
            'suggest': 'SUGGESTION',
            'mistake': 'MISTAKE'
        }[state]
        body = f"From: @{username}\n\n{message}"
        yag.send(to=ADMIN_EMAIL, subject=subject, contents=body)
        await update.message.reply_text("Rahmat! Javobingiz qabul qilindi.")
        del user_state[user_id]
        return

    # Role Application Handling
    if isinstance(state, dict) and 'role' in state:
        role = state['role']
        if state['step'] == 1:
            # Save resume
            if doc:
                file = await doc.get_file()
                fpath = f"{user_id}_{doc.file_name}"
                await file.download_to_drive(fpath)
                yag.send(to=ADMIN_EMAIL, subject=f"APPLICATION - {role}", contents=f"From: @{username}\n\nAttached Resume:", attachments=[fpath])
            else:
                yag.send(to=ADMIN_EMAIL, subject=f"APPLICATION - {role}", contents=f"From: @{username}\n\nResume:\n\n{message}")
            user_state[user_id]['step'] = 2
            await update.message.reply_text("Rahmat! Endi cover letter yuboring.")
        elif state['step'] == 2:
            yag.send(to=ADMIN_EMAIL, subject=f"APPLICATION - {role} (Cover Letter)", contents=f"From: @{username}\n\nCover Letter:\n\n{message}")
            await update.message.reply_text("Arizangiz qabul qilindi. Tez orada javob beramiz insha'Allah.")
            del user_state[user_id]

# === MAIN ===
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, handle_message))

if __name__ == '__main__':
    print("Bot ishga tushdi...")
    app.run_polling()
