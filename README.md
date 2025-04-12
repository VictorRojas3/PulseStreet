# ⚡ PulseStreet: Your AI Crypto Market Co-Pilot ⚡

**FlashBot delivers real-time, LLaMA-powered insights to navigate volatile crypto markets.**

## Overview

In today's fast-paced financial markets, especially crypto, information is fragmented, and speed is everything. Traditional terminals are expensive, and manually tracking news, social media sentiment, and on-chain data is overwhelming.

**PulseStreet** is an accessible, real-time financial alert platform that acts like your personal AI analyst. It continuously monitors critical market signals:

*   🐋 **Whale Transactions:** Large crypto movements via Whale Alert.
*   🐦 **Social Sentiment:** Real-time trends and discussions via Twitter API.
*   📰 **Financial News:** Breaking headlines (Planned integration).
*   📈 **Macroeconomic Events:** Fed announcements, etc. (Planned integration).

These diverse inputs are synthesized by a powerful Large Language Model (**`llama3.1-8b` via the Cerebras Cloud SDK**) to provide concise, actionable insights delivered instantly via **FlashBot** on Telegram.

## Why PulseStreet?

*   **AI-Driven Synthesis:** Moves beyond simple keyword alerts. LLaMA interprets the *combined meaning* of disparate events (e.g., whale movement + Twitter hype).
*   **Real-Time Edge:** Monitors WebSocket streams and APIs constantly, processing information as it happens.
*   **Actionable Insights via FlashBot:** Doesn't just report data; suggests potential market impact and sentiment, helping you make faster decisions.
*   **Accessibility:** Aims to provide sophisticated analysis capabilities without the hefty price tag of institutional terminals.
*   **The Cerebras Advantage: Time is Money:**
    *   In volatile markets, speed is paramount. Just like on Wall Street, **time is money.**
    *   PulseStreet leverages the **Cerebras Cloud SDK for potentially ultra-fast LLaMA inference.** This minimizes the delay between market event detection and receiving an actionable insight via FlashBot.
    *   Faster analysis means faster alerts, giving you a crucial time advantage to potentially **save time and gain money.**

## Key Features

*   **Real-time Monitoring:** Listens to Whale Alert WebSocket stream.
*   **Multi-Symbol Tracking:** Currently configured for BTC & ETH alerts.
*   **Twitter Context:** Fetches recent relevant tweets (subject to API limits).
*   **LLaMA Analysis:** Uses `llama3.1-8b` (or configured model) via Cerebras Cloud SDK for summarization and sentiment analysis.
*   **Instant FlashBot Alerts:** Formatted alerts pushed directly to your configured Telegram chat, group, or channel.
*   **Configurable:** Set API keys, whale alert thresholds, target chat ID via `.env` file.
*   **Modular Codebase:** Organized into reusable Python modules.
*   **Asynchronous:** Built with `asyncio`, `websockets`, and `httpx` for efficient I/O handling, using `asyncio.to_thread` for the synchronous Cerebras SDK calls.

## How It Works (Simplified Flow)

1.  **Listen:** `alerts.py` connects to Whale Alert WebSocket, filters for configured symbols (BTC/ETH) and value threshold.
2.  **Trigger:** When a relevant alert is received, `main.py` initiates processing.
3.  **Context (Optional):** `twitter.py` fetches recent tweets related to the alert's symbol (if configured).
4.  **Analyze:** `llama.py` formats a prompt with whale data and tweets, then calls the **Cerebras Cloud SDK** to get the analysis.
5.  **Format:** `main.py` combines the whale info, Twitter context, and LLaMA analysis into a user-friendly message.
6.  **Notify:** `telegram_bot.py` sends the formatted alert via **FlashBot** to the configured Telegram chat ID.

## Technology Stack

*   **Language:** Python 3.10+
*   **Core Libraries:**
    *   `asyncio`: For asynchronous operations.
    *   `websockets`: For Whale Alert real-time connection.
    *   `httpx`: For asynchronous HTTP requests (Twitter, Telegram).
    *   `python-dotenv`: For managing environment variables.
    *   `cerebras-cloud-sdk`: For interacting with the Cerebras AI model.
