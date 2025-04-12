# telegram_bot.py
import httpx
import logging
from telegram.constants import ParseMode # Using constant for clarity
from config import TELEGRAM_TIMEOUT_SECONDS # Import config
import json
# Use module-specific logger
logger = logging.getLogger(__name__)

async def send_telegram_alert(client: httpx.AsyncClient, bot_token: str, chat_id: str, message: str):
    """
    Sends alert message to the specified Telegram chat using httpx.
    Based on test_telegram.py logic. Returns True on success, False on failure.
    """
    if not bot_token or not chat_id:
        logger.error("Telegram bot token or chat ID is missing. Cannot send alert.")
        return False # Indicate failure

    try:
        # Construct API URL and payload
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': ParseMode.MARKDOWN # Default to Markdown
            # Add 'disable_web_page_preview': True if needed
        }
        logger.debug(f"Sending message to Telegram chat ID: {chat_id}")

        # Make the API call using the shared client
        response = await client.post(url, json=payload, timeout=TELEGRAM_TIMEOUT_SECONDS)

        # Check response status
        if response.status_code >= 400:
             logger.error(f"Telegram API Error {response.status_code}: {response.text}")
             return False # Indicate failure
        else:
            # Success path
            logger.info("Telegram alert sent successfully!")
            return True # Indicate success

    # Handle httpx-specific errors
    except httpx.TimeoutException:
         logger.error(f"Telegram API request timed out after {TELEGRAM_TIMEOUT_SECONDS} seconds.")
    except httpx.RequestError as e:
        logger.error(f"Telegram API connection error: {e}")
    # Handle potential JSON errors if Telegram response changes unexpectedly
    except json.JSONDecodeError as e:
         logger.error(f"Failed to decode Telegram API JSON response: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}")
    # Catch any other unexpected exceptions
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram alert: {e}", exc_info=True)

    return False # Indicate failure if any exception occurred