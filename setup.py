import subprocess
import sys
import os

def install_packages():
    packages = [
        "python-telegram-bot==20.7",
        "qrcode[pil]==7.4.2", 
        "requests==2.31.0",
        "python-dotenv==1.0.0",
        "Pillow==10.0.1"
    ]
    
    print("🚀 Installing required packages for JomNenh Bot...")
    print("=" * 50)
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed: {package}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install: {package}")
    
    print("\n" + "=" * 50)
    print("📦 Installation complete!")
    print("\n🔧 Next steps:")
    print("1. Update config.py with your bot token")
    print("2. Run: python bot.py")
    print("3. Your bot will be live!")

def create_env_file():
    env_content = """# Bot Configuration
BOT_TOKEN=8531374089:AAH9ES_O_d1PyX-AJ5s3r-Vlb8js1DoxuXg
ADMIN_USERNAME=tephh
ADMIN_PASSWORD=Tep#@54321

# KHQR Configuration (Get these from your bank)
KHQR_MERCHANT_ID=your_merchant_id_here
KHQR_API_KEY=your_khqr_api_key_here
KHQR_BASE_URL=https://api.khqr.bakong.nbc.gov.kh
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file - please update with your credentials")

if __name__ == "__main__":
    install_packages()
    create_env_file()