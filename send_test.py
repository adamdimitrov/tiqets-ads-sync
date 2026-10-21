import os
import time
import requests
import json

TIQETS_API_KEY = "tqat-riUgqzjZAhtdw09J2G8rOUgTvNBKBGQC"
META_ACCESS_TOKEN = "dummy"
META_PIXEL_ID = "dummy"

from dotenv import load_dotenv
load_dotenv(dotenv_path="/Users/adamdimitrov/Development/tiqets-ads-sync/.env")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
META_PIXEL_ID = os.environ.get("META_PIXEL_ID")

test_code = "TEST64747"
order_id = "1015543946"
fbclid = "AdamRealPurchaseTest"

timestamp = int(time.time())
fbc = f"fb.1.{timestamp}.{fbclid}"

payload = {
    "data": [
        {
            "event_name": "Purchase",
            "event_time": timestamp,
            "action_source": "website",
            "user_data": {
                "fbc": fbc
            },
            "custom_data": {
                "value": 7.46,
                "currency": "EUR"
            },
            "event_id": f"{order_id}_TEST"
        }
    ],
    "test_event_code": test_code
}

url = f"https://graph.facebook.com/v20.0/{META_PIXEL_ID}/events?access_token={META_ACCESS_TOKEN}"
try:
    res = requests.post(url, json=payload)
    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)
except Exception as e:
    print("ERROR:", e)
