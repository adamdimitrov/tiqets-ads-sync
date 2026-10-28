import os
import sys
import json
import requests
from dotenv import dotenv_values

env = dotenv_values("/Users/adamdimitrov/Development/tiqets-ads-sync/.env")

# 1. Refresh OAuth Token
token_res = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": env["GOOGLE_CLIENT_ID"],
    "client_secret": env["GOOGLE_CLIENT_SECRET"],
    "refresh_token": env["GOOGLE_REFRESH_TOKEN"],
    "grant_type": "refresh_token"
})
if token_res.status_code != 200:
    print("OAuth refresh failed:", token_res.text)
    sys.exit(1)

access_token = token_res.json()["access_token"]
customer_id = "4899321613"
manager_id = "7269565229"
campaign_id = "24384448947"
dev_token = env["GOOGLE_DEV_TOKEN"]

headers = {
    "Authorization": f"Bearer {access_token}",
    "developer-token": dev_token,
    "login-customer-id": manager_id,
    "Content-Type": "application/json"
}

validate_only = "--live" not in sys.argv
mode_str = "VALIDATE ONLY (Dry Run)" if validate_only else "LIVE DEPLOYMENT"
print(f"=== {mode_str} ===")
print(f"Target Campaign: {campaign_id}")
print(f"Target Account: {customer_id} (MCC: {manager_id})\n")

mutate_operations = []

# 2. Ad Group: Paris Dinner Cruise BOF - EN
AG_DINNER_TEMP = f"customers/{customer_id}/adGroups/-60"

mutate_operations.append({
    "adGroupOperation": {
        "create": {
            "resourceName": AG_DINNER_TEMP,
            "name": "Paris Dinner Cruise BOF - EN",
            "campaign": f"customers/{customer_id}/campaigns/{campaign_id}",
            "status": "ENABLED",
            "type": "SEARCH_STANDARD",
            "cpcBidMicros": 550000
        }
    }
})

# 3. Exact Match Keywords
keywords = [
    "paris dinner cruise",
    "dinner cruise paris",
    "seine river dinner cruise",
    "seine dinner cruise",
    "best dinner cruise paris",
    "best dinner cruise in paris",
    "paris seine dinner cruise",
    "romantic dinner cruise paris",
    "dinner cruise on the seine"
]

for kw in keywords:
    mutate_operations.append({
        "adGroupCriterionOperation": {
            "create": {
                "adGroup": AG_DINNER_TEMP,
                "status": "ENABLED",
                "keyword": {
                    "text": kw,
                    "matchType": "EXACT"
                }
            }
        }
    })

# 4. Responsive Search Ads
headlines_ad1 = [
    {"text": "Paris Dinner Cruises 2026"},
    {"text": "Top 5 Seine Dinner Cruises"},
    {"text": "Compare Menus & Prices"},
    {"text": "Best Dinner Cruise in Paris"},
    {"text": "Instant Tickets From €65"},
    {"text": "Save Up To 30% Online"},
    {"text": "Bateaux Mouches & Parisiens"},
    {"text": "Gourmet 3 & 4-Course Dinners"},
    {"text": "Instant Mobile Voucher"},
    {"text": "Eiffel Tower Illuminations"},
    {"text": "Panoramic Glass Ceiling"},
    {"text": "Live Music & Champagne"},
    {"text": "Free 24h Cancellation"},
    {"text": "Skip The Box Office Line"},
    {"text": "Ranked by Verified Guests"}
]

headlines_ad2 = [
    {"text": "Best Dinner Cruise in Paris", "pinnedField": "HEADLINE_1"},
    {"text": "Compare Menus & Prices", "pinnedField": "HEADLINE_2"},
    {"text": "Instant Tickets From €65"},
    {"text": "Paris Dinner Cruises 2026"},
    {"text": "Top 5 Seine Dinner Cruises"},
    {"text": "Save Up To 30% Online"},
    {"text": "Bateaux Mouches & Parisiens"},
    {"text": "Gourmet 3 & 4-Course Dinners"},
    {"text": "Instant Mobile Voucher"},
    {"text": "Eiffel Tower Illuminations"},
    {"text": "Panoramic Glass Ceiling"},
    {"text": "Live Music & Champagne"},
    {"text": "Free 24h Cancellation"},
    {"text": "Skip The Box Office Line"},
    {"text": "Ranked by Verified Guests"}
]

descriptions = [
    {"text": "Compare top 5 Paris dinner cruises side by side. Real menus, photos, and live pricing."},
    {"text": "From budget 65 Euro to luxury 130 Euro boats. Pick the perfect Seine cruise for tonight."},
    {"text": "Avoid tourist traps with tested rankings. Direct Tiqets partner with free cancellation."},
    {"text": "Book online and skip ticket queues. Window seat options, live music, and Eiffel views."}
]

# Validation assertions
for h in headlines_ad1 + headlines_ad2:
    assert len(h["text"]) <= 30, f"Headline >30 chars: {h['text']} ({len(h['text'])})"
for d in descriptions:
    assert len(d["text"]) <= 90, f"Description >90 chars: {d['text']} ({len(d['text'])})"

landing_url = "https://deals.thecruisedetective.com/dinner-cruise-paris"

# Ad 1 (Unpinned - Google ML Optimization)
mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_DINNER_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": [landing_url],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Dinner",
                    "headlines": headlines_ad1,
                    "descriptions": descriptions
                }
            }
        }
    }
})

# Ad 2 (Pinned - Structured Brand & Intent Testing)
mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_DINNER_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": [landing_url],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Dinner-Cruises",
                    "headlines": headlines_ad2,
                    "descriptions": descriptions
                }
            }
        }
    }
})

print(f"Total mutate operations prepared: {len(mutate_operations)}")
print(f" - 1 Ad Group: Paris Dinner Cruise BOF - EN")
print(f" - {len(keywords)} Exact Match Keywords")
print(f" - 2 Responsive Search Ads (1 unpinned ML, 1 pinned)")

# Send API Request
url = f"https://googleads.googleapis.com/v26/customers/{customer_id}/googleAds:mutate"
payload = {
    "mutateOperations": mutate_operations,
    "validateOnly": validate_only
}

res = requests.post(url, headers=headers, json=payload)
print(f"\nAPI Response Code: {res.status_code}")

if res.status_code == 200:
    data = res.json()
    if validate_only:
        print(">> VALIDATION SUCCEEDED! All entities and character limits valid with Google Ads API v26.")
        print("To deploy live, run: python3 add_dinner_en_campaign.py --live")
    else:
        print(">> LIVE MUTATION SUCCESSFUL!")
        print(json.dumps(data, indent=2))
else:
    print("API Error:")
    print(res.text)
    sys.exit(1)
