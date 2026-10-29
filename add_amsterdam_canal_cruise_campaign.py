#!/usr/bin/env python3
import os
import sys
import json
import requests
from dotenv import dotenv_values

ENV_PATH = "/Users/adamdimitrov/Development/tiqets-ads-sync/.env"
env = dotenv_values(ENV_PATH)

CUSTOMER_ID = "4899321613"
MANAGER_ID = "7269565229"
DEV_TOKEN = env["GOOGLE_DEV_TOKEN"]
LOGO_ASSET_ID = "432769086002"

BUDGET_MICROS = 20000000        # €20.00 / day
BID_CEILING_MICROS = 500000     # €0.50 Max CPC bid ceiling (matches BOF sightseeing standard)
ADGROUP_BID_MICROS = 500000      # €0.50 default ad group bid

# 1. Fetch OAuth token
token_res = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": env["GOOGLE_CLIENT_ID"],
    "client_secret": env["GOOGLE_CLIENT_SECRET"],
    "refresh_token": env["GOOGLE_REFRESH_TOKEN"],
    "grant_type": "refresh_token"
})
if token_res.status_code != 200:
    print("OAuth token refresh failed:", token_res.text)
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
print(f"Target Account: {CUSTOMER_ID} (MCC: {MANAGER_ID})\n")

CAMPAIGN_NAME = "[BOF] Amsterdam - Canal Cruise (EN)"
AD_GROUP_NAME = "Amsterdam Canal Cruise BOF - EN"
LANDING_URL = "https://deals.thecruisedetective.com/amsterdam-canal-cruises"

budget_temp = f"customers/{CUSTOMER_ID}/campaignBudgets/-701"
campaign_temp = f"customers/{CUSTOMER_ID}/campaigns/-702"
adgroup_temp = f"customers/{CUSTOMER_ID}/adGroups/-703"

ops = []

# 1. Campaign Budget (€20/day)
ops.append({
    "campaignBudgetOperation": {
        "create": {
            "resourceName": budget_temp,
            "name": f"{CAMPAIGN_NAME} Budget €20",
            "amountMicros": BUDGET_MICROS,
            "deliveryMethod": "STANDARD",
            "explicitlyShared": False
        }
    }
})

# 2. Campaign ([BOF] Amsterdam - Canal Cruise (EN))
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

# 4. Campaign Negative Keywords (Broad Match)
NEGATIVES = [
    "dinner", "diner", "lunch", "meal", "restaurant",
    "free", "jobs", "career", "history", "route map",
    "phone number", "refund", "cancellation", "login",
    "accidents", "wikipedia", "paris", "seine", "budapest", "danube"
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

# 5. Official Business Logo Asset Attachment
ops.append({
    "campaignAssetOperation": {
        "create": {
            "campaign": campaign_temp,
            "asset": f"customers/{CUSTOMER_ID}/assets/{LOGO_ASSET_ID}",
            "fieldType": "BUSINESS_LOGO"
        }
    }
})

# 6. Ad Group
ops.append({
    "adGroupOperation": {
        "create": {
            "resourceName": adgroup_temp,
            "name": AD_GROUP_NAME,
            "campaign": campaign_temp,
            "status": "ENABLED",
            "type": "SEARCH_STANDARD",
            "cpcBidMicros": ADGROUP_BID_MICROS
        }
    }
})

# 7. Exact Match Keywords
KEYWORDS = [
    "amsterdam canal cruise",
    "amsterdam canal cruises",
    "canal cruise amsterdam",
    "canal cruises amsterdam",
    "amsterdam canal cruise tickets",
    "canal cruise amsterdam tickets",
    "best amsterdam canal cruise",
    "best canal cruise amsterdam",
    "best canal cruise in amsterdam",
    "amsterdam boat tour",
    "amsterdam boat tours",
    "amsterdam boat tour tickets",
    "amsterdam canal tour",
    "amsterdam canal tours",
    "amsterdam sightseeing cruise",
    "lovers canal cruise amsterdam",
    "lovers canal cruise",
    "amsterdam lovers canal cruise",
    "flagship amsterdam cruise",
    "blue boat amsterdam"
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

# 8. Responsive Search Ad (RSA)
HEADLINES = [
    {"text": "Amsterdam Canal Cruise"},
    {"text": "Best Amsterdam Canal Cruise"},
    {"text": "Canal Cruise Amsterdam 2026"},
    {"text": "Compare 5 Canal Cruises Live"},
    {"text": "Amsterdam Canal Tour €16"},
    {"text": "Top 5 Amsterdam Boat Tours"},
    {"text": "Instant Mobile QR Tickets"},
    {"text": "Central Station Boarding"},
    {"text": "Lovers, Flagship & Blue Boat"},
    {"text": "Skip The Box Office Line"},
    {"text": "Audio Guide In 19 Languages"},
    {"text": "Heated Boats & Open Sloops"},
    {"text": "Daily Departures Every 15m"},
    {"text": "100% Flexible Cancellation"},
    {"text": "Verified 2026 Cruise Rankings"}
]

DESCRIPTIONS = [
    {"text": "We tested & ranked the top 5 Amsterdam canal cruises. Compare prices, piers & boat types."},
    {"text": "Official mobile QR tickets from €16. Skip the long box office queues at Central Station."},
    {"text": "Compare Lovers, Flagship, Blue Boat & Captain Jack side by side before booking online."},
    {"text": "Frequent departures outside Central Station. Heated panoramic boats & GPS audio guides."}
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
                    "path1": "Amsterdam",
                    "path2": "Canal-Cruises",
                    "headlines": HEADLINES,
                    "descriptions": DESCRIPTIONS
                }
            }
        }
    }
})

print(f"Total mutate operations prepared: {len(ops)}")
print(f" - 1 Campaign Budget: €20.00/day")
print(f" - 1 Campaign: {CAMPAIGN_NAME} (ENABLED, Target Spend Max CPC €0.50, English)")
print(f" - {len(NEGATIVES)} Negative Keywords")
print(f" - 1 Official Business Logo Asset ({LOGO_ASSET_ID})")
print(f" - 1 Ad Group: {AD_GROUP_NAME}")
print(f" - {len(KEYWORDS)} Exact Match Keywords")
print(f" - 1 Responsive Search Ad -> {LANDING_URL}")

url = f"https://googleads.googleapis.com/v23/customers/{CUSTOMER_ID}/googleAds:mutate"
res = requests.post(url, headers=headers, json={
    "mutateOperations": ops,
    "validateOnly": validate_only
})

print(f"\nHTTP Status: {res.status_code}")
if res.status_code == 200:
    print("SUCCESS!")
    print(json.dumps(res.json(), indent=2))
else:
    print("ERROR:")
    print(res.text)
    sys.exit(1)
