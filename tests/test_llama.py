import asyncio
import logging
import time
import os

try:
    from config import ( CEREBRAS_API_KEY, CEREBRAS_MODEL_ID, logger, LOG_LEVEL, IS_CONFIG_VALID, LLAMA_MAX_TOKENS )
except ImportError as e:
    logging.basicConfig(level=logging.INFO); logger = logging.getLogger()
    logger.error(f"Failed config import: {e}"); exit(1)
except Exception as e:
    logging.basicConfig(level=logging.INFO); logger = logging.getLogger()
    logger.error(f"Unexpected config import error: {e}"); exit(1)
try:
    from llama import analyze_with_llama
    from llama import cerebras_client 
except ImportError as e:
     logger.error(f"Failed llama.py import: {e}"); exit(1)
except Exception as e:
     logger.error(f"Unexpected llama.py import error: {e}"); exit(1)


async def run_cerebras_llama_test():
    """Tests Cerebras SDK completions via the llama.py module."""
    logger.info("--- Starting Cerebras LLaMA SDK Test (completions via llama.py) ---")
    if not CEREBRAS_API_KEY or not CEREBRAS_MODEL_ID:
        logger.error("TEST FAILED: CEREBRAS_API_KEY or CEREBRAS_MODEL_ID missing."); return
    if cerebras_client is None:
         logger.error("TEST FAILED: Cerebras SDK client failed to initialize."); return
    logger.info(f"Using Cerebras Model ID: {CEREBRAS_MODEL_ID}")
    test_whale_summary = "Test: 5 BTC ($100k USD) transferred."
    test_tweets = ["#bitcoin looking strong"]
    test_symbol = "TEST_COMPLETION"
    logger.info(f"Submitting test analysis request for symbol: {test_symbol}")
    generated_text = "Error: Analysis failed."
    inference_time = 0.0
    success = False
    try:
        start_time = time.monotonic()
        generated_text, inference_time = await analyze_with_llama(
            whale_summary=test_whale_summary,
            tweet_snippets=test_tweets,
            symbol=test_symbol
        )
        success = not generated_text.startswith("Error:")
    except Exception as e:
        logger.error(f"Unexpected error calling analyze_with_llama: {e}", exc_info=True)
        generated_text = "Error: Unexpected Exception during test run"
        inference_time = time.monotonic() - (start_time if 'start_time' in locals() else time.monotonic())
    logger.info(f"Inference Time reported: {inference_time:.2f} seconds")
    logger.info(f"Generated Text Result: >>> {generated_text} <<<")
    if success:
         logger.info("✅ TEST SUCCEEDED: Successfully received response via Cerebras SDK completions wrapper.")
         print("\n>>> Test successful! <<<")
    else:
         logger.error("❌ TEST FAILED: Could not get valid response via Cerebras SDK completions wrapper.")
         logger.error("Check logs for errors (API, parsing, etc.). Verify parsing in _sync_cerebras_call.")


if __name__ == "__main__":
    logger.info("Running Cerebras LLaMA SDK completions test...")
    if not os.environ.get("CEREBRAS_API_KEY") and CEREBRAS_API_KEY:
         os.environ["CEREBRAS_API_KEY"] = CEREBRAS_API_KEY
    if not os.environ.get("CEREBRAS_API_KEY"):
         logger.critical("Cannot proceed without CEREBRAS_API_KEY set.")
         exit(1)
    try:
        asyncio.run(run_cerebras_llama_test())
    except KeyboardInterrupt: logger.info("Test interrupted.")
    finally: logger.info("--- Test Finished ---")