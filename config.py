import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_data.db")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
POST_HOURS = [6, 8, 10, 12, 14, 16, 18]
PORT = int(os.getenv("PORT", "8000"))

USER_AGENT = (
    "Mozilla/5.0 (compatible; TelegramBot/3DPrint; +https://t.me/your_bot)"
)

HF_API_KEY = os.getenv("HF_API_KEY", "")
USE_AI_DESCRIPTION = os.getenv("USE_AI_DESCRIPTION", "true").lower() == "true"