*   **LLM:** `llama3.1-8b` (or configured model) via Cerebras Cloud SDK.
*   **Data Sources:**
    *   Whale Alert API (WebSocket)
    *   Twitter API v2 (Recent Search - Free tier has limitations)
*   **Notifications:** Telegram Bot API (**FlashBot**)
*   **Testing:** `pytest`

## Setup & Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/VictorRojas3/PulseStreet.git 
    cd PulseStreet
    ```

2.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate    # On Windows
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    *   Create a `.env` file in the project root.
    *   Edit the `.env` file and add your API keys and configuration:
        ```dotenv
        # .env file REQUIRED Variables
        WHALE_ALERT_API_KEY=your_whale_alert_api_key_here
        CEREBRAS_API_KEY=PASTE_YOUR_CEREBRAS_API_KEY_HERE # For Cerebras SDK
        TELEGRAM_BOT_TOKEN=your_flashbot_telegram_bot_token_here # FlashBot's Token
        TELEGRAM_CHAT_ID=your_target_telegram_chat_id_here # (User ID, Group ID starting with -, or @channel_name)

        # .env file OPTIONAL Variables (Defaults are in config.py)
        # TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here # Enable Twitter context
        CEREBRAS_MODEL_ID=llama3.1-8b # Optional: Override default model
        WHALE_MIN_USD=10000 # Minimum transaction value in USD to trigger alert
        TWITTER_MAX_RESULTS=10 # Must be >= 10
        LLAMA_MAX_TOKENS=60 # Max new tokens for LLaMA to generate
        # LLAMA_TIMEOUT_SECONDS=60 # Timeout mainly for httpx calls now
        TELEGRAM_TIMEOUT_SECONDS=10 # Timeout for Telegram sending
        RECONNECT_DELAY_SECONDS=15 # Delay before WebSocket reconnect attempt
        LOG_LEVEL=INFO # Logging level (DEBUG, INFO, WARNING, ERROR)
        ```
    *   **Important:** The Cerebras SDK reads `CEREBRAS_API_KEY` directly from the environment variables when initializing. Ensure it's set correctly where you run the application.

## Running the Application

Ensure your virtual environment is active and your `.env` file is configured.

```bash
python main.py
```

The application will start, connect to Whale Alert, initialize the Cerebras client, and begin listening for events. Alerts will be sent via **FlashBot** to the configured Telegram chat ID. Press `Ctrl+C` to stop the application gracefully.

## Testing

Unit/Integration tests are located in the `tests/` directory and use `pytest`.

1.  Make sure `pytest` is installed (`pip install pytest`).
2.  Run tests from the project root directory:
    ```bash
    # Run all tests
    pytest

    # Run tests in a specific file
    pytest tests/test_alerts.py

    # Run the Cerebras SDK test
    pytest tests/test_llama_cerebras.py
    ```

## ⚠️ Disclaimer ⚠️

**PulseStreet and FlashBot are for informational and educational purposes only. The alerts generated are based on AI analysis and publicly available data, and DO NOT constitute financial advice.**

*   Cryptocurrency markets are highly volatile and carry significant risk.
*   AI models (including LLaMA) can make mistakes, hallucinate, or misinterpret data.
*   The information provided may be delayed, incomplete, or inaccurate.
*   **Always conduct your own thorough research (DYOR) and consult with a qualified financial advisor before making any investment decisions.**
*   Use this tool entirely at your own risk. The authors assume no liability for any financial losses incurred.

## Future Enhancements (Roadmap)

*   Integrate News APIs (NewsAPI, etc.).
*   Add more data sources (Reddit, Macroeconomic calendars).
*   Implement more sophisticated sentiment analysis pre-LLM.
*   Allow configuration of multiple symbols/alerts via UI or config file.
*   Web interface for configuration and viewing alert history.
*   More robust error handling and monitoring.

## Contributing

<!-- If open source: Add guidelines for contributing -->
Contributions to PulseStreet are welcome! Please read the `CONTRIBUTING.md` file for details (You'll need to create this file).

## Author

*   Victor Rojas