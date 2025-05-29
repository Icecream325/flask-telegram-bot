from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import os
import threading
import asyncio

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

# Create the Telegram bot app
telegram_app = Application.builder().token(TOKEN).build()

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hello from your bot on Render!")

# Add handler
telegram_app.add_handler(CommandHandler("start", start))

# Run the bot in a background thread
def run_bot():
    asyncio.run(_run_bot())

async def _run_bot():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    await telegram_app.updater.idle()

# Start the bot thread when Flask launches
threading.Thread(target=run_bot).start()

# Web route (optional)
@app.route("/")
def index():
    return "🚀 Flask + Telegram Bot running on Render!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
