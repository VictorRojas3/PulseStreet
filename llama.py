# llama.py
import os
import time
import logging
import asyncio
from cerebras.cloud.sdk import Cerebras 
from config import CEREBRAS_API_KEY, CEREBRAS_MODEL_ID, LLAMA_MAX_TOKENS

"""
Cerebras LLaMA SDK wrapper for completions.
This module provides functions to format prompts and make synchronous calls to the Cerebras SDK for text generation.
"""

logger = logging.getLogger(__name__)

cerebras_client = None
if CEREBRAS_API_KEY:
    try:
        cerebras_client = Cerebras(api_key=CEREBRAS_API_KEY)
        logger.info("Cerebras SDK client initialized.")
    except Exception as sdk_init_e:
        logger.critical(f"Failed to initialize Cerebras SDK client: {sdk_init_e}", exc_info=True)
else:
    logger.critical("CEREBRAS_API_KEY environment variable not found.")


def format_prompt_for_completion(whale_summary: str, tweet_snippets: list, symbol: str) -> str:
    """Formats the input data into a single prompt string."""
    prompt = f"""
Analyze potential {symbol} market impact based ONLY on this fresh data:
Whale Transactions:
{whale_summary if whale_summary else 'None reported now.'}
Recent Twitter Mentions ({symbol}):
{' '.join([f'- "{t}"' for t in tweet_snippets]) if tweet_snippets else 'None relevant found.'}
Task: Briefly summarize potential short-term (1-4h) impact/sentiment for {symbol} in under 50 words. Focus: concise market sentiment (e.g., Bullish pressure, Bearish risk, Mixed).
Summary:""" 
    return prompt.strip()


def _sync_cerebras_call(prompt_str: str) -> str:
    """Synchronous function using client.completions.create."""
    if not cerebras_client:
        raise RuntimeError("Cerebras SDK client not initialized.")

    try:
        completion = cerebras_client.completions.create(
            prompt=prompt_str, 
            model=CEREBRAS_MODEL_ID,
            max_tokens=LLAMA_MAX_TOKENS, 
            temperature=0.7,
        )
        if completion.choices and len(completion.choices) > 0:
            completion_text = completion.choices[0].text
            if completion_text:
                return completion_text.strip()
            else:
                 logger.error("Cerebras API completion response text is empty.")
                 return "Error: Received empty completion text"
        else:
            logger.error(f"Cerebras API completion response structure unexpected: {completion}")
            return "Error: Could not parse Cerebras completion structure"
    except Exception as e: 
        logger.error(f"Error during Cerebras SDK completion call: {e}", exc_info=True)
        status_code = getattr(e, 'status_code', None) or getattr(e, 'status', None)
        if status_code:
            return f"Error: Cerebras API Call Failed ({status_code})"
        else:
            raise 

async def analyze_with_llama(whale_summary: str, tweet_snippets: list, symbol: str):
    """Analyzes data using Cerebras SDK (completions), handling sync call."""
    if not cerebras_client:
        logger.error("Cerebras SDK client not initialized. Cannot analyze.")
        return "Error: Cerebras client not ready.", 0.0
    prompt_str = format_prompt_for_completion(whale_summary, tweet_snippets, symbol)
    logger.info(f"Submitting prompt for {symbol} analysis via Cerebras SDK (completions)...")
    start_time = time.monotonic()
    analysis_text = "Error: Analysis failed."
    inference_time = 0.0

    try:
        analysis_text = await asyncio.to_thread(_sync_cerebras_call, prompt_str)
        inference_time = time.monotonic() - start_time
        if analysis_text.startswith("Error:"):
            logger.error(f"Cerebras analysis failed within sync call: {analysis_text}")
        else:
            logger.info(f"Cerebras Inference for {symbol} successful in {inference_time:.2f} seconds.")
    except RuntimeError as rt_e:
        logger.error(f"Cannot analyze: {rt_e}")
        analysis_text = "Error: Cerebras client initialization failed."
        inference_time = time.monotonic() - start_time
    except Exception as e:
        inference_time = time.monotonic() - start_time
        logger.error(f"Unexpected error during async execution of Cerebras call: {e}", exc_info=True)
        analysis_text = "Error: Unexpected Exception during analysis."

    return analysis_text.strip(), inference_time