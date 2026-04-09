import time
import random
import os
import asyncio
from telegram import Bot
from playwright.sync_api import sync_playwright

# ============ CONFIG ============
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

COOLDOWN = 30  # seconds
# ================================

bot = Bot(token=TOKEN)
last_alert_time = {}

# ---------- TELEGRAM ----------
async def send_alert(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg)

# ---------- TIME FILTERS ----------
def is_after_1230(t):
    return t >= "12:30"

def is_before_1900(t):
    return t < "19:00"

# ---------- MAIN CHECK ----------
def check_page(page, date, from_station, to_station, condition):
    try:
        page.goto("https://shuttleonline.ktmb.com.my/Home/Shuttle")
        page.wait_for_load_state("networkidle")

        # wait for inputs
        page.wait_for_selector("input", timeout=10000)

        inputs = page.query_selector_all("input")

        # 🔽 FROM station
        inputs[0].click()
        page.click(f"text={from_station}")

        # 🔽 TO station
        inputs = page.query_selector_all("input")
        inputs[1].click()
        page.click(f"text={to_station}")

        # 🔽 DATE
        inputs = page.query_selector_all("input")
        inputs[2].fill(date)

        # 🔽 SEARCH
        page.click("button:has-text('Search')")

        # wait for results
        page.wait_for_selector("table tbody tr", timeout=10000)

    except Exception as e:
        print("❌ UI selection failed:", e)
        return

    rows = page.query_selector_all("table tbody tr")

    for row in rows:
        try:
            dep_time = row.query_selector("td:nth-child(1)").inner_text().strip()

            # 🎯 Apply time condition
            if not condition(dep_time):
                continue

            button = row.query_selector("button")
            btn_text = button.inner_text().lower()

            if "sold out" not in btn_text:
                key = f"{date}_{from_station}_{dep_time}"
                now = time.time()

                if key not in last_alert_time or now - last_alert_time[key] > COOLDOWN:
                    last_alert_time[key] = now

                    print(f"🎯 FOUND {date} {dep_time}")

                    asyncio.run(send_alert(
                        f"🚆 SLOT AVAILABLE!\n"
                        f"📅 {date}\n"
                        f"📍 {from_station} → {to_station}\n"
                        f"🕒 {dep_time}\n"
                        f"⚡ BOOK NOW!"
                    ))

            else:
                print(f"❌ {date} {dep_time} sold out")

        except Exception as e:
            print("Row error:", e)


# ---------- RUN ----------
print("🚀 KTMB Bot Running...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    while True:
        # ✅ 19 Apr JB → Woodlands (after 12:30)
        check_page(
            page,
            "2026-04-19",
            "JB SENTRAL",
            "WOODLANDS CIQ",
            is_after_1230
        )

        # ✅ 1 May Woodlands → JB (before 19:00)
        check_page(
            page,
            "2026-05-01",
            "WOODLANDS CIQ",
            "JB SENTRAL",
            is_before_1900
        )

        sleep_time = random.uniform(2, 4)
        print(f"⏳ Sleeping {sleep_time:.2f}s\n")
        time.sleep(sleep_time)