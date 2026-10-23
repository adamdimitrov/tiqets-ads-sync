import os
import sys
import requests
from dotenv import dotenv_values

env = dotenv_values("/Users/adamdimitrov/Development/tiqets-ads-sync/.env")

# 1. Fetch OAuth token
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
dev_token = env["GOOGLE_DEV_TOKEN"]

headers = {
    "Authorization": f"Bearer {access_token}",
    "developer-token": dev_token,
    "login-customer-id": manager_id,
    "Content-Type": "application/json"
}

validate_only = "--live" not in sys.argv
print(f"Running Google Ads Campaign Setup (validateOnly = {validate_only})...")

# Mutate Operations
mutate_operations = []

# Temp IDs
BUDGET_TEMP = f"customers/{customer_id}/campaignBudgets/-1"
CAMPAIGN_TEMP = f"customers/{customer_id}/campaigns/-2"
AG_BP_TEMP = f"customers/{customer_id}/adGroups/-3"
AG_BM_TEMP = f"customers/{customer_id}/adGroups/-4"

# 1. Campaign Budget: €25.00 / day
mutate_operations.append({
    "campaignBudgetOperation": {
        "create": {
            "resourceName": BUDGET_TEMP,
            "name": "Paris Seine Cruises Daily Budget €25",
            "amountMicros": 25000000,
            "deliveryMethod": "STANDARD"
        }
    }
})

# 2. Campaign: Search Network Only, Max Clicks Capped at €0.45, PAUSED
mutate_operations.append({
    "campaignOperation": {
        "create": {
            "resourceName": CAMPAIGN_TEMP,
            "name": "[BOF] Paris Seine Cruises - Bateaux High Intent",
            "status": "PAUSED",
            "advertisingChannelType": "SEARCH",
            "campaignBudget": BUDGET_TEMP,
            "targetSpend": {
                "cpcBidCeilingMicros": 450000
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

# 3. Location Targeting: Paris (City: 1006094, Department: 9040871, Île-de-France: 20340)
for geo_id in ["1006094", "9040871"]:
    mutate_operations.append({
        "campaignCriterionOperation": {
            "create": {
                "campaign": CAMPAIGN_TEMP,
                "location": {
                    "geoTargetConstant": f"geoTargetConstants/{geo_id}"
                }
            }
        }
    })

# 4. Language Targeting: English (1000)
mutate_operations.append({
    "campaignCriterionOperation": {
        "create": {
            "campaign": CAMPAIGN_TEMP,
            "language": {
                "languageConstant": "languageConstants/1000"
            }
        }
    }
})

# 5. Campaign Negative Keywords
negatives = ["free", "jobs", "career", "history", "route map", "phone number", "refund", "cancellation", "login", "accidents", "wikipedia"]
for neg in negatives:
    mutate_operations.append({
        "campaignCriterionOperation": {
            "create": {
                "campaign": CAMPAIGN_TEMP,
                "negative": True,
                "keyword": {
                    "text": neg,
                    "matchType": "BROAD"
                }
            }
        }
    })

# 6. Ad Groups
# Ad Group 1: Bateaux Parisiens BOF
mutate_operations.append({
    "adGroupOperation": {
        "create": {
            "resourceName": AG_BP_TEMP,
            "name": "Bateaux Parisiens - High Intent BOF",
            "campaign": CAMPAIGN_TEMP,
            "status": "ENABLED",
            "type": "SEARCH_STANDARD"
        }
    }
})

# Ad Group 2: Bateaux Mouches BOF
mutate_operations.append({
    "adGroupOperation": {
        "create": {
            "resourceName": AG_BM_TEMP,
            "name": "Bateaux Mouches - High Intent BOF",
            "campaign": CAMPAIGN_TEMP,
            "status": "ENABLED",
            "type": "SEARCH_STANDARD"
        }
    }
})

# 7. Keywords for Bateaux Parisiens
bp_keywords = [
    ("bateaux parisiens tickets", "EXACT"),
    ("bateaux parisiens tickets", "PHRASE"),
    ("bateaux parisiens ticket", "EXACT"),
    ("buy bateaux parisiens tickets", "EXACT"),
    ("bateaux parisiens booking", "EXACT"),
    ("bateaux parisiens price", "PHRASE"),
    ("bateaux parisiens prices", "PHRASE")
]
for text, match in bp_keywords:
    mutate_operations.append({
        "adGroupCriterionOperation": {
            "create": {
                "adGroup": AG_BP_TEMP,
                "status": "ENABLED",
                "keyword": {
                    "text": text,
                    "matchType": match
                }
            }
        }
    })

# 8. Keywords for Bateaux Mouches
bm_keywords = [
    ("bateaux mouches tickets", "EXACT"),
    ("bateaux mouches tickets", "PHRASE"),
    ("bateaux mouches ticket", "EXACT"),
    ("buy bateaux mouches tickets", "EXACT"),
    ("bateaux mouches booking", "EXACT"),
    ("bateaux mouches price", "PHRASE"),
    ("bateaux mouches prices", "PHRASE")
]
for text, match in bm_keywords:
    mutate_operations.append({
        "adGroupCriterionOperation": {
            "create": {
                "adGroup": AG_BM_TEMP,
                "status": "ENABLED",
                "keyword": {
                    "text": text,
                    "matchType": match
                }
            }
        }
    })

# 9. Responsive Search Ad for Bateaux Parisiens
bp_headlines = [
    {"text": "Bateaux Parisiens Tickets", "pinnedField": "HEADLINE_1"},
    {"text": "Official Pier 3 Eiffel Tower", "pinnedField": "HEADLINE_2"},
    {"text": "Instant Mobile QR Ticket"},
    {"text": "Adults €18, Kids €9 (50% Off)"},
    {"text": "Children Under 4 Free"},
    {"text": "Skip The Ticket Line"},
    {"text": "Boats Depart Every 30 Min"},
    {"text": "70-Min Seine River Cruise"},
    {"text": "Direct Eiffel Tower Boarding"},
    {"text": "100% Flexible Instant Tickets"},
    {"text": "Instant Booking Confirmation"},
    {"text": "Audio Guide in 14 Languages"},
    {"text": "Open Upper Deck Panoramic View"},
    {"text": "Valid on Any Departure Today"},
    {"text": "Official Digital River Pass"}
]

bp_descriptions = [
    {"text": "Board at Pier 3 under the Eiffel Tower. Instant mobile QR ticket sent right to your phone."},
    {"text": "Avoid ticket counter lines. Boats depart every 30 minutes from Port de la Bourdonnais."},
    {"text": "Guaranteed boarding with digital barcode tickets. Flexible departures throughout the day."},
    {"text": "Adults €18, Kids 4–11 €9 (50% off), Under 4 Free. Panoramic 70-min Seine river cruise."}
]

mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_BP_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": ["https://deals.thecruisedetective.com/family-pass"],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Tickets",
                    "headlines": bp_headlines,
                    "descriptions": bp_descriptions
                }
            }
        }
    }
})

