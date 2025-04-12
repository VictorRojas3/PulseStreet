# test_telegram.py
import asyncio
import httpx
import logging
import time

# Import necessary functions/variables from your modules
try:
    # Assuming send_telegram_alert is in telegram_bot.py
    from telegram_bot import send_telegram_alert
    # Import config variables needed for this test
    from config import (
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        logger, # Use the logger already configured in config.py
        LOG_LEVEL,
        IS_CONFIG_VALID # Check if overall essential config is valid
    )
except ImportError as e:
    # Fallback logging if config import fails severely
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

    # --- Validation ---
    # Check essential config specifically needed for this test
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TEST FAILED: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing in your .env file or config.py.")
        return # Exit the async function

    # Optional: Check the overall config validation status from config.py
    # This checks if *other* essential keys (like Whale Alert, LLaMA) are set.
    # It's okay if these are missing for *this specific test*, but good to note.
    if not IS_CONFIG_VALID:
         logger.warning("Note: Overall essential configuration validation failed (other API keys might be missing), "
                        "but proceeding with Telegram test as its specific keys seem present.")

    # --- Test Message ---
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    # Use MarkdownV2 for formatting - requires escaping special chars like '.'
    # Let's stick to simpler Markdown for now unless needed
    test_message = (
        f"✅ *Telegram Bot Test Message*\n\n"
        f"Timestamp: `{timestamp}`\n"
        f"Target Chat ID: `{TELEGRAM_CHAT_ID}`\n\n"
        f"If you see this message, the bot token is valid, the chat ID is correct, "
        f"and the `send_telegram_alert` function works!"
    )
    logger.info(f"Attempting to send test message to Chat ID: {TELEGRAM_CHAT_ID}")
    logger.debug(f"Test message content:\n{test_message}") # Log the message at debug level

    # --- Execution ---
    success = False
    try:
        # Create a temporary client for this test
        async with httpx.AsyncClient() as client:
            # Call the actual sending function from telegram_bot.py
            success = await send_telegram_alert(
                client=client,
                bot_token=TELEGRAM_BOT_TOKEN,
                chat_id=TELEGRAM_CHAT_ID,
                message=test_message
                # parse_mode should be handled within send_telegram_alert if needed
            )

        # --- Report Result ---
        if success:
            logger.info("✅ TEST SUCCEEDED: Message sent successfully via Telegram API.")
            print("\n>>> Check your Telegram client (User chat, Group, or Channel) for the test message! <<<")
        else:
            # The error should have been logged within send_telegram_alert already
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
        # Catch any unexpected errors during client creation or the call itself
        logger.error(f"❌ TEST FAILED: An unexpected error occurred during test execution: {e}", exc_info=True)


if __name__ == "__main__":
    # Logging is already configured by importing config.py, so no need for basicConfig here
    # unless the import itself fails (handled above).

    logger.info("Running telegram_bot.py test script...")
    try:
        asyncio.run(run_telegram_test())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user (Ctrl+C).")
    finally:
        logger.info("--- Telegram Bot Test Finished ---")