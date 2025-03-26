from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, ConversationHandler, CommandHandler
import os
import shutil
import subprocess

TOKEN = os.getenv("7715067294:AAG-Q0FytScllZa7mP9UIDfhcQBNrjP4hsQ")
ASK_FILENAME = 1
user_data = {}

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📥 Send me an MKV file (up to 4GB)!")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document or update.message.video
    if not file or not file.file_name.endswith(".mkv"):
        await update.message.reply_text("⚠️ Send a valid .mkv file.")
        return

    user_id = update.message.from_user.id
    file_path = f"{DOWNLOAD_FOLDER}/{file.file_unique_id}_{file.file_name}"

    await update.message.reply_text("📥 Downloading file... ⏳")
    telegram_file = await file.get_file()
    await telegram_file.download_to_drive(file_path)

    user_data[user_id] = file_path
    await update.message.reply_text("✅ Got it! Send me the **new name** (without .mkv)")
    return ASK_FILENAME

async def rename_and_clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    old_path = user_data.get(user_id)
    if not old_path:
        await update.message.reply_text("❌ Something went wrong. Try again.")
        return ConversationHandler.END

    new_name = update.message.text.strip()
    new_path = f"{DOWNLOAD_FOLDER}/{new_name}.mkv"

    await update.message.reply_text("🧹 Cleaning thumbnail...")

    subprocess.run(['mkvpropedit', old_path, '--delete', 'attachment:name="cover.jpg"'], check=False)

    shutil.move(old_path, new_path)

    await update.message.reply_text("🚀 Uploading...")
    await update.message.reply_document(document=InputFile(new_path), filename=f"{new_name}.mkv")

    os.remove(new_path)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Document.MimeType("video/x-matroska") | filters.VIDEO, handle_file)],
    states={ASK_FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, rename_and_clean)]},
    fallbacks=[CommandHandler("cancel", cancel)]
)

app.add_handler(CommandHandler("start", start))
app.add_handler(conv_handler)

app.run_polling()
