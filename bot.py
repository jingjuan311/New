import time
import random
import os
import asyncio
from telegram import Bot
from playwright.sync_api import sync_playwright

# ============ CONFIG ============
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

COOLDOWN = 30
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
def check_page(page, date_display, date_fill, from_station, to_station, condition):
    try:
        page.goto("https://shuttleonline.ktmb.com.my/Home/Shuttle")
        page.wait_for_load_state("networkidle")

        # 🔽 Fill date (IMPORTANT FORMAT)
        date_input = page.locator("input[placeholder='Depart']")
        date_input.click()
        date_input.fill(date_fill)

        # 🔽 Click SEARCH
        page.locator("button:has-text('SEARCH')").click()

        # wait for results
        page.wait_for_selector("table tbody tr", timeout=10000)

    except Exception as e:
        print("❌ UI selection failed:", e)
        return

    rows = page.locator("table tbody tr")

    for i in range(rows.count()):
        row = rows.nth(i)

        try:
            cells = row.locator("td")

            values = []
            for j in range(cells.count()):
                text = cells.nth(j).inner_text().strip()
                values.append(text)

            # 🔍 DEBUG (IMPORTANT)
            print("ROW:", values)

            # departure time
            dep_time = values[1]

            if not condition(dep_time):
                continue

            # 🔥 FIND SEATS DYNAMICALLY
            seats = 0
            for v in values:
                if v.isdigit():
                    seats = int(v)

            if seats > 0:
                key = f"{date_display}_{from_station}_{dep_time}"
                now = time.time()

                if key not in last_alert_time or now - last_alert_time[key] > COOLDOWN:
                    last_alert_time[key] = now

                    print(f"🎯 FOUND {date_display} {dep_time} seats={seats}")

                    asyncio.run(send_alert(
                        f"🚆 SLOT AVAILABLE!\n"
                        f"📅 {date_display}\n"
                        f"📍 {from_station} → {to_station}\n"
                        f"🕒 {dep_time}\n"
                        f"🎟 Seats: {seats}\n"
                        f"⚡ BOOK NOW!"
                    ))

            else:
                print(f"❌ {dep_time} sold out")

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
            "19 Apr",
            "19 Apr 2026",
            "JB SENTRAL",
            "WOODLANDS CIQ",
            is_after_1230
        )

        # ✅ 1 May Woodlands → JB (before 19:00)
        check_page(
            page,
            "1 May",
            "01 May 2026",
            "WOODLANDS CIQ",
            "JB SENTRAL",
            is_before_1900
        )

        sleep_time = random.uniform(2, 4)
        print(f"⏳ Sleeping {sleep_time:.2f}s\n")
        time.sleep(sleep_time)