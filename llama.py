import httpx
import time
import logging
import json
from config import (
    HF_API_TOKEN,
    HF_SERVERLESS_API_URL,
    LLAMA_MAX_TOKENS,
    LLAMA_TIMEOUT_SECONDS
)

logger = logging.getLogger(__name__)

def format_llama_prompt(whale_summary: str, tweet_snippets: list, symbol: str) -> str:
    """Formats the prompt for the LLaMA API. (Same as previous main.py)"""
    prompt = f"""
    Analyze potential {symbol} market impact based ONLY on this fresh data:

    Whale Transactions:
    {whale_summary if whale_summary else 'None reported now.'}

    Recent Twitter Mentions ({symbol}):
    {' '.join([f'- "{t}"' for t in tweet_snippets]) if tweet_snippets else 'None relevant found.'}

    Task: Briefly summarize potential short-term (1-4h) impact/sentiment for {symbol} in under 50 words. Focus: concise market sentiment (e.g., Bullish pressure, Bearish risk, Mixed).
    """
    return prompt

async def analyze_with_llama(client: httpx.AsyncClient, whale_summary: str, tweet_snippets: list, symbol: str):
    """
    Sends data to the Hugging Face Serverless LLaMA API and parses the response.
    Based on test_llama_hf.py logic.
    """
    target_url = HF_SERVERLESS_API_URL
    api_token = HF_API_TOKEN

    if not target_url or not api_token:
         logger.error("Hugging Face Serverless API URL or Token not configured in llama.py.")
         return "Error: LLaMA URL/token not configured.", 0.0

    prompt = format_llama_prompt(whale_summary, tweet_snippets, symbol)
    headers = { "Authorization": f"Bearer {api_token}", "Content-Type": "application/json" }
    params = { "max_new_tokens": LLAMA_MAX_TOKENS, "temperature": 0.7, "do_sample": True, "return_full_text": False }
    payload = { "inputs": prompt, "parameters": params, "options": {"wait_for_model": True} }

    logger.info(f"Sending prompt for {symbol} analysis to HF Serverless API...")
    start_time = time.monotonic()
    analysis_text = "Error: Analysis failed."
    inference_time = 0.0

    try:
        response = await client.post(target_url, json=payload, headers=headers, timeout=LLAMA_TIMEOUT_SECONDS)
        inference_time = time.monotonic() - start_time 
        logger.debug(f"HF API Response Status: {response.status_code}, Time: {inference_time:.2f}s")

        if response.status_code == 503:
            logger.warning(f"LLaMA Serverless API returned 503 (Model Loading/Cold Start?) after {inference_time:.2f}s.")
            analysis_text = "Error: Model loading (503)"
        elif response.status_code >= 400:
             try:
                  error_detail = response.json() 
             except json.JSONDecodeError:
                  error_detail = response.text 
             logger.error(f"LLaMA Serverless API Error {response.status_code}: {error_detail}")
             analysis_text = f"Error: LLaMA API Error ({response.status_code})"
        else: 
            try:
                response_data = response.json()
                if isinstance(response_data, list) and len(response_data) > 0:
                    analysis_text = response_data[0].get('generated_text', 'Error: "generated_text" key not found in list')
                elif isinstance(response_data, dict) and 'error' in response_data:
                     logger.error(f"API Success Status but returned error field: {response_data['error']}")
                     analysis_text = f"Error: API Error ({response_data.get('error', 'Unknown')})"
                else:
                    logger.warning(f"Unexpected successful response format from HF API: {response_data}")
                    analysis_text = f"Error: Unexpected response format ({type(response_data)})"
                if analysis_text.startswith("Error:"):
                     logger.error(f"Failed to extract 'generated_text' from successful response.")
                else:
                    logger.info(f"LLaMA Inference for {symbol} successful in {inference_time:.2f} seconds.")

            except json.JSONDecodeError as json_err:
                 logger.error(f"Failed to decode successful JSON response from HF API: {json_err}. Response text: {response.text}")
                 analysis_text = "Error: Invalid JSON response"

    except httpx.TimeoutException:
        inference_time = time.monotonic() - start_time 
        logger.error(f"LLaMA API request timed out after {LLAMA_TIMEOUT_SECONDS} seconds.")
        analysis_text = "Error: LLaMA analysis timed out."
    except httpx.RequestError as e:
        inference_time = time.monotonic() - start_time
        logger.error(f"LLaMA API connection error: {e}")
        analysis_text = "Error: Could not connect to LLaMA API."
    except Exception as e:
        inference_time = time.monotonic() - start_time
        logger.error(f"Unexpected error during LLaMA analysis: {e}", exc_info=True)
        analysis_text = "Error: Unexpected Exception during analysis"
    return analysis_text.strip(), inference_time