"""
setup.py — One-click setup for Job AI Agent
Run: python setup.py
"""
import subprocess
import sys
import shutil
from pathlib import Path


def run(cmd, desc):
    print(f"\n>>> {desc}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️  Warning: {result.stderr.strip()[:200]}")
    else:
        print(f"  ✅ Done")
    return result.returncode == 0


def main():
    print("\n" + "=" * 55)
    print("  JOB AI AGENT — SETUP")
    print("=" * 55)

    # 1. Create .env from example
    env_path = Path(".env")
    if not env_path.exists():
        shutil.copy(".env.example", ".env")
        print("\n✅ Created .env file")
        print("   ⚠️  IMPORTANT: Open .env and fill in your API keys before running!")
    else:
        print("\n✅ .env already exists")

    # 2. Create folders
    for folder in ["assets", "logs"]:
        Path(folder).mkdir(exist_ok=True)
    print("✅ Folders created")

    # 3. Install Python packages
    run(f"{sys.executable} -m pip install -r requirements.txt", "Installing Python packages")

    # 4. Install Playwright browsers
    run(f"{sys.executable} -m playwright install chromium", "Installing Playwright browser")

    # 5. Create package inits
    for folder in ["agents", "db", "api"]:
        init = Path(folder) / "__init__.py"
        if not init.exists():
            init.touch()
    print("✅ Package structure ready")

    print("\n" + "=" * 55)
    print("  SETUP COMPLETE!")
    print("=" * 55)
    print("""
NEXT STEPS:
  1. Open .env and fill in:
       ANTHROPIC_API_KEY = (get from console.anthropic.com)
       GMAIL_ADDRESS     = your Gmail address
       GMAIL_APP_PASSWORD= your Gmail App Password
       CV_PATH           = path to your CV PDF

  2. Put your CV PDF in the assets/ folder

  3. Edit config.py if you want to change your profile

  4. Run the bot:
       python main.py run         — Full automated cycle
       python main.py server      — Launch web dashboard
       python main.py scrape      — Just find jobs
       python main.py apply       — Just send applications
       python main.py inbox       — Just check email responses
""")


if __name__ == "__main__":
    main()
