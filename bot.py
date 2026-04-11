import time
import random
import os
import asyncio
import re
from telegram import Bot
from playwright.sync_api import sync_playwright

# ============ CONFIG ============
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
COOLDOWN = 20
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

# ---------- POPUP FIX ----------
def close_popup(page):
    try:
        if page.locator("#validationSummaryModal").is_visible():
            page.keyboard.press("Escape")
            time.sleep(0.5)

        page.evaluate("""
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
        """)
    except:
        pass

# ---------- DATE PICKER (FINAL FIX) ----------
def select_date(page, day, month_text):
    date_input = page.locator("input[placeholder='Depart']")

    # try multiple ways to open calendar
    date_input.click()
    time.sleep(0.5)

    if not page.locator(".datepicker-days").is_visible():
        date_input.click(force=True)
        time.sleep(0.5)

    if not page.locator(".datepicker-days").is_visible():
        date_input.press("Enter")
        time.sleep(0.5)

    # wait calendar
    page.wait_for_selector(".datepicker-days", timeout=10000)

    # navigate month
    for _ in range(6):
        header = page.locator(".datepicker-days th.datepicker-switch").inner_text()

        if month_text in header:
            break

        next_btn = page.locator(".datepicker-days th.next")

        if next_btn.count() > 0:
            next_btn.click()
        else:
            page.keyboard.press("ArrowRight")

        time.sleep(0.5)

    # click day
    page.locator(f".datepicker-days td.day >> text='{day}'").first.click()

# ---------- MAIN CHECK ----------
def check_page(page, date_label, day, month_text, from_station, to_station, condition):
    try:
        page.goto("https://shuttleonline.ktmb.com.my/Home/Shuttle")
        time.sleep(1)

        close_popup(page)

        page.wait_for_selector("button:has-text('SEARCH')", timeout=10000)

        # select date
        select_date(page, day, month_text)

        close_popup(page)

        # click search
        page.locator("button:has-text('SEARCH')").click(force=True)

        # wait redirect
        page.wait_for_url("**/ShuttleTrip", timeout=10000)

        # wait results
        page.wait_for_selector("table tbody tr", timeout=15000)

    except Exception as e:
        print("❌ SEARCH FAILED:", e)
        return

    rows = page.locator("table tbody tr")
    print("🔍 Rows:", rows.count())

    for i in range(rows.count()):
        row = rows.nth(i)

        try:
            cells = row.locator("td")

            values = []
            for j in range(cells.count()):
                values.append(cells.nth(j).inner_text().strip())

            print("ROW:", values)

            dep_time = values[1]

            if not condition(dep_time):
                continue

            # ---------- SEAT DETECTION ----------
            seats = 0
            for v in values:
                match = re.search(r"\d+", v)
                if match:
                    seats = int(match.group())

            # ---------- BUTTON DETECTION ----------
            button = row.locator("button")
            btn_text = ""

            if button.count() > 0:
                try:
                    btn_text = button.inner_text().lower()
                except:
                    pass

            # ---------- SNIPER LOGIC ----------
            trigger = False

            if seats > 0:
                trigger = True
            elif "login" in btn_text:
                trigger = True
            elif button.count() > 0:
                try:
                    if button.is_enabled():
                        trigger = True
                except:
                    pass

            # ---------- ALERT ----------
            if trigger:
                key = f"{date_label}_{from_station}_{dep_time}"
                now = time.time()

                if key not in last_alert_time or now - last_alert_time[key] > COOLDOWN:
                    last_alert_time[key] = now

                    print(f"🚨 SNIPER HIT {dep_time} seats={seats}")

                    asyncio.run(send_alert(
                        f"🚨 SNIPER ALERT!\n"
                        f"📅 {date_label}\n"
                        f"📍 {from_station} → {to_station}\n"
                        f"🕒 {dep_time}\n"
                        f"🎟 Seats: {seats}\n"
                        f"⚡ BOOK NOW!"
                    ))

        except Exception as e:
            print("Row error:", e)

# ---------- RUN ----------
print("🚀 SNIPER BOT RUNNING...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    while True:
        # 19 Apr JB → Woodlands
        check_page(
            page,
            "19 Apr",
            19,
            "April",
            "JB SENTRAL",
            "WOODLANDS CIQ",
            is_after_1230
        )

        # 1 May Woodlands → JB
        check_page(
            page,
            "1 May",
            1,
            "May",
            "WOODLANDS CIQ",
            "JB SENTRAL",
            is_before_1900
        )

        sleep_time = random.uniform(0.8, 1.5)
        print(f"⏳ Sleeping {sleep_time:.2f}s\n")
        time.sleep(sleep_time)