import os
import logging
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

"""
Main configuration file for the application.
"""

# --- Basic Logging Setup ---
LOG_LEVEL_STR = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) 

# --- API Keys & Tokens ---
WHALE_ALERT_API_KEY = os.getenv('WHALE_ALERT_API_KEY')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN') 
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# --- Whale Alert Config ---
WHALE_SUBSCRIPTION_MSG = {
    "type": "subscribe_alerts",
    "blockchains": ["ethereum", "bitcoin"],
    "symbols": ["eth", "btc"],
    "min_value_usd": 10_000,
}
WHALE_ALERT_WSS_URL = f"wss://leviathan.whale-alert.io/ws?api_key={WHALE_ALERT_API_KEY}" if WHALE_ALERT_API_KEY else None

# --- Twitter Config ---
TWITTER_MAX_RESULTS = int(os.getenv('TWITTER_MAX_RESULTS', '10')) 
if TWITTER_MAX_RESULTS < 10:
    logger.warning(f"TWITTER_MAX_RESULTS ({TWITTER_MAX_RESULTS}) is less than 10. Setting to 10 as required by Twitter API.")
    TWITTER_MAX_RESULTS = 10

# --- Cerebras Config ---
CEREBRAS_MODEL_ID = os.getenv('CEREBRAS_MODEL_ID')
LLAMA_MAX_TOKENS = int(os.getenv('LLAMA_MAX_TOKENS', '60')) 

# --- Telegram Config ---
TELEGRAM_TIMEOUT_SECONDS = int(os.getenv('TELEGRAM_TIMEOUT_SECONDS', '10')) 

# --- General Config ---
RECONNECT_DELAY_SECONDS = int(os.getenv('RECONNECT_DELAY_SECONDS', '300')) 

# --- Validation Function ---
def validate_config():
    """Checks if essential configuration variables are set."""
    essential_vars = {
        "WHALE_ALERT_API_KEY": WHALE_ALERT_API_KEY,
        "CEREBRAS_API_TOKEN": CEREBRAS_API_KEY,
        "CEREBRAS_MODEL_ID": CEREBRAS_MODEL_ID, 
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }
    missing = [k for k, v in essential_vars.items() if not v]
    if missing:
        logger.critical(f"CRITICAL ERROR: Missing essential config variables: {', '.join(missing)}")
        return False
    if not WHALE_ALERT_WSS_URL:
        logger.critical("CRITICAL ERROR: WHALE_ALERT_WSS_URL could not be constructed (WHALE_ALERT_API_KEY missing?).")
        return False
    if not TWITTER_BEARER_TOKEN:
         logger.warning("Optional config 'TWITTER_BEARER_TOKEN' not set. Twitter context will be skipped.")
    return True

IS_CONFIG_VALID = validate_config()

logger.debug(f"Config Loaded: Whale WSS URL set = {bool(WHALE_ALERT_WSS_URL)}, Sub Msg = {WHALE_SUBSCRIPTION_MSG}")
logger.debug(f"Config Loaded: Twitter Token set = {bool(TWITTER_BEARER_TOKEN)}, Max Results = {TWITTER_MAX_RESULTS}")
logger.debug(f"Config Loaded: Cerebras key set = {bool(CEREBRAS_API_KEY)}, Model ID = {CEREBRAS_MODEL_ID}")
logger.debug(f"Config Loaded: Telegram Token set = {bool(TELEGRAM_BOT_TOKEN)}, Chat ID = {TELEGRAM_CHAT_ID}")