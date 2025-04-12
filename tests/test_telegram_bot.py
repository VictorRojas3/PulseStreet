import asyncio
import httpx
import logging
import time

try:
    from telegram_bot import send_telegram_alert
    from config import (
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        logger, 
        LOG_LEVEL,
        IS_CONFIG_VALID 
    )
except ImportError as e:
    logging.basicConfig(level=logging.INFO)
    logging.error(f"Failed to import modules. Ensure config.py and telegram_bot.py exist and are correct. Error: {e}")
    exit(1)
except Exception as e:
    logging.basicConfig(level=logging.INFO)
    logging.error(f"An unexpected error occurred during module import: {e}")
    exit(1)


async def run_telegram_test():
    """Runs the telegram alert function and reports success/failure."""

    logger.info("--- Starting Telegram Bot Test ---")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TEST FAILED: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing in your .env file or config.py.")
        return 
    if not IS_CONFIG_VALID:
         logger.warning("Note: Overall essential configuration validation failed (other API keys might be missing), "
                        "but proceeding with Telegram test as its specific keys seem present.")

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
   
    test_message = (
        f"✅ *Telegram Bot Test Message*\n\n"
        f"Timestamp: `{timestamp}`\n"
        f"Target Chat ID: `{TELEGRAM_CHAT_ID}`\n\n"
        f"If you see this message, the bot token is valid, the chat ID is correct, "
        f"and the `send_telegram_alert` function works!"
    )
    logger.info(f"Attempting to send test message to Chat ID: {TELEGRAM_CHAT_ID}")
    logger.debug(f"Test message content:\n{test_message}") 

    success = False
    try:
        async with httpx.AsyncClient() as client:
            success = await send_telegram_alert(
                client=client,
                bot_token=TELEGRAM_BOT_TOKEN,
                chat_id=TELEGRAM_CHAT_ID,
                message=test_message
            )

        if success:
            logger.info("✅ TEST SUCCEEDED: Message sent successfully via Telegram API.")
            print("\n>>> Check your Telegram client (User chat, Group, or Channel) for the test message! <<<")
        else:
            logger.error("❌ TEST FAILED: The send_telegram_alert function indicated failure. "
                         "Check the logs above this message for specific API errors (e.g., 400 Bad Request, 403 Forbidden, 404 Not Found).")
            logger.error("Common Causes:")
            logger.error("  - Bot token incorrect or revoked.")
            logger.error("  - Chat ID incorrect.")
            logger.error("  - Bot not added to the group/channel.")
            logger.error("  - Bot doesn't have 'Post messages' permission in the channel.")
            logger.error("  - Network issues.")

    except asyncio.CancelledError:
        logger.info("Telegram test run cancelled.")
    except Exception as e:
        logger.error(f"❌ TEST FAILED: An unexpected error occurred during test execution: {e}", exc_info=True)


if __name__ == "__main__":
    logger.info("Running telegram_bot.py test script...")
    try:
        asyncio.run(run_telegram_test())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user (Ctrl+C).")
    finally:
        logger.info("--- Telegram Bot Test Finished ---")