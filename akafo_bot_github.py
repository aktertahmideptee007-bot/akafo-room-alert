import json
import os
from datetime import datetime

import requests


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "https://akafoe.studylife.org/api/housing/db-apartments"

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

STATE_FILE = "akafo_state.json"


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": False
    }

    response = requests.post(
        url,
        data=data,
        timeout=30
    )

    response.raise_for_status()


# ============================================================
# GET AVAILABLE LISTINGS
# ============================================================

def get_available_listings():

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        API_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    listings = result.get("data", [])

    available = {}

    for listing in listings:

        availability = listing.get("availability", {})

        if availability.get("available") is True:

            listing_id = listing.get("id")

            if listing_id:
                available[listing_id] = listing

    return available


# ============================================================
# STATE
# ============================================================

def load_state():

    if not os.path.exists(STATE_FILE):
        return {}

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# FORMAT TELEGRAM MESSAGE
# ============================================================

def format_listing_message(listing):

    title = listing.get(
        "title",
        "Unknown listing"
    )

    address = listing.get(
        "address",
        {}
    )

    full_address = address.get(
        "full_address",
        "Address not available"
    )

    details = listing.get(
        "details",
        {}
    )

    rent = (
        details.get("rent_total")
        or details.get("rent")
    )

    size = details.get("size")

    rooms = details.get("rooms")

    availability = listing.get(
        "availability",
        {}
    )

    available_from = availability.get(
        "available_from",
        "Not specified"
    )

    message = (
        "🚨 NEW AKAFÖ ROOM AVAILABLE!\n"
        "\n"
        f"🏠 {title}\n"
        f"📍 {full_address}\n"
        f"💶 Rent: €{rent if rent else 'N/A'}\n"
        f"📐 Size: {size if size else 'N/A'} m²\n"
        f"🚪 Rooms: {rooms if rooms else 'N/A'}\n"
        f"📅 Available from: {available_from}\n"
        "\n"
        "🔗 Open AKAFÖ:\n"
        "https://www.akafoe.de/wohnen/wohnanlagen/freie-zimmer"
    )

    return message


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("AKAFÖ ROOM CHECK")
    print("=" * 60)

    print("Checking AKAFÖ...")

    print("Sending Telegram test...")
    

    try:

        current = get_available_listings()

    except Exception as e:

        print("ERROR: Could not access AKAFÖ API.")
        print(e)

        raise

    print(
        f"Currently available listings: {len(current)}"
    )

    previous = load_state()

    # --------------------------------------------------------
    # FIRST RUN
    # --------------------------------------------------------

    if not previous:

        print()
        print("First run detected.")
        print("Saving current listings without sending alerts.")

        save_state(current)

        return

    # --------------------------------------------------------
    # CHECK FOR NEW LISTINGS
    # --------------------------------------------------------

    new_ids = set(current) - set(previous)

    if new_ids:

        print(
            f"🚨 Found {len(new_ids)} new listing(s)!"
        )

        for listing_id in new_ids:

            listing = current[listing_id]

            message = format_listing_message(
                listing
            )

            print(
                "Sending Telegram alert:",
                listing.get("title")
            )

            send_telegram_message(message)

            print("Telegram alert sent successfully.")

    else:

        print(
            f"No new listings. Available: {len(current)}"
        )

    # Save latest state
    save_state(current)

    print()
    print(
        "Check completed:",
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
