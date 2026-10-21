import time
import urllib.request
import json

env_vars = {}
with open("/Users/adamdimitrov/Development/tiqets-ads-sync/.env", "r") as f:
    for line in f:
        line = line.strip()
        if line and "=" in line:
            key, val = line.split("=", 1)
            env_vars[key] = val

token = env_vars.get("META_ACCESS_TOKEN")
pixel = env_vars.get("META_PIXEL_ID")

test_code = "TEST25452"
fbclid = "AdamLegendaTestDirect"

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
                "value": 15.50,
                "currency": "EUR"
            }
        }
    ],
    "test_event_code": test_code
}

url = f"https://graph.facebook.com/v20.0/{pixel}/events?access_token={token}"
req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    res = urllib.request.urlopen(req)
    print("STATUS:", res.getcode())
    print("RESPONSE:", res.read().decode('utf-8'))
except Exception as e:
    print("ERROR:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
