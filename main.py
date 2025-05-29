from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import os
import asyncio

TOKEN = os.environ.get("BOT_TOKEN")

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is up and running!"

# This keeps the app alive and starts the bot
@app.before_first_request
def start_bot():
    asyncio.create_task(run_bot())

async def run_bot():
    app_telegram = Application.builder().token(TOKEN).build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hello from your Render bot!")

    app_telegram.add_handler(CommandHandler("start", start))

    await app_telegram.initialize()
    await app_telegram.start()
    await app_telegram.updater.start_polling()
    await app_telegram.updater.idle()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
