import os
import requests
import json

# Manually parse .env to avoid needing the dotenv package
env_vars = {}
try:
    with open("/Users/adamdimitrov/Development/tiqets-ads-sync/.env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()
except Exception:
    pass


def test_webhook():
    print("Testing the Google Ads & Meta Webhook Payload...\n")
    
    # We use a fake GCLID
    fake_gclid = "Cj0KCQjw_5unBhCMARIsACZhz1_fake_gclid_12345"
    fake_fbclid = "IwAR2_fake_fbclid_67890"
    
    # This is exactly how the webflow-sync.js formats it now!
    subid_string = f"fbclid:{fake_fbclid}|gclid:{fake_gclid}"
    
    payload = {
        "order_id": "TEST-12345",
        "subid": subid_string,
        "commission": 12.50,
        "currency": "EUR",
        "test_event_code": "TEST12345"
    }
    
    import sys
    sys.path.append("/Users/adamdimitrov/Development/tiqets-ads-sync/api")
    
    # We must delete the dummy meta credentials from the environment BEFORE importing the app
    # so the app loads them as None and safely skips the Meta block without crashing!
    os.environ.pop("META_ACCESS_TOKEN", None)
    os.environ.pop("META_PIXEL_ID", None)
    
    try:
        from index import app
        import index
        
        # Override environment variables manually
        index.GOOGLE_DEV_TOKEN = os.environ.get("GOOGLE_DEV_TOKEN")
        index.GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
        index.GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
        index.GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN")
        index.GOOGLE_CUSTOMER_ID = os.environ.get("GOOGLE_CUSTOMER_ID")
        index.GOOGLE_CONVERSION_ACTION_ID = os.environ.get("GOOGLE_CONVERSION_ACTION_ID")
        
        app.testing = True
        client = app.test_client()
        
        print(f"Sending payload: {json.dumps(payload, indent=2)}\n")
        
        response = client.post('/', json=payload)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Data: {response.data.decode('utf-8')}")
        
        print("\nNOTE FOR GOOGLE ADS:")
        print("Because we used a fake GCLID, Google Ads will reject it. If you see an error in the logs above mentioning 'ClickNotFound' or 'UNPARSEABLE_GCLID' from Google, THAT IS A HUGE SUCCESS! It means the API is fully connected and successfully talking to Google, it just correctly rejected our fake click.")
        
    except Exception as e:
        print(f"Error running test: {e}")

if __name__ == "__main__":
    test_webhook()
