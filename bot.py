import time
import random
import os
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# ============ CONFIG ============
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

COOLDOWN = 20
CHECK_INTERVAL = 2
# ================================

bot = Bot(token=TOKEN)
last_alert_time = {}

def send_alert(msg):
    bot.send_message(chat_id=CHAT_ID, text=msg)

# setup headless chrome
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)

URL = "https://shuttleonline.ktmb.com.my/Home/Shuttle"

def check_page(date, from_station, to_station, condition):
    try:
        driver.get(URL)
        time.sleep(3)

        page = driver.page_source.lower()

        # simple detection
        if "sold out" not in page:
            key = f"{date}_{from_station}"
            current_time = time.time()

            if key not in last_alert_time or current_time - last_alert_time[key] > COOLDOWN:
                last_alert_time[key] = current_time

                send_alert(
                    f"🚆 POSSIBLE TICKET AVAILABLE!\n"
                    f"📅 {date}\n"
                    f"📍 {from_station} → {to_station}\n"
                    f"⚡ CHECK NOW!"
                )

    except Exception as e:
        print("Error:", e)


print("🚀 Selenium bot running...")

while True:
    # 1 May: Woodlands → JB (before 2pm)
    check_page(
        "2026-05-01",
        "WOODLANDS CIQ",
        "JB SENTRAL",
        lambda x: x < "14:00"
    )

    # 19 Apr: JB → Woodlands (after 12:30pm)
    check_page(
        "2026-04-19",
        "JB SENTRAL",
        "WOODLANDS CIQ",
        lambda x: x >= "12:30"
    )

    sleep_time = random.uniform(2, 4)
    print(f"Sleeping {sleep_time:.2f}s")
    time.sleep(sleep_time)