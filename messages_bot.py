import os
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram.error import TelegramError
import logging
from datetime import datetime
from config import messages_collection, users_collection

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_ID')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def save_to_db(data):
    collection = messages_collection()
    collection.insert_one(data)

def process_message(update):
    message = update.message
    user = message.from_user
    chat = message.chat

    data = {
        "timestamp": datetime.now(),
        "message_id": message.message_id,
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_bot": user.is_bot,
            "language_code": user.language_code
        },
        "chat": {
            "id": chat.id,
            "type": chat.type,
            "title": chat.title
        },
        "message_type": "text",
        "text": message.text,
        "entities": [{"type": entity.type, "offset": entity.offset, "length": entity.length} for entity in message.entities] if message.entities else [],
        "reply_to_message_id": message.reply_to_message.message_id if message.reply_to_message else None,
        "forward_from": message.forward_from.id if message.forward_from else None,
        "forward_from_chat": message.forward_from_chat.id if message.forward_from_chat else None,
        "forward_date": message.forward_date.isoformat() if message.forward_date else None,
        "edit_date": message.edit_date.isoformat() if message.edit_date else None,
        "media_group_id": message.media_group_id,
        "author_signature": message.author_signature,
    }

    for attr in ['has_protected_content', 'has_media_spoiler']:
        if hasattr(message, attr):
            data[attr] = getattr(message, attr)

    if message.photo:
        data["message_type"] = "photo"
        data["photo"] = [{"file_id": photo.file_id, "file_unique_id": photo.file_unique_id, "width": photo.width, "height": photo.height, "file_size": photo.file_size} for photo in message.photo]
        data["caption"] = message.caption

    elif message.document:
        data["message_type"] = "document"
        data["document"] = {"file_id": message.document.file_id, "file_name": message.document.file_name, "mime_type": message.document.mime_type, "file_size": message.document.file_size}

    elif message.video:
        data["message_type"] = "video"
        data["video"] = {"file_id": message.video.file_id, "width": message.video.width, "height": message.video.height, "duration": message.video.duration, "file_name": message.video.file_name, "mime_type": message.video.mime_type, "file_size": message.video.file_size}

    elif message.audio:
        data["message_type"] = "audio"
        data["audio"] = {"file_id": message.audio.file_id, "duration": message.audio.duration, "performer": message.audio.performer, "title": message.audio.title, "file_name": message.audio.file_name, "mime_type": message.audio.mime_type, "file_size": message.audio.file_size}

    elif message.voice:
        data["message_type"] = "voice"
        data["voice"] = {"file_id": message.voice.file_id, "duration": message.voice.duration, "mime_type": message.voice.mime_type, "file_size": message.voice.file_size}

    elif message.sticker:
        data["message_type"] = "sticker"
        sticker_data = {
            "file_id": message.sticker.file_id,
            "width": message.sticker.width,
            "height": message.sticker.height,
            "is_animated": message.sticker.is_animated,
            "emoji": message.sticker.emoji,
            "set_name": message.sticker.set_name,
            "file_size": message.sticker.file_size
        }
        if hasattr(message.sticker, 'is_video'):
            sticker_data["is_video"] = message.sticker.is_video
        data["sticker"] = sticker_data
    return data


def wallet_handler(update, context):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /wallet <wallet_address>")
        return
    
    wallet_address = context.args[0]
    logger.info(f"Received wallet command with address: {wallet_address}")
    
    update.message.reply_text("Nice!")


def all_message_handler(update, context):
    try:
        data = process_message(update)
        logger.info(f"Received {data['message_type']} in group {data['chat']['id']} from {'bot' if data['user']['is_bot'] else 'user'} {data['user']['id']}")
        save_to_db(data)
    except AttributeError as e:
        logger.error(f"AttributeError in message processing: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in message handling: {e}")



def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('wallet', wallet_handler))

    dispatcher.add_handler(MessageHandler(Filters.all, all_message_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()