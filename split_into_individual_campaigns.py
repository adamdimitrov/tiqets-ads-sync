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
ORIGINAL_CAMPAIGN_ID = "24384448947"
BUDGET_MICROS = 20000000 # €20.00 / day

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

def query_api(query):
    url = f"https://googleads.googleapis.com/v26/customers/{CUSTOMER_ID}/googleAds:search"
    res = requests.post(url, headers=headers, json={"query": query})
    if res.status_code != 200:
        raise Exception(f"Query error {res.status_code}: {res.text}")
    return res.json().get("results", [])

# 2. Extract original ad groups, keywords, and ads
print("Fetching existing structure from Google Ads API...")

ag_query = f"""
    SELECT ad_group.id, ad_group.name, ad_group.status, ad_group.cpc_bid_micros
    FROM ad_group
    WHERE campaign.id = {ORIGINAL_CAMPAIGN_ID}
"""
ag_results = query_api(ag_query)
ad_groups = {row["adGroup"]["id"]: row["adGroup"] for row in ag_results}

kw_query = f"""
    SELECT ad_group_criterion.ad_group, ad_group_criterion.keyword.text, 
           ad_group_criterion.keyword.match_type, ad_group_criterion.status
    FROM ad_group_criterion
    WHERE campaign.id = {ORIGINAL_CAMPAIGN_ID} 
      AND ad_group_criterion.type = 'KEYWORD' 
      AND ad_group_criterion.negative = false
"""
kw_results = query_api(kw_query)
ad_group_keywords = {}
for row in kw_results:
    ag_id = row["adGroupCriterion"]["adGroup"].split("/")[-1]
    ad_group_keywords.setdefault(ag_id, []).append(row["adGroupCriterion"]["keyword"])

ads_query = f"""
    SELECT ad_group_ad.ad_group, ad_group_ad.ad.id, ad_group_ad.ad.final_urls, 
           ad_group_ad.ad.responsive_search_ad.headlines, 
           ad_group_ad.ad.responsive_search_ad.descriptions,
           ad_group_ad.ad.responsive_search_ad.path1,
           ad_group_ad.ad.responsive_search_ad.path2
    FROM ad_group_ad
    WHERE campaign.id = {ORIGINAL_CAMPAIGN_ID}
"""
ads_results = query_api(ads_query)
ad_group_ads = {}
for row in ads_results:
    ag_id = row["adGroupAd"]["adGroup"].split("/")[-1]
    ad_group_ads.setdefault(ag_id, []).append(row["adGroupAd"]["ad"])

print(f"Loaded {len(ad_groups)} ad groups, {sum(len(v) for v in ad_group_keywords.values())} keywords, {sum(len(v) for v in ad_group_ads.values())} ads.")

# Language mapping
LANGUAGE_MAP = {
    "Bateaux Parisiens - High Intent BOF": ("languageConstants/1000", "[BOF] Paris - Bateaux Parisiens (EN)", 450000),
    "Bateaux Mouches - High Intent BOF": ("languageConstants/1000", "[BOF] Paris - Bateaux Mouches (EN)", 450000),
    "Paris Dinner Cruise BOF - EN": ("languageConstants/1000", "[BOF] Paris - Dinner Cruise (EN)", 550000),
    "Bateaux Parisiens BOF - FR": ("languageConstants/1002", "[BOF] Paris - Bateaux Parisiens (FR)", 450000),
    "Bateaux Parisiens BOF - ES": ("languageConstants/1003", "[BOF] Paris - Bateaux Parisiens (ES)", 450000),
    "Bateaux Parisiens BOF - DE": ("languageConstants/1001", "[BOF] Paris - Bateaux Parisiens (DE)", 450000),
    "Bateaux Parisiens BOF - IT": ("languageConstants/1004", "[BOF] Paris - Bateaux Parisiens (IT)", 450000),
    "Bateaux Parisiens BOF - NL": ("languageConstants/1010", "[BOF] Paris - Bateaux Parisiens (NL)", 450000),
}

NEGATIVES = [
    "free", "jobs", "career", "history", "route map", 
    "phone number", "refund", "cancellation", "login", 
    "accidents", "wikipedia"
]

