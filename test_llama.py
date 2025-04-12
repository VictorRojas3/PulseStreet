# test_llama_hf.py
import asyncio
import httpx
import logging
import time
import os

try:
    # Import the relevant config vars for Serverless API
    from config import (
        HF_API_TOKEN,
        HF_MODEL_ID,
        HF_SERVERLESS_API_URL, # Use this constructed URL
        logger,
        LOG_LEVEL,
        IS_CONFIG_VALID,
        LLAMA_TIMEOUT_SECONDS # Use the (longer) timeout from config
    )
except ImportError as e:
    logging.basicConfig(level=logging.INFO)
    logging.error(f"Failed to import config. Ensure config.py exists and loads .env. Error: {e}")
    exit(1)
except Exception as e:
    logging.basicConfig(level=logging.INFO)
    logging.error(f"An unexpected error occurred during config import: {e}")
    exit(1)

async def run_hf_llama_test():
    """Tests connection and inference with the Hugging Face Serverless LLaMA API."""
    logger.info("--- Starting Hugging Face LLaMA Serverless API Test ---")

    if not HF_API_TOKEN or not HF_MODEL_ID:
        logger.error("TEST FAILED: HF_API_TOKEN or HF_MODEL_ID is missing.")
        return
    if not HF_SERVERLESS_API_URL:
        logger.error("TEST FAILED: HF_SERVERLESS_API_URL could not be constructed.")
        return

    target_url = HF_SERVERLESS_API_URL
    logger.info(f"Using Serverless Inference API URL: {target_url}")

    test_prompt = "Explain the concept of blockchain in one sentence."
    params = { "max_new_tokens": 50, "temperature": 0.7, "do_sample": True, "return_full_text": False }
    payload = { "inputs": test_prompt, "parameters": params, "options": {"wait_for_model": True} } # Add wait_for_model
    headers = { "Authorization": f"Bearer {HF_API_TOKEN}", "Content-Type": "application/json" }

    logger.info(f"Sending test prompt to Serverless API: {target_url}")
    logger.debug(f"Payload: {payload}")

    generated_text = "Error: Inference failed."
    inference_time = 0.0
    success = False

    try:
        # Use the potentially long timeout from config
        async with httpx.AsyncClient(timeout=LLAMA_TIMEOUT_SECONDS) as client:
            start_time = time.monotonic()
            response = await client.post(target_url, headers=headers, json=payload)
            inference_time = time.monotonic() - start_time

            logger.info(f"Received response status code: {response.status_code}")

            # Handle potential 503 during model loading
            if response.status_code == 503:
                logger.warning(f"Received HTTP 503 after {inference_time:.2f}s: Model might be loading (cold start).")
                # Estimate remaining time based on 'estimated_time' if present
                try:
                    error_data = response.json()
                    est_time = error_data.get("estimated_time")
                    if est_time:
                        logger.warning(f"  Estimated loading time remaining: {est_time:.1f} seconds. Re-running the test might work.")
                except Exception:
                    pass # Ignore errors parsing the error response
                generated_text = "Error: HTTP 503 (Model Loading)"
            # Handle other errors (like 429 Too Many Requests)
            elif response.status_code >= 400:
                 logger.error(f"HTTP Error {response.status_code}: {response.text}")
                 generated_text = f"Error: HTTP {response.status_code}"
                 response.raise_for_status() # Let httpx handle standard error raising for logging below
            # Handle success
            else:
                response_data = response.json()
                if isinstance(response_data, list) and len(response_data) > 0:
                    generated_text = response_data[0].get('generated_text', 'Error: "generated_text" key not found')
                elif isinstance(response_data, dict) and 'error' in response_data:
                     logger.error(f"API returned error field: {response_data['error']}")
                     generated_text = f"Error: API Error ({response_data.get('error', 'Unknown')})"
                else:
                     generated_text = f"Error: Unexpected success response format: {response_data}"

                success = not generated_text.startswith("Error:")

    except httpx.HTTPStatusError as e:
         # This catches the raise_for_status() for non-503 errors >= 400
         logger.error(f"Request failed: {e.response.status_code} - Check logs above.", exc_info=False)
         # generated_text is already set to error string in the block above
    except httpx.TimeoutException:
        logger.error(f"Request timed out after {LLAMA_TIMEOUT_SECONDS} seconds (Severe cold start or network issue).")
        generated_text = "Error: Timeout"
    except httpx.RequestError as e:
        logger.error(f"Request Error: {e}")
        generated_text = "Error: Request Failed"
    except Exception as e:
        logger.error(f"An unexpected error occurred parsing response or during request: {e}", exc_info=True)
        generated_text = "Error: Unexpected Exception during processing"

    logger.info(f"Inference Time: {inference_time:.2f} seconds")
    logger.info(f"Generated Text Result: {generated_text}")

    if success:
         logger.info("✅ TEST SUCCEEDED: Successfully received response from Hugging Face Serverless LLaMA API.")
         print("\n>>> Test successful! Model generated a response. <<<")
    else:
         logger.error("❌ TEST FAILED: Could not get valid response from Hugging Face Serverless LLaMA API.")
         logger.error("Check logs above for specific errors (HTTP status, API errors, timeouts).")

if __name__ == "__main__":
    logger.info("Running Hugging Face LLaMA Serverless API connection test...")
    try:
        asyncio.run(run_hf_llama_test())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user (Ctrl+C).")
    finally:
        logger.info("--- Hugging Face LLaMA Serverless Test Finished ---")