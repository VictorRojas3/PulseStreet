# main.py
import asyncio
import httpx
import time
import logging
import os 
import config 
if not config.IS_CONFIG_VALID:
    logging.critical("Essential configuration is invalid. Exiting.")
    exit(1)
from alerts import listen_for_alerts
from twitter import fetch_recent_tweets
from llama import analyze_with_llama 
from telegram_bot import send_telegram_alert

"""
Handles the full workflow for processing a single whale alert:
1. Formats whale data.
2. Fetches Twitter context (optional, uses client).
3. Analyzes with LLaMA via Cerebras SDK (handled in llama.py).
4. Sends formatted alert to Telegram (uses client).
"""

logger = logging.getLogger(__name__)

async def process_alert(client: httpx.AsyncClient, whale_data: dict):
    start_process_time = time.monotonic()
    symbol = whale_data.get('symbol', 'UNKNOWN')
    if not symbol or symbol == 'UNKNOWN':
        logger.warning(f"Skipping processing for alert with missing/unknown symbol: {whale_data}")
        return
    logger.info(f"Processing {symbol} alert...")
    try:
        whale_summary = (
            f"{float(whale_data['amount']):,.2f} {symbol} (${float(whale_data['value_usd']):,.0f} USD) "
            f"transferred from '{whale_data.get('from_owner', 'unknown')}' to '{whale_data.get('to_owner', 'unknown')}'."
        )
    except (ValueError, TypeError) as e:
         logger.error(f"Could not format whale summary due to invalid amount/value: {e}. Data: {whale_data}")
         whale_summary = f"Whale movement detected for {symbol} (details formatting error)."
    tweets = []
    dynamic_search_term = f"#{symbol}"
    if config.TWITTER_BEARER_TOKEN:
        logger.info(f"Fetching Twitter context using search term: '{dynamic_search_term}'")
        tweets = await fetch_recent_tweets(
            client, 
            config.TWITTER_BEARER_TOKEN,
            dynamic_search_term
        )
    else:
        logger.info("Skipping Twitter fetch as token is not configured.")
    logger.info(f"Sending data for {symbol} to LLaMA via Cerebras SDK for analysis...")
    analysis, inference_time = await analyze_with_llama(
        whale_summary,
        tweets,
        symbol
    )
    total_latency = time.monotonic() - start_process_time
    alert_message = f"🚨 **Real-Time {symbol} Alert** 🚨\n\n"
    alert_message += f"**Whale Movement:**\n`{whale_summary}`\n\n"
    if config.TWITTER_BEARER_TOKEN:
        if tweets:
            alert_message += f"**Recent Twitter Buzz ({dynamic_search_term}):**\n"
            for t in tweets:
                escaped_tweet = t.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')
                alert_message += f"- _{escaped_tweet[:150]}..._\n"
            alert_message += "\n"
        else:
            alert_message += f"_(No recent Twitter context found/fetched for {dynamic_search_term})_\n\n"
    alert_message += f"**LLaMA Analysis ({config.CEREBRAS_MODEL_ID}):**\n{analysis}\n\n"
    alert_message += f"⏱️ *LLaMA Inference: {inference_time:.2f}s | Total Processing: {total_latency:.2f}s*"
    logger.info(f"Sending alert for {symbol} to Telegram...")
    await send_telegram_alert(
        client, 
        config.TELEGRAM_BOT_TOKEN,
        config.TELEGRAM_CHAT_ID,
        alert_message
    )
    logger.info(f"Alert processing for {symbol} completed in {total_latency:.2f}s.")


async def run_alerter():
    """Main application loop: Listens for alerts and schedules processing."""
    logger.info("==================================================")
    logger.info(f"🚀 Starting PulseStreet Alerter (FlashBot)")
    logger.info(f"   Monitoring Symbols : {', '.join(config.WHALE_SUBSCRIPTION_MSG.get('symbols', [])).upper()}")
    logger.info(f"   Whale Threshold    : >= ${config.WHALE_SUBSCRIPTION_MSG.get('min_value_usd', 0):,}")
    logger.info(f"   LLM Engine         : Cerebras SDK")
    logger.info(f"   LLM Model          : {config.CEREBRAS_MODEL_ID}")
    logger.info(f"   Twitter Context    : {'Enabled' if config.TWITTER_BEARER_TOKEN else 'Disabled'}")
    logger.info(f"   Target Chat        : {config.TELEGRAM_CHAT_ID}")
    logger.info("==================================================")
    timeout_config = httpx.Timeout(30.0, read=None)
    async with httpx.AsyncClient(timeout=timeout_config) as client:
        logger.info("Created shared HTTP client (for Twitter/Telegram).")
        alert_generator = listen_for_alerts(config.WHALE_ALERT_WSS_URL, config.WHALE_SUBSCRIPTION_MSG)
        logger.info("Waiting for whale alerts...")
        async for whale_alert_data in alert_generator:
            logger.debug(f"Received raw alert data: {whale_alert_data}")
            asyncio.create_task(process_alert(client, whale_alert_data))
    logger.info("Alerter main loop finished (HTTP client closed).")


if __name__ == "__main__":
    try:
        if not os.environ.get("CEREBRAS_API_KEY") and config.CEREBRAS_API_KEY:
            logger.info("Setting CEREBRAS_API_KEY in environment from config for SDK.")
            os.environ["CEREBRAS_API_KEY"] = config.CEREBRAS_API_KEY
        if not os.environ.get("CEREBRAS_API_KEY"):
             logger.critical("CEREBRAS_API_KEY not found in environment. Cannot initialize SDK in llama.py.")
             exit(1)
        asyncio.run(run_alerter())
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user (Ctrl+C).")
    except Exception as e:
        logger.critical(f"Unhandled exception in main execution: {e}", exc_info=True)
    finally:
        logger.info("PulseStreet Alerter stopped.")
