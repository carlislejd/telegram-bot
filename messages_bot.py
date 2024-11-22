import os
import logging
from telegram.ext import Updater, MessageHandler, Filters
from bot_commands import add_command_handlers
from config import messages_collection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_ID")

def save_to_db(data):
    collection = messages_collection()
    collection.insert_one(data)

def process_message(update):
    message = update.message
    user = message.from_user
    chat = message.chat

    data = {
        "timestamp": message.date,
        "message_id": message.message_id,
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_bot": user.is_bot,
            "language_code": user.language_code,
        },
        "chat": {"id": chat.id, "type": chat.type, "title": chat.title},
        "text": message.text,
    }
    return data

def all_message_handler(update, context):
    """Handle all incoming messages."""
    try:
        data = process_message(update)
        logger.info(f"Received message from {data['user']['id']}")
        save_to_db(data)
    except Exception as e:
        logger.error(f"Error in message handler: {e}")

def main():
    """Main entry point for the bot."""
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Add command handlers from bot_commands.py
    add_command_handlers(dispatcher)

    # Add a message handler for all text messages
    dispatcher.add_handler(MessageHandler(Filters.all, all_message_handler))

    # Start the bot
    updater.start_polling()
    logger.info("Bot started and polling for updates.")
    updater.idle()

if __name__ == "__main__":
    main()