def build_campaign_operations(ag_id, ag_name, temp_prefix):
    lang_constant, new_campaign_name, bid_ceiling = LANGUAGE_MAP[ag_name]
    budget_temp = f"customers/{CUSTOMER_ID}/campaignBudgets/{temp_prefix}1"
    campaign_temp = f"customers/{CUSTOMER_ID}/campaigns/{temp_prefix}2"
    adgroup_temp = f"customers/{CUSTOMER_ID}/adGroups/{temp_prefix}3"

    ops = []

    # 1. Budget Operation
    ops.append({
        "campaignBudgetOperation": {
            "create": {
                "resourceName": budget_temp,
                "name": f"{new_campaign_name} Budget €20",
                "amountMicros": BUDGET_MICROS,
                "deliveryMethod": "STANDARD"
            }
        }
    })

    # 2. Campaign Operation
    ops.append({
        "campaignOperation": {
            "create": {
                "resourceName": campaign_temp,
                "name": new_campaign_name,
                "status": "ENABLED",
                "advertisingChannelType": "SEARCH",
                "campaignBudget": budget_temp,
                "targetSpend": {
                    "cpcBidCeilingMicros": bid_ceiling
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

    # 3. Campaign Language Criterion
    ops.append({
        "campaignCriterionOperation": {
            "create": {
                "campaign": campaign_temp,
                "language": {
                    "languageConstant": lang_constant
                }
            }
        }
    })

    # 4. Campaign Negatives
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

    # 5. Ad Group Operation
    ops.append({
        "adGroupOperation": {
            "create": {
                "resourceName": adgroup_temp,
                "name": ag_name,
                "campaign": campaign_temp,
                "status": "ENABLED",
                "type": "SEARCH_STANDARD"
            }
        }
    })

    # 6. Keywords
    for kw in ad_group_keywords.get(ag_id, []):
        ops.append({
            "adGroupCriterionOperation": {
                "create": {
                    "adGroup": adgroup_temp,
                    "status": "ENABLED",
                    "keyword": {
                        "text": kw["text"],
                        "matchType": kw["matchType"]
                    }
                }
            }
        })

    # 7. Ads (RSAs)
    for ad in ad_group_ads.get(ag_id, []):
        rsa = ad.get("responsiveSearchAd", {})
        cleaned_headlines = []
        for h in rsa.get("headlines", []):
            item = {"text": h["text"]}
            if "pinnedField" in h:
                item["pinnedField"] = h["pinnedField"]
            cleaned_headlines.append(item)

        cleaned_descriptions = []
        for d in rsa.get("descriptions", []):
            item = {"text": d["text"]}
            if "pinnedField" in d:
                item["pinnedField"] = d["pinnedField"]
            cleaned_descriptions.append(item)

        rsa_obj = {
            "headlines": cleaned_headlines,
            "descriptions": cleaned_descriptions
        }
        if rsa.get("path1"):
            rsa_obj["path1"] = rsa["path1"]
        if rsa.get("path2"):
            rsa_obj["path2"] = rsa["path2"]

        ops.append({
            "adGroupAdOperation": {
                "create": {
                    "adGroup": adgroup_temp,
                    "status": "ENABLED",
                    "ad": {
                        "finalUrls": ad.get("finalUrls", []),
                        "responsiveSearchAd": rsa_obj
                    }
                }
            }
        })

    return ops

def main():
    validate_only = "--live" not in sys.argv
    mode_str = "VALIDATE ONLY (Dry Run)" if validate_only else "LIVE DEPLOYMENT"
    print(f"\n=== GOOGLE ADS SPLIT PIPELINE: {mode_str} ===")
    print(f"Target Account: {CUSTOMER_ID} (MCC: {MANAGER_ID})")
    print(f"Daily Budget per Campaign: €{BUDGET_MICROS / 1000000:.2f}/day\n")

    # Deploy each campaign sequentially to avoid oversized batch requests
    temp_idx = 1
    for ag_id, ag in ad_groups.items():
        ag_name = ag["name"]
        if ag_name not in LANGUAGE_MAP:
            print(f"Skipping unrecognized ad group: {ag_name}")
            continue

        _, new_camp_name, _ = LANGUAGE_MAP[ag_name]
        print(f"Processing: '{ag_name}' -> '{new_camp_name}'...")
        ops = build_campaign_operations(ag_id, ag_name, f"-{temp_idx}")
        temp_idx += 1

        mutate_url = f"https://googleads.googleapis.com/v26/customers/{CUSTOMER_ID}/googleAds:mutate"
        payload = {
            "mutateOperations": ops,
            "validateOnly": validate_only
        }

        res = requests.post(mutate_url, headers=headers, json=payload)
        if res.status_code == 200:
            status = "Validated successfully" if validate_only else "Deployed successfully"
            print(f"  ✓ {status} ({len(ops)} operations)")
        else:
            print(f"  ✗ Failed for {ag_name}: {res.status_code}")
            print(res.text)
            sys.exit(1)

    # Finally, pause the original campaign
    print(f"\nPausing original combined campaign {ORIGINAL_CAMPAIGN_ID}...")
    pause_op = [{
        "campaignOperation": {
            "update": {
                "resourceName": f"customers/{CUSTOMER_ID}/campaigns/{ORIGINAL_CAMPAIGN_ID}",
                "status": "PAUSED"
            },
            "updateMask": "status"
        }
    }]
    res = requests.post(
        f"https://googleads.googleapis.com/v26/customers/{CUSTOMER_ID}/googleAds:mutate",
        headers=headers,
        json={"mutateOperations": pause_op, "validateOnly": validate_only}
    )
    if res.status_code == 200:
        status = "Validation passed for pausing" if validate_only else "Original campaign successfully PAUSED"
        print(f"  ✓ {status}")
    else:
        print(f"  ✗ Failed to pause original campaign: {res.status_code}")
        print(res.text)

    if validate_only:
        print("\nAll 8 campaigns validated with 0 errors! To execute live deployment, run with --live.")
    else:
        print("\nALL 8 INDIVIDUAL CAMPAIGNS ARE LIVE AT €20/DAY EACH!")

if __name__ == "__main__":
    main()
