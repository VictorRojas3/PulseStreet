# test_twitter.py
import asyncio
import httpx
import logging

# Import necessary functions/variables from your modules
try:
    from twitter import fetch_recent_tweets
    # Import config variables needed for this test
    from config import TWITTER_BEARER_TOKEN, TWITTER_SEARCH_TERM, logger, LOG_LEVEL, IS_CONFIG_VALID
except ImportError as e:
    print(f"Failed to import modules. Ensure config.py and twitter.py exist and are correct. Error: {e}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred during config import: {e}")
    exit(1)


async def run_twitter_test():
    """Runs the twitter fetch function and prints the results."""

    # Explicitly check if the Twitter token is loaded, crucial for this test
    if not TWITTER_BEARER_TOKEN:
         logger.error("TWITTER_BEARER_TOKEN is not set in your .env file or config.py. Cannot run test.")
         return # Exit the async function

    # IS_CONFIG_VALID checks all essential keys, which might not include Twitter if it's optional.
    # So, the direct check above is more important here.
    # if not IS_CONFIG_VALID:
    #     logger.warning("Note: Overall configuration validation failed, but proceeding with Twitter test as token is present.")

    logger.info(f"Starting Twitter API test...")
    logger.info(f"Fetching up to {TWITTER_MAX_RESULTS} recent tweets for search term: '{TWITTER_SEARCH_TERM}'") # Assuming TWITTER_MAX_RESULTS is also in config

    tweet_list = []
    try:
        # Create an httpx client session for the test
        async with httpx.AsyncClient() as client:
            # Call the function from twitter.py
            tweet_list = await fetch_recent_tweets(
                client=client,
                bearer_token=TWITTER_BEARER_TOKEN,
                search_term=TWITTER_SEARCH_TERM
                # max_results is likely handled by the default in fetch_recent_tweets
                # or uses TWITTER_MAX_RESULTS from config.py internally
            )

        # Process and print results
        if tweet_list:
            logger.info(f"Successfully retrieved {len(tweet_list)} tweets:")
            for i, tweet_text in enumerate(tweet_list):
                print(f"  Tweet {i+1}: {tweet_text[:100]}...") # Print first 100 chars
        elif tweet_list == []: # Explicitly check for empty list (could be no results or an error handled inside fetch_recent_tweets)
            logger.warning("Received an empty list. This could mean:")
            logger.warning("  1. No recent tweets matched your search criteria.")
            logger.warning("  2. An error occurred during the fetch (check logs from twitter.py if available).")
            logger.warning("  3. You might have hit the API rate limit (unlikely with only 3 results).")
        else:
             # Should not happen if fetch_recent_tweets returns list or None
             logger.error(f"Received unexpected result type: {type(tweet_list)}")


    except asyncio.CancelledError:
        logger.info("Twitter test run cancelled.")
    except Exception as e:
        # Catch any unexpected errors during client creation or the call
        logger.error(f"An error occurred during the Twitter test execution: {e}", exc_info=True)


if __name__ == "__main__":
    # Setup basic logging for the test script itself
    # Use the level defined in config if available, otherwise default to INFO
    log_level_to_use = LOG_LEVEL if 'LOG_LEVEL' in locals() else logging.INFO
    logging.basicConfig(level=log_level_to_use, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Assuming TWITTER_MAX_RESULTS exists in config, else define it here for clarity
    try:
        from config import TWITTER_MAX_RESULTS
    except ImportError:
        TWITTER_MAX_RESULTS = 10 # Fallback if not in config
        logger.warning("TWITTER_MAX_RESULTS not found in config, defaulting to 3 for test.")


    logger.info("Running twitter.py test script...")
    try:
        asyncio.run(run_twitter_test())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user (Ctrl+C).")
    finally:
        logger.info("Twitter test finished.")