# 10. Responsive Search Ad for Bateaux Mouches
bm_headlines = [
    {"text": "Bateaux Mouches Tickets", "pinnedField": "HEADLINE_1"},
    {"text": "Pont de l'Alma Boarding", "pinnedField": "HEADLINE_2"},
    {"text": "Instant Smartphone QR Ticket"},
    {"text": "Official 360° Open Deck Cruise"},
    {"text": "Skip The Box Office Queue"},
    {"text": "Departures Every 30-45 Min"},
    {"text": "70-Minute Seine River Cruise"},
    {"text": "Stunning Eiffel Tower Views"},
    {"text": "100% Flexible Departure Time"},
    {"text": "Instant Mobile Confirmation"},
    {"text": "Audio Commentary Included"},
    {"text": "Iconic Paris River Cruise"},
    {"text": "Adults €17, Kids €8"},
    {"text": "Children Under 4 Free"},
    {"text": "Official Seine Digital Ticket"}
]

bm_descriptions = [
    {"text": "Board at Pont de l'Alma. Instant mobile QR ticket delivered directly to your smartphone."},
    {"text": "Avoid box office lines. Panoramic 360° open-air upper deck views of Notre-Dame and Louvre."},
    {"text": "Guaranteed admission with digital barcode tickets. Frequent departures daily until 22:30."},
    {"text": "Experience Paris from the water on the historic Bateaux Mouches. Instant mobile pass."}
]

mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_BM_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": ["https://deals.thecruisedetective.com/couples-pass"],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Cruise",
                    "headlines": bm_headlines,
                    "descriptions": bm_descriptions
                }
            }
        }
    }
})

url = f"https://googleads.googleapis.com/v26/customers/{customer_id}/googleAds:mutate"
payload = {
    "mutateOperations": mutate_operations,
    "validateOnly": validate_only
}

res = requests.post(url, headers=headers, json=payload)
print("STATUS CODE:", res.status_code)
if res.status_code == 200:
    print("SUCCESS!")
    data = res.json()
    if validate_only:
        print("Validation successful! 0 errors detected across Budget, Campaign, Ad Groups, Keywords, and RSA Creatives.")
    else:
        print("Campaign successfully created in your Google Ads account!")
        import json
        print(json.dumps(data, indent=2))
else:
    print("ERROR RESPONSE:")
    print(res.text)
