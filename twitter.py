import httpx
import logging
from config import TWITTER_MAX_RESULTS 
import json 

"""
Uses the Twitter API v2 to search for tweets containing the alert symbol.
"""

logger = logging.getLogger(__name__)

async def fetch_recent_tweets(client: httpx.AsyncClient, bearer_token: str, search_term: str):
    if not bearer_token:
        logger.debug("Bearer token not provided to fetch_recent_tweets.")
        return [] 
    try:
        headers = {"Authorization": f"Bearer {bearer_token}"}
        query = f"({search_term}) -is:retweet lang:en" 
        params = {
            "query": query,
            "max_results": TWITTER_MAX_RESULTS, 
            "tweet.fields": "created_at", 
        }
        url = "https://api.twitter.com/2/tweets/search/recent"
        logger.info(f"Fetching up to {TWITTER_MAX_RESULTS} tweets with query: '{query}'")
        response = await client.get(url, headers=headers, params=params, timeout=10.0)
        if response.status_code >= 400:
             logger.error(f"Twitter API Error {response.status_code}: {response.text}")
             return []
        data = response.json()
        tweets = [tweet.get('text', '') for tweet in data.get('data', [])]
        logger.info(f"Successfully fetched {len(tweets)} tweets for context.")
        return tweets
    except httpx.TimeoutException:
        logger.error("Twitter API request timed out.")
    except httpx.RequestError as e:
        logger.error(f"Twitter API connection error: {e}")
    except json.JSONDecodeError as e:
         logger.error(f"Failed to decode Twitter API JSON response: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}")
    except Exception as e:
        logger.error(f"Unexpected error fetching tweets: {e}", exc_info=True)
    return [] 