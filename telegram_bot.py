import httpx
import logging
from telegram.constants import ParseMode 
from config import TELEGRAM_TIMEOUT_SECONDS 
import json

"""
Sends an alert message to the specified Telegram chat using httpx, in this case to a telegram channel 
with all the info.
"""

logger = logging.getLogger(__name__)

async def send_telegram_alert(client: httpx.AsyncClient, bot_token: str, chat_id: str, message: str):
    if not bot_token or not chat_id:
        logger.error("Telegram bot token or chat ID is missing. Cannot send alert.")
        return False 
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': ParseMode.MARKDOWN 
        }
        logger.debug(f"Sending message to Telegram chat ID: {chat_id}")
        response = await client.post(url, json=payload, timeout=TELEGRAM_TIMEOUT_SECONDS)
        if response.status_code >= 400:
             logger.error(f"Telegram API Error {response.status_code}: {response.text}")
             return False
        else:
            logger.info("Telegram alert sent successfully!")
            return True 
    except httpx.TimeoutException:
         logger.error(f"Telegram API request timed out after {TELEGRAM_TIMEOUT_SECONDS} seconds.")
    except httpx.RequestError as e:
        logger.error(f"Telegram API connection error: {e}")
    except json.JSONDecodeError as e:
         logger.error(f"Failed to decode Telegram API JSON response: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}")
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram alert: {e}", exc_info=True)
    return False