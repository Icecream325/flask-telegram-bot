from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import CommandHandler, Dispatcher, Application

import os
import logging
import asyncio

TOKEN = os.getenv("BOT_TOKEN")  # Load from environment

app = Flask(__name__)
bot = Bot(token=TOKEN)

@app.route("/")
def home():
    return "Bot is running!"

@app.route("/start-bot")
def start_bot():
    asyncio.run(start_polling())
    return "Bot started!"

async def start_polling():
    application = Application.builder().token(TOKEN).build()

    async def start(update: Update, context):
        await update.message.reply_text("Hello from Render!")

    application.add_handler(CommandHandler("start", start))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
