import asyncio
import httpx
import time
import logging
import config
if not config.IS_CONFIG_VALID:
    # Logger might not be fully configured if basic config failed,
    # but attempt logging anyway. A print might be needed if logging fails.
    logging.critical("Essential configuration is invalid. Exiting.")
    # print("CRITICAL: Essential configuration is invalid. Exiting.", file=sys.stderr)
    exit(1)

# Import module functions
from alerts import listen_for_alerts
from twitter import fetch_recent_tweets
from llama import analyze_with_llama # This now uses HF Serverless API
from telegram_bot import send_telegram_alert

# Get the logger configured in config.py
logger = logging.getLogger(__name__)

async def process_alert(client: httpx.AsyncClient, whale_data: dict):
    """
    Handles the full workflow for processing a single whale alert:
    1. Formats whale data.
    2. Fetches Twitter context (optional).
    3. Analyzes with LLaMA via HF Serverless API.
    4. Sends formatted alert to Telegram.
    """
    start_process_time = time.monotonic()
    symbol = whale_data.get('symbol', 'UNKNOWN')
    if not symbol or symbol == 'UNKNOWN':
        logger.warning(f"Skipping processing for alert with missing/unknown symbol: {whale_data}")
        return

    logger.info(f"Processing {symbol} alert...")

    # 1. Format Whale Summary
    # Using f-string formatting, ensure values are numeric for formatting codes
    try:
        whale_summary = (
            f"{float(whale_data['amount']):,.2f} {symbol} (${float(whale_data['value_usd']):,.0f} USD) "
            f"transferred from '{whale_data.get('from_owner', 'unknown')}' to '{whale_data.get('to_owner', 'unknown')}'."
        )
    except (ValueError, TypeError) as e:
         logger.error(f"Could not format whale summary due to invalid amount/value: {e}. Data: {whale_data}")
         whale_summary = f"Whale movement detected for {symbol} (details formatting error)."


    # 2. Fetch Twitter Context (Conditional)
    tweets = []
    dynamic_search_term = f"#{symbol}" # Default search term (e.g., #ETH, #BTC)
    if config.TWITTER_BEARER_TOKEN:
        logger.info(f"Fetching Twitter context using search term: '{dynamic_search_term}'")
        tweets = await fetch_recent_tweets(
            client,
            config.TWITTER_BEARER_TOKEN,
            dynamic_search_term
        )
        # Note: tweets could be empty list if API fails or no results
    else:
        logger.info("Skipping Twitter fetch as token is not configured.")


    # 3. Analyze with LLaMA (Using HF Serverless API via llama.py)
    logger.info(f"Sending data for {symbol} to LLaMA for analysis...")
    analysis, inference_time = await analyze_with_llama(
        client,          # Pass the shared httpx client
        whale_summary,   # Pass whale data string
        tweets,          # Pass list of tweet strings (can be empty)
        symbol           # Pass the symbol (e.g., 'ETH', 'BTC')
    )
    # 'analysis' will contain the generated text or an error string


    # 4. Format Telegram Message
    total_latency = time.monotonic() - start_process_time
    # Start building the message string
    alert_message = f"🚨 **Real-Time {symbol} Alert** 🚨\n\n"
    alert_message += f"**Whale Movement:**\n`{whale_summary}`\n\n" # Use markdown code block

    # Add Twitter context section if fetched
    if config.TWITTER_BEARER_TOKEN: # Check if Twitter was attempted
        if tweets:
            alert_message += f"**Recent Twitter Buzz ({dynamic_search_term}):**\n"
            for t in tweets:
                # Basic Markdown escaping for common characters
                escaped_tweet = t.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')
                alert_message += f"- _{escaped_tweet[:150]}..._\n" # Limit length, use italics
            alert_message += "\n"
        else:
            alert_message += f"_(No recent Twitter context found/fetched for {dynamic_search_term})_\n\n"

    # Add LLaMA analysis section
    alert_message += f"**LLaMA Analysis ({config.HF_MODEL_ID}):**\n{analysis}\n\n" # Mention model used

    # Add performance metrics
    alert_message += f"⏱️ *LLaMA Inference: {inference_time:.2f}s | Total Processing: {total_latency:.2f}s*"


    # 5. Send Alert to Telegram
    logger.info(f"Sending alert for {symbol} to Telegram...")
    await send_telegram_alert(
        client,
        config.TELEGRAM_BOT_TOKEN,
        config.TELEGRAM_CHAT_ID,
        alert_message
        # Assumes send_telegram_alert uses Markdown parse mode by default
    )
    logger.info(f"Alert processing for {symbol} completed in {total_latency:.2f}s.")


async def run_alerter():
    """Main application loop: Listens for alerts and schedules processing."""
    logger.info("==================================================")
    logger.info(f"🚀 Starting LLaMA Crypto Alerter")
    logger.info(f"   Monitoring Symbols : {', '.join(config.WHALE_SUBSCRIPTION_MSG.get('symbols', [])).upper()}")
    logger.info(f"   Whale Threshold    : >= ${config.WHALE_SUBSCRIPTION_MSG.get('min_value_usd', 0):,}")
    logger.info(f"   LLM Model (HF API) : {config.HF_MODEL_ID}")
    logger.info(f"   Twitter Context    : {'Enabled' if config.TWITTER_BEARER_TOKEN else 'Disabled'}")
    logger.info(f"   Target Chat        : {config.TELEGRAM_CHAT_ID}")
    logger.info("==================================================")


    # Create a single httpx client session to reuse connections efficiently
    # Apply the longer timeout globally if needed, or handle timeouts per-call
    # Setting a default timeout here for the client
    timeout_config = httpx.Timeout(config.LLAMA_TIMEOUT_SECONDS, read=None) # Use LLAMA timeout as default connect/read
    async with httpx.AsyncClient(timeout=timeout_config) as client:
        logger.info("Created shared HTTP client.")

        # Start the alert listener generator
        alert_generator = listen_for_alerts(config.WHALE_ALERT_WSS_URL, config.WHALE_SUBSCRIPTION_MSG)

        logger.info("Waiting for whale alerts...")
        # Process alerts concurrently as they arrive
        async for whale_alert_data in alert_generator:
            logger.debug(f"Received raw alert data: {whale_alert_data}")
            # Schedule process_alert to run without blocking the listener
            asyncio.create_task(process_alert(client, whale_alert_data))

    logger.info("Alerter main loop finished (HTTP client closed).") # Should not be reached unless listener exits unexpectedly


if __name__ == "__main__":
    try:
        asyncio.run(run_alerter())
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user (Ctrl+C).")
    except Exception as e:
        # Catch any unexpected errors in the main execution flow
        logger.critical(f"Unhandled exception in main execution: {e}", exc_info=True)
    finally:
        logger.info("LLaMA Crypto Alerter stopped.")