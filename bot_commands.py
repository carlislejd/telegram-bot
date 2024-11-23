import os
import random
import requests
import logging
from datetime import datetime, timedelta
from telegram.ext import CommandHandler

# Logger setup
logger = logging.getLogger(__name__)

# API Configuration
API_KEY = os.getenv('ANKR')
ANKR_MULTICHAIN = f'https://rpc.ankr.com/multichain/{API_KEY}'
HEADERS = {'Content-Type': 'application/json'}

# Function to fetch all NFT transfers
def fetch_all_nft_transfers(owner_address):
    transfers = []
    page_token = None
    url = ANKR_MULTICHAIN.replace('/multichain', '/multichain/?ankr_getNftTransfers')

    while True:
        payload = {
            "jsonrpc": "2.0",
            "method": "ankr_getNftTransfers",
            "params": {
                "address": [owner_address],
                "pageSize": 10000
            },
            "id": 1
        }

        if page_token:
            payload["params"]["pageToken"] = page_token

        try:
            response = requests.post(url, json=payload, headers=HEADERS)
            response.raise_for_status()
            data = response.json()

            if 'result' not in data or 'transfers' not in data['result']:
                break

            transfers.extend(data['result']['transfers'])

            if 'nextPageToken' in data['result']:
                page_token = data['result']['nextPageToken']
            else:
                break
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data for address {owner_address}: {e}")
            return []

    return transfers

# Handler for /wallet_nft
def wallet_nft_handler(update, context):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /wallet_nft <wallet_address>")
        return

    wallet_address = context.args[0].lower()
    logger.info(f"Fetching NFT data for wallet: {wallet_address}")

    # Fetch NFT transfers
    transfers = fetch_all_nft_transfers(wallet_address)
    if not transfers:
        update.message.reply_text(f"No NFT transfer data found for wallet {wallet_address}.")
        return

    try:
        # Process transfers
        total_records = len(transfers)
        unique_types = len(set(transfer.get('type') for transfer in transfers if 'type' in transfer))
        unique_type_counts = {}
        count_by_direction = {'sent': 0, 'received': 0}
        earliest_timestamp = float('inf')
        most_recent_timestamp = float('-inf')
        image_urls = []

        for transfer in transfers:
            # Calculate direction
            from_address = transfer.get('fromAddress', '').lower()
            to_address = transfer.get('toAddress', '').lower()
            if from_address == wallet_address:
                direction = 'sent'
            elif to_address == wallet_address:
                direction = 'received'
            else:
                direction = 'other'

            # Update counts
            count_by_direction[direction] = count_by_direction.get(direction, 0) + 1

            # Track unique types
            nft_type = transfer.get('type')
            if nft_type:
                unique_type_counts[nft_type] = unique_type_counts.get(nft_type, 0) + 1

            # Track timestamps
            timestamp = transfer.get('timestamp')
            if timestamp:
                earliest_timestamp = min(earliest_timestamp, timestamp)
                most_recent_timestamp = max(most_recent_timestamp, timestamp)

            # Collect image URLs
            image_url = transfer.get('imageUrl')
            if image_url:
                image_urls.append(image_url)

        # Convert timestamps to human-readable format
        if earliest_timestamp != float('inf'):
            earliest_datetime = datetime.utcfromtimestamp(earliest_timestamp)
            earliest_timestamp_str = earliest_datetime.strftime('%Y-%m-%d %H:%M:%S')
        else:
            earliest_timestamp_str = "N/A"

        if most_recent_timestamp != float('-inf'):
            most_recent_datetime = datetime.utcfromtimestamp(most_recent_timestamp)
            most_recent_timestamp_str = most_recent_datetime.strftime('%Y-%m-%d %H:%M:%S')
        else:
            most_recent_timestamp_str = "N/A"

        # Categorization
        current_datetime = datetime.utcnow()
        og_status = (
            "You're an OG! Your first transaction was over 3 years ago. 🎉"
            if earliest_datetime and earliest_datetime < current_datetime - timedelta(days=3 * 365)
            else "You're relatively new, but there's always room to grow!"
        )

        records_bucket = (
            "You're just getting started with fewer than 500 transactions. 🚀"
            if total_records <= 500 else
            "You're on your way with a solid 501-1500 transactions. 💪"
            if 501 <= total_records <= 1500 else
            "Impressive! You have between 1501-3000 transactions. 🌟"
            if 1501 <= total_records <= 3000 else
            "You're a true power user with over 3000 transactions! 🔥"
        )

        received_count = count_by_direction.get('received', 0)
        sent_count = count_by_direction.get('sent', 0)

        giver_taker_label = (
            "You're a receiver! You love collecting from others. 🎁"
            if received_count > sent_count else
            "You're a giver! Sharing is your middle name. ❤️"
            if sent_count > received_count else
            "You're perfectly balanced, like all things should be. ⚖️"
        )

        random_image_url = random.choice(image_urls) if image_urls else "No image available"

        # Prepare report
        report = (
            f"**NFT Wallet Report for {wallet_address}**\n\n"
            f"**Total Records:** {total_records}\n"
            f"**Unique Types:** {unique_types}\n"
            f"**Unique Types Breakdown:** {unique_type_counts}\n"
            f"**Earliest Transaction:** {earliest_timestamp_str}\n"
            f"**Most Recent Transaction:** {most_recent_timestamp_str}\n"
            f"**Received vs Sent:** {count_by_direction}\n\n"
            f"{og_status}\n"
            f"{records_bucket}\n"
            f"{giver_taker_label}\n\n"
            f"**Here's a random NFT image from your collection:**\n{random_image_url}"
        )

        # Send report
        update.message.reply_text(report)
    except Exception as e:
        logger.error(f"Error processing data for wallet {wallet_address}: {e}")
        update.message.reply_text("An error occurred while generating the report. Please try again later.")


# Add the other handlers as-is
def wallet_token_handler(update, context):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /wallet_token <wallet_address>")
        return

    wallet_address = context.args[0]
    update.message.reply_text(f"Token data for {wallet_address} will be implemented soon!")

def commands_handler(update, context):
    commands_list = """
    Available Commands:
    - /wallet_nft <wallet_address>: Fetch NFT data for the specified wallet.
    - /wallet_token <wallet_address>: Fetch token data for the specified wallet.
    - /commands: Show this list of commands.
    """
    update.message.reply_text(commands_list)

def add_command_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler('wallet_nft', wallet_nft_handler))
    dispatcher.add_handler(CommandHandler('wallet_token', wallet_token_handler))
    dispatcher.add_handler(CommandHandler('commands', commands_handler))

