import os
import requests
import logging
from telegram.ext import CommandHandler

logger = logging.getLogger(__name__)

API_KEY = os.getenv('ANKR')
ANKR_MULTICHAIN = f'https://rpc.ankr.com/multichain/{API_KEY}'
HEADERS = {'Content-Type': 'application/json'}


def wallet_nft_handler(update, context):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /wallet_nft <wallet_address>")
        return
    
    wallet_address = context.args[0]
    logger.info(f"Fetching NFT data for wallet: {wallet_address}")
    
    params = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "ankr_getNFTsByOwner",
        "params": {
            "blockchain": ["eth", "base", "arbitrum"], 
            "walletAddress": wallet_address,
            "pageSize": 10,
            "pageToken": "",
            "filter": []
        }
    }

    try:
        response = requests.post(ANKR_MULTICHAIN, headers=HEADERS, json=params)
        data = response.json()

        if "result" in data and "assets" in data["result"]:
            assets = data["result"]["assets"]
            if assets:
                nft_details = [
                    f"- {nft['name']} (Blockchain: {nft['blockchain']}, Token ID: {nft['tokenId']})"
                    for nft in assets
                ]
                nft_summary = "\n".join(nft_details[:5])
                update.message.reply_text(
                    f"Wallet {wallet_address} owns the following NFTs:\n{nft_summary}\n\nShowing up to 5 of {len(assets)} NFTs."
                )
            else:
                update.message.reply_text(f"No NFTs found for wallet {wallet_address}.")
        else:
            update.message.reply_text(f"Could not retrieve NFT data for wallet {wallet_address}. Please try again later.")

    except Exception as e:
        logger.error(f"Error fetching NFT data: {e}")
        update.message.reply_text("An error occurred while fetching the NFT data. Please try again later.")


def wallet_token_handler(update, context):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /wallet_token <wallet_address>")
        return

    wallet_address = context.args[0]
    logger.info(f"Fetching token data for wallet: {wallet_address}")
    update.message.reply_text(f"Token data for {wallet_address} will be implemented soon!")

def commands_handler(update, context):
    commands_list = """
    Available Commands:
    - /wallet_nft <wallet_address>: Fetch NFT data for the specified wallet.
    - /wallet_token <wallet_address>: Fetch token data for the specified wallet.
    - /commands: Show this list of commands.
    """
    update.message.reply_text(commands_list)

# Add all command handlers to the dispatcher
def add_command_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler('wallet_nft', wallet_nft_handler))
    dispatcher.add_handler(CommandHandler('wallet_token', wallet_token_handler))
    dispatcher.add_handler(CommandHandler('commands', commands_handler))
