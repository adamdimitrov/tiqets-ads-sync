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
BID_CEILING_MICROS = 300000     # €0.30 Max CPC bid ceiling (matches live EN Dinner Cruise campaign)
ADGROUP_BID_MICROS = 10000      # €0.01 default ad group bid (Target Spend controls actual CPC)

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

CAMPAIGN_NAME = "[BOF] Paris - Dinner Cruise (FR)"
AD_GROUP_NAME = "Paris Dinner Cruise BOF - FR"
LANDING_URL = "https://deals.thecruisedetective.com/fr/croisiere-diner-paris"

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

# 2. Campaign ([BOF] Paris - Dinner Cruise (FR))
ops.append({
    "campaignOperation": {
        "create": {
            "resourceName": campaign_temp,
            "name": CAMPAIGN_NAME,
            "status": "PAUSED",
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
            "geoTargetTypeSetting": {
                "positiveGeoTargetType": "PRESENCE_OR_INTEREST",
                "negativeGeoTargetType": "PRESENCE"
            },
            "containsEuPoliticalAdvertising": "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING"
        }
    }
})

# 3. Language Criterion: French (1002)
ops.append({
    "campaignCriterionOperation": {
        "create": {
            "campaign": campaign_temp,
            "language": {
                "languageConstant": "languageConstants/1002"
            }
        }
    }
})

# 4. Campaign Negative Keywords (EN + FR negatives)
NEGATIVES = [
    "free", "jobs", "career", "history", "route map",
    "phone number", "refund", "cancellation", "login",
    "accidents", "wikipedia",
    "gratuit", "emploi", "recrutement", "stage", "remboursement",
    "annulation", "téléphone", "horaires", "plan"
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

# 6. Ad Group: Paris Dinner Cruise BOF - FR
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

# 7. Exact Match French Keywords (BOF High-Intent)
keywords = [
    "diner croisiere paris",
    "croisiere diner paris",
    "diner croisiere sur la seine",
    "diner croisiere seine",
    "meilleur diner croisiere paris",
    "meilleur diner croisiere sur la seine",
    "paris diner croisiere",
    "diner croisiere romantique paris",
    "croisiere diner sur la seine",
    "comparatif diner croisiere paris",
    "diner bateau mouche paris",
    "diner bateaux parisiens"
]

for kw in keywords:
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

# 8. Responsive Search Ads (FR)
headlines_ad1 = [
    {"text": "Dîner-Croisière Paris 2026"},       # 26
    {"text": "Top 5 Dîners-Croisières Seine"},    # 29
    {"text": "Comparez Menus et Tarifs"},         # 24
    {"text": "Meilleur Dîner-Croisière Paris"},   # 30
    {"text": "Billets Officiels dès 65 €"},       # 26
    {"text": "Économisez Jusqu'à 30%"},           # 22
    {"text": "Bateaux-Mouches et Parisiens"},     # 28
    {"text": "Menus Gastronomiques 3-4 Plats"},   # 30
    {"text": "Billet Mobile Instantané"},         # 24
    {"text": "Tour Eiffel Scintillante"},         # 24
    {"text": "Verrière et Toit Panoramique"},     # 28
    {"text": "Musique Live et Champagne"},        # 25
    {"text": "Annulation Gratuite à 24h"},        # 25
    {"text": "Accès Coupe-File Embarquement"},    # 29
    {"text": "5 Compagnies Testées sur Place"}    # 30
]

descriptions = [
    {"text": "Comparez les 5 meilleurs dîners-croisières à Paris : vrais menus, photos et prix 2026."},     # 86
    {"text": "Du bistrot à 65 € aux bateaux de luxe à 130 €. Choisissez votre croisière sur la Seine."},    # 87
    {"text": "Évitez les attrape-touristes grâce à nos tests. Billets Tiqets et annulation gratuite."},     # 86
    {"text": "Réservez en ligne sans file d'attente. Baie vitrée, musique live et vue Tour Eiffel."}        # 84
]

for h in headlines_ad1:
    assert len(h["text"]) <= 30, f"Headline >30 chars: {h['text']} ({len(h['text'])})"
for d in descriptions:
    assert len(d["text"]) <= 90, f"Description >90 chars: {d['text']} ({len(d['text'])})"

# Ad 1 (Unpinned - Google ML Optimization)
ops.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": adgroup_temp,
            "status": "ENABLED",
            "ad": {
                "finalUrls": [LANDING_URL],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Diner",
                    "headlines": headlines_ad1,
                    "descriptions": descriptions
                }
            }
        }
    }
})

print(f"Total mutate operations prepared: {len(ops)}")
print(f" - 1 Campaign Budget: €20.00/day")
print(f" - 1 Campaign: {CAMPAIGN_NAME} (PAUSED, Target Spend Max CPC €0.30, French 1002)")
print(f" - {len(NEGATIVES)} Negative Keywords")
print(f" - 1 Official Business Logo Asset ({LOGO_ASSET_ID})")
print(f" - 1 Ad Group: {AD_GROUP_NAME}")
print(f" - {len(keywords)} Exact Match French Keywords")
print(f" - 1 Responsive Search Ad -> {LANDING_URL}")

url = f"https://googleads.googleapis.com/v26/customers/{CUSTOMER_ID}/googleAds:mutate"
payload = {
    "mutateOperations": ops,
    "validateOnly": validate_only
}

res = requests.post(url, headers=headers, json=payload)
print(f"\nAPI Response Code: {res.status_code}")

if res.status_code == 200:
    data = res.json()
    if validate_only:
        print(">> VALIDATION SUCCEEDED! All entities and character limits valid with Google Ads API v26.")
        print("To deploy live, run: python3 add_dinner_fr_campaign.py --live")
    else:
        print(">> LIVE MUTATION SUCCESSFUL!")
        print(json.dumps(data, indent=2))
else:
    print("API Error:")
    print(res.text)
    sys.exit(1)
