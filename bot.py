import time
import random
import os
from telegram import Bot
from playwright.sync_api import sync_playwright

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

COOLDOWN = 20
CHECK_INTERVAL = 2

bot = Bot(token=TOKEN)
last_alert_time = {}

def send_alert(msg):
    bot.send_message(chat_id=CHAT_ID, text=msg)

def check_page(page, date, from_station, to_station):
    page.goto("https://shuttleonline.ktmb.com.my/Home/Shuttle")
    time.sleep(3)

    content = page.content().lower()

    if "sold out" not in content:
        key = f"{date}_{from_station}"
        now = time.time()

        if key not in last_alert_time or now - last_alert_time[key] > COOLDOWN:
            last_alert_time[key] = now

            send_alert(
                f"🚆 POSSIBLE TICKET!\n"
                f"📅 {date}\n"
                f"📍 {from_station} → {to_station}\n"
                f"⚡ CHECK NOW!"
            )

print("🚀 Playwright bot running...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    while True:
        check_page(page, "2026-05-01", "WOODLANDS CIQ", "JB SENTRAL")
        check_page(page, "2026-04-19", "JB SENTRAL", "WOODLANDS CIQ")

        sleep_time = random.uniform(2, 4)
        print(f"Sleeping {sleep_time:.2f}s")
        time.sleep(sleep_time)