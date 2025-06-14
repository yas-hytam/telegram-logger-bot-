import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ganti token bot lu di sini
BOT_TOKEN = '7939205172:AAHG3Tln0Ti9ML2RDNfYliyH9bC1oy7RvqM'

# UID yang diizinkan
VALID_UIDS = ['UID1112', 'UID1807']

# menyimpan sesi aktif: {chat_id: uid}
user_sessions = {}

# menyimpan message_id monitoring: {chat_id: msg_id}
user_monitoring_msg = {}

# menyimpan konten terakhir: {chat_id: teks}
last_update = {}

# log biar tau error apa aja
logging.basicConfig(level=logging.INFO)


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_sessions.pop(chat_id, None)
    await context.bot.send_message(chat_id, '📲 Masukkan UID kamu untuk mulai monitoring.')


# handle UID input
async def handle_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    uid = update.message.text.strip()

    if uid in VALID_UIDS:
        user_sessions[chat_id] = uid
        teks = f"✅ UID diterima: *{uid}*\nMenunggu data dari device..."
        keyboard = [[
            InlineKeyboardButton("🔄 Monitoring", callback_data="monitoring"),
            InlineKeyboardButton("🚪 Keluar", callback_data="logout")
        ]]
        sent = await update.message.reply_text(teks, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        user_monitoring_msg[chat_id] = sent.message_id
    else:
        await update.message.reply_text("❌ UID tidak valid. Coba lagi.")


# tombol inline ditekan
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    if query.data == "logout":
        user_sessions.pop(chat_id, None)
        user_monitoring_msg.pop(chat_id, None)
        last_update.pop(chat_id, None)
        await query.edit_message_text("🚪 Kamu telah keluar dari sesi monitoring.\nGunakan /start untuk login lagi.")
    elif query.data == "monitoring":
        if chat_id in user_sessions:
            uid = user_sessions[chat_id]
            teks = last_update.get(chat_id, f"📲 UID: {uid}\n\nBelum ada data dari device.")
            keyboard = [[
                InlineKeyboardButton("🔄 Monitoring", callback_data="monitoring"),
                InlineKeyboardButton("🚪 Keluar", callback_data="logout")
            ]]
            await query.edit_message_text(teks, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("❌ Sesi kamu sudah berakhir. Gunakan /start untuk mulai lagi.")


# endpoint buat APK ngirim data (pake HTTP POST)
async def push_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    if not msg.startswith("UID:"):
        return

    lines = msg.split('\n')
    uid_line = lines[0]
    uid = uid_line.replace("UID:", "").strip()

    # cari semua chat_id yang pake UID ini
    for chat_id, session_uid in user_sessions.items():
        if session_uid == uid:
            text_to_send = msg.strip()
            last_update[chat_id] = text_to_send

            msg_id = user_monitoring_msg.get(chat_id)
            if msg_id:
                keyboard = [[
                    InlineKeyboardButton("🔄 Monitoring", callback_data="monitoring"),
                    InlineKeyboardButton("🚪 Keluar", callback_data="logout")
                ]]
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg_id,
                        text=text_to_send,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except:
                    pass


# pasang handler
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex('^UID:'), push_data))  # data dari APK
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uid))       # input UID biasa

    print("Bot siap jalan...")
    app.run_polling()
