#!/usr/bin/env python3
import sys
import json
import requests
from dotenv import dotenv_values

ENV_PATH = "/Users/adamdimitrov/Development/tiqets-ads-sync/.env"
env = dotenv_values(ENV_PATH)

CUSTOMER_ID = "4899321613"
MANAGER_ID = "7269565229"
DEV_TOKEN = env["GOOGLE_DEV_TOKEN"]
BUDGET_MICROS = 20000000      # $20.00 / day (matches all other [BOF] campaigns)
BID_CEILING_MICROS = 500000   # $0.50 Max CPC ceiling

# 1. Refresh OAuth token
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
headers = {
    "Authorization": f"Bearer {access_token}",
    "developer-token": DEV_TOKEN,
    "login-customer-id": MANAGER_ID,
    "Content-Type": "application/json"
}

validate_only = "--live" not in sys.argv
mode_str = "VALIDATE ONLY (Dry Run)" if validate_only else "LIVE DEPLOYMENT"
print(f"=== {mode_str} ===")

CAMPAIGN_NAME = "[BOF] Paris - Sightseeing Cruise (EN)"
AD_GROUP_NAME = "Paris Sightseeing Cruise BOF - EN"
LANDING_URL = "https://deals.thecruisedetective.com/seine-river-cruises-paris"

budget_temp = f"customers/{CUSTOMER_ID}/campaignBudgets/-701"
campaign_temp = f"customers/{CUSTOMER_ID}/campaigns/-702"
adgroup_temp = f"customers/{CUSTOMER_ID}/adGroups/-703"

ops = []

# 1. Campaign Budget ($20/day)
ops.append({
    "campaignBudgetOperation": {
        "create": {
            "resourceName": budget_temp,
            "name": f"{CAMPAIGN_NAME} Budget $20",
            "amountMicros": BUDGET_MICROS,
            "deliveryMethod": "STANDARD"
        }
    }
})

# 2. Campaign (Search Only, Target Spend w/ $0.50 Max CPC Ceiling)
ops.append({
    "campaignOperation": {
        "create": {
            "resourceName": campaign_temp,
            "name": CAMPAIGN_NAME,
            "status": "ENABLED",
            "advertisingChannelType": "SEARCH",
            "campaignBudget": budget_temp,
            "targetSpend": {
                "cpcBidCeilingMicros": BID_CEILING_MICROS
            },
            "networkSettings": {
                "targetGoogleSearch": True,
                "targetSearchNetwork": False,
                "targetContentNetwork": False,
                "targetPartnerSearchNetwork": False
            },
            "containsEuPoliticalAdvertising": "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING"
        }
    }
})

# 3. Language Targeting: English (languageConstants/1000)
ops.append({
    "campaignCriterionOperation": {
        "create": {
            "campaign": campaign_temp,
            "language": {
                "languageConstant": "languageConstants/1000"
            }
        }
    }
})

# 4. Campaign Negative Keywords (Broad Match) — prevent Dinner Cruise & junk overlap
NEGATIVES = [
    "dinner", "diner", "lunch", "meal", "restaurant",
    "free", "jobs", "career", "history", "route map",
    "phone number", "refund", "cancellation", "login",
    "accidents", "wikipedia"
]
for neg in NEGATIVES:
    ops.append({
        "campaignCriterionOperation": {
            "create": {
                "campaign": campaign_temp,
                "negative": True,
                "keyword": {
                    "text": neg,
                    "matchType": "BROAD"
                }
            }
        }
    })

# 5. Ad Group
ops.append({
    "adGroupOperation": {
        "create": {
            "resourceName": adgroup_temp,
            "name": AD_GROUP_NAME,
            "campaign": campaign_temp,
            "status": "ENABLED",
            "type": "SEARCH_STANDARD",
            "cpcBidMicros": BID_CEILING_MICROS
        }
    }
})

# 6. High-Intent Exact Match Keywords (NO phrase match)
KEYWORDS = [
    "seine river cruise",
    "paris river cruise",
    "seine river cruise paris",
    "best seine river cruise",
    "best seine river cruise paris",
    "best river cruise in paris",
    "paris boat tour",
    "seine boat tour paris",
    "paris sightseeing cruise",
    "seine sightseeing cruise",
    "seine river cruise tickets",
    "paris river cruise tickets",
    "eiffel tower river cruise",
    "seine cruise paris"
]

for kw in KEYWORDS:
    ops.append({
        "adGroupCriterionOperation": {
            "create": {
                "adGroup": adgroup_temp,
                "status": "ENABLED",
                "keyword": {
                    "text": kw,
                    "matchType": "EXACT"
                }
            }
        }
    })

# 7. Single Unpinned Responsive Search Ad (15 headlines w/ high keyword inclusion + 4 descriptions)
HEADLINES = [
    {"text": "Seine River Cruise Paris"},
    {"text": "Best Seine River Cruise 2026"},
    {"text": "Paris River Cruise Tickets"},
    {"text": "Top 5 Paris Boat Tours Ranked"},
    {"text": "Compare 5 Seine Cruises Live"},
    {"text": "Paris Sightseeing Cruise €18"},
    {"text": "Kids 50% Off (€9 Ages 4-11)"},
    {"text": "Board At The Eiffel Tower"},
    {"text": "Bateaux Parisiens & Mouches"},
    {"text": "360° Open-Air Rooftop Decks"},
    {"text": "Instant Mobile QR Tickets"},
    {"text": "Skip The 60-Min Ticket Line"},
    {"text": "1-Hour Guided Seine Boat Tour"},
    {"text": "Audio Guide In 14 Languages"},
    {"text": "Verified 2026 Cruise Rankings"}
]

DESCRIPTIONS = [
    {"text": "We boarded & tested the top 5 Paris Seine sightseeing cruises. Compare prices & views."},
    {"text": "Official mobile QR tickets from €18 Adult & €9 Kids (50% Off). Skip box office queues."},
    {"text": "Compare Bateaux Parisiens, Bateaux-Mouches & Vedettes de Paris side by side before buying."},
    {"text": "Departures every 30 mins right under the Eiffel Tower. 360° open upper decks & audio app."}
]

for h in HEADLINES:
    assert len(h["text"]) <= 30, f"Headline >30 chars: {h['text']} ({len(h['text'])})"
for d in DESCRIPTIONS:
    assert len(d["text"]) <= 90, f"Description >90 chars: {d['text']} ({len(d['text'])})"

ops.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": adgroup_temp,
            "status": "ENABLED",
            "ad": {
                "finalUrls": [LANDING_URL],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Seine-Cruises",
                    "headlines": HEADLINES,
                    "descriptions": DESCRIPTIONS
                }
            }
        }
    }
})

url = f"https://googleads.googleapis.com/v23/customers/{CUSTOMER_ID}/googleAds:mutate"
res = requests.post(url, headers=headers, json={
    "mutateOperations": ops,
    "validateOnly": validate_only
})

print(f"HTTP Status: {res.status_code}")
if res.status_code == 200:
    print(json.dumps(res.json(), indent=2))
else:
    print(res.text)
    sys.exit(1)
