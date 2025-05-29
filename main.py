from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import os
import threading
import asyncio
import sys

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable not set!")
    sys.exit(1)  # Stop the app immediately

# Create the Telegram bot application only after TOKEN is confirmed
telegram_app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hello from your bot on Render!")

telegram_app.add_handler(CommandHandler("start", start))

def run_bot():
    asyncio.run(_run_bot())

async def _run_bot():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    await telegram_app.updater.idle()

threading.Thread(target=run_bot).start()

@app.route("/")
def index():
    return "🚀 Flask + Telegram Bot running on Render!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
