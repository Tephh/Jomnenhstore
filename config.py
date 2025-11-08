import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8531374089:AAExQ3nQQZbf5AQ0LCtCuX8Pby3l6fhhyGM')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'tephh')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Tep#@54321')

# KHQR Configuration (You'll need to get these from your bank)
KHQR_MERCHANT_ID = os.getenv('KHQR_MERCHANT_ID', 'your_merchant_id_here')
KHQR_API_KEY = os.getenv('KHQR_API_KEY', 'your_khqr_api_key_here')
KHQR_BASE_URL = os.getenv('KHQR_BASE_URL', 'https://api.khqr.bakong.nbc.gov.kh')

# Database
DATABASE_NAME = "business_bot.db"

# Logging
LOG_LEVEL = "INFO"

print("✅ Config loaded successfully!")
print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
print(f"👤 Admin: {ADMIN_USERNAME}")
