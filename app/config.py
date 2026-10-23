"""Application configuration and constants."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_FILENAME = "ai_bi_assistant_sales_data_-_GET.csv"
DATA_CSV_PATH = DATA_DIR / CSV_FILENAME
DB_PATH = DATA_DIR / "sales.db"

# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.8-flash").strip()

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Currency & Formatting
CURRENCY_SYMBOL = "₹"
DATE_FORMAT_INPUT = "%d-%m-%Y"
DATE_FORMAT_ISO = "%Y-%m-%d"
