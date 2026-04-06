import requests
import time
import random
import os
from telegram import Bot

# ============ CONFIG ============
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CHECK_INTERVAL_MIN = 1
CHECK_INTERVAL_MAX = 2

COOLDOWN = 20  # seconds
# ================================

bot = Bot(token=TOKEN)

# track last alert time per train
last_alert_time = {}

# create session (important for KTMB)
session = requests.Session()


def send_alert(msg):
    bot.send_message(chat_id=CHAT_ID, text=msg)


def check_route(date, from_station, to_station, condition):
    url = "https://shuttleonline.ktmb.com.my/api/shuttle/search"

    payload = {
        "from": from_station,
        "to": to_station,
        "date": date
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://shuttleonline.ktmb.com.my",
        "Referer": "https://shuttleonline.ktmb.com.my/"
    }

    try:
        # 👇 get session cookies first (VERY IMPORTANT)
        session.get("https://shuttleonline.ktmb.com.my/")

        response = session.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            print(f"❌ API error {date}: {response.status_code}")
            return

        data = response.json()

        for train in data.get("data", []):
            dep = train.get("departure_time", "")[:5]  # HH:MM
            seats = train.get("available_seats", 0)

            if not dep:
                continue

            if condition(dep):
                print(f"🕒 {date} {dep} | Seats: {seats}")

                if seats > 0:
                    key = f"{date}_{from_station}_{dep}"
                    current_time = time.time()

                    # 🔁 cooldown alert system
                    if key not in last_alert_time or current_time - last_alert_time[key] > COOLDOWN:
                        last_alert_time[key] = current_time

                        print(f"🎯 ALERT: {key}")

                        send_alert(
                            f"🚆 KTMB SLOT FOUND!\n"
                            f"📅 {date}\n"
                            f"📍 {from_station} → {to_station}\n"
                            f"🕒 {dep}\n"
                            f"⚡ BOOK NOW!"
                        )

    except Exception as e:
        print("❌ Error:", e)


# ================= CONDITIONS =================

def before_2pm(time_str):
    return time_str < "14:00"


def after_1230pm(time_str):
    return time_str >= "12:30"


# =============================================


print("🚀 KTMB Multi-Route Bot Running...")


while True:
    # ✅ 1 May: Woodlands → JB (before 2pm)
    check_route(
        "2026-05-01",
        "WOODLANDS CIQ",
        "JB SENTRAL",
        before_2pm
    )

    # ✅ 19 Apr: JB → Woodlands (after 12:30pm)
    check_route(
        "2026-04-19",
        "JB SENTRAL",
        "WOODLANDS CIQ",
        after_1230pm
    )

    sleep_time = random.uniform(CHECK_INTERVAL_MIN, CHECK_INTERVAL_MAX)
    print(f"⏳ Sleeping {sleep_time:.2f}s...\n")

    time.sleep(sleep_time)