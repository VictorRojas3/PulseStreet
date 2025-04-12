# twitter.py
import httpx
import logging
from config import TWITTER_MAX_RESULTS # Import config
import json 

# Use module-specific logger
logger = logging.getLogger(__name__)

async def fetch_recent_tweets(client: httpx.AsyncClient, bearer_token: str, search_term: str):
    """
    Fetches recent tweets asynchronously based on search term.
    Based on test_twitter.py logic. Requires bearer_token and search_term as args.
    """
    if not bearer_token:
        # Logged in main.py already, but good to double-check
        logger.debug("Bearer token not provided to fetch_recent_tweets.")
        return [] # Return empty list if no token

    try:
        headers = {"Authorization": f"Bearer {bearer_token}"}
        # Use hashtag/keyword search term passed as argument
        # Ensure it's properly URL encoded? httpx usually handles params well.
        # Query constructed based on test_twitter.py and free tier limits
        query = f"({search_term}) -is:retweet lang:en" # Assumes search_term is like "#ETH" or "#BTC"
        params = {
            "query": query,
            "max_results": TWITTER_MAX_RESULTS, # Use value from config (min 10)
            "tweet.fields": "created_at", # Optional: helps verify recency
        }
        url = "https://api.twitter.com/2/tweets/search/recent"

        logger.info(f"Fetching up to {TWITTER_MAX_RESULTS} tweets with query: '{query}'")
        # Use a reasonable timeout for the Twitter API call itself
        response = await client.get(url, headers=headers, params=params, timeout=10.0)

        # Check for API errors specifically
        if response.status_code >= 400:
             logger.error(f"Twitter API Error {response.status_code}: {response.text}")
             # Don't raise, just return empty list as context is optional
             return []

        # Process successful response
        data = response.json()
        tweets = [tweet.get('text', '') for tweet in data.get('data', [])]
        logger.info(f"Successfully fetched {len(tweets)} tweets for context.")
        return tweets

    # Catch specific httpx errors
    except httpx.TimeoutException:
        logger.error("Twitter API request timed out.")
    except httpx.RequestError as e:
        logger.error(f"Twitter API connection error: {e}")
    # Catch potential JSON errors if response isn't valid JSON
    except json.JSONDecodeError as e:
         logger.error(f"Failed to decode Twitter API JSON response: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}")
    except Exception as e:
        logger.error(f"Unexpected error fetching tweets: {e}", exc_info=True)

    return [] # Return empty list on any error