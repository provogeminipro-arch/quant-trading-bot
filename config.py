import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local testing)
load_dotenv()

# Telegram Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Advanced API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
FMP_API_KEY = os.getenv("FMP_API_KEY")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

# Strategy Parameters
MIN_WIN_RATE = 65.0  # Percentage
YEARS_HISTORY = 10
RSI_PERIOD = 14
RSI_OVERSOLD = 30
ATR_PERIOD = 14
ATR_MULTIPLIER = 1.5
HOLDING_PERIOD_DAYS = 5

# System Parameters
PAUSE_BETWEEN_STOCKS = 0.5  # Seconds to pause between Yahoo Finance calls
TOP_STOCKS_COUNT = 100  # Number of top stocks to fetch by volume
