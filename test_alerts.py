# test_alerts.py
import asyncio
import logging

# Import the specific function and config variables needed from your modules
from alerts import listen_for_alerts
try:
    from config import WHALE_ALERT_WSS_URL, WHALE_SUBSCRIPTION_MSG, IS_CONFIG_VALID, logger
except ImportError as e:
    print(f"Failed to import configuration. Ensure config.py and .env exist and are correct. Error: {e}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred during config import: {e}")
    exit(1)


async def run_test():
    """Runs the alert listener and prints yielded data."""

    if not IS_CONFIG_VALID:
         logger.error("Essential configuration is missing or invalid (check config.py validation). Cannot run test.")
         # Specifically check the needed variable for clarity
         if not WHALE_ALERT_WSS_URL or "?api_key=None" in WHALE_ALERT_WSS_URL:
             logger.error("WHALE_ALERT_API_KEY seems missing in .env, resulting in invalid WSS URL.")
         return # Exit the async function

    # Check if the specific URL looks okay (basic sanity check)
    if not WHALE_ALERT_WSS_URL or "?api_key=None" in WHALE_ALERT_WSS_URL:
         logger.error("WHALE_ALERT_WSS_URL is not configured correctly. Check your .env file.")
         return

    logger.info("Starting test for alerts.py...")
    alert_count = 0
    max_alerts_to_receive = 3 # Limit how many alerts to print before stopping automatically

    try:
        # Create the generator by calling the listener function
        alert_generator = listen_for_alerts(WHALE_ALERT_WSS_URL, WHALE_SUBSCRIPTION_MSG)

        # Iterate through the alerts yielded by the generator
        async for parsed_alert in alert_generator:
            alert_count += 1
            logger.info(f"--- Alert #{alert_count} Received ---")
            print(parsed_alert) # Print the dictionary
            logger.info("--------------------------")

            # Optional: Stop after receiving a few alerts
            if alert_count >= max_alerts_to_receive:
                logger.info(f"Received {max_alerts_to_receive} alerts. Stopping test.")
                break

    except asyncio.CancelledError:
        logger.info("Test run cancelled.")
    except Exception as e:
        logger.error(f"An error occurred during the alert test: {e}", exc_info=True)


if __name__ == "__main__":
    # Setup basic logging for the test script itself
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("Running alerts.py test script. Press Ctrl+C to stop manually if needed.")
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user (Ctrl+C).")
    finally:
        logger.info("Alerts test finished.")