import os
import sys
import requests
from dotenv import dotenv_values

env = dotenv_values("/Users/adamdimitrov/Development/tiqets-ads-sync/.env")

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
print(f"Deploying DE, IT, NL Ad Groups to Campaign {campaign_id} (validateOnly = {validate_only})...")

mutate_operations = []

# 1. Add Campaign Language Criteria: German (1001), Italian (1004), Dutch (1010)
for lang_id in ["1001", "1004", "1010"]:
    mutate_operations.append({
        "campaignCriterionOperation": {
            "create": {
                "campaign": f"customers/{customer_id}/campaigns/{campaign_id}",
                "language": {
                    "languageConstant": f"languageConstants/{lang_id}"
                }
            }
        }
    })

# 2. Ad Groups
AG_DE_TEMP = f"customers/{customer_id}/adGroups/-30"
AG_IT_TEMP = f"customers/{customer_id}/adGroups/-40"
AG_NL_TEMP = f"customers/{customer_id}/adGroups/-50"

ad_group_configs = [
    (AG_DE_TEMP, "Bateaux Parisiens BOF - DE"),
    (AG_IT_TEMP, "Bateaux Parisiens BOF - IT"),
    (AG_NL_TEMP, "Bateaux Parisiens BOF - NL"),
]

for temp_id, name in ad_group_configs:
    mutate_operations.append({
        "adGroupOperation": {
            "create": {
                "resourceName": temp_id,
                "name": name,
                "campaign": f"customers/{customer_id}/campaigns/{campaign_id}",
                "status": "ENABLED",
                "type": "SEARCH_STANDARD",
                "cpcBidMicros": 450000
            }
        }
    })

# 3. Keywords (Exact Match only)
de_keywords = [
    "bateaux parisiens tickets",
    "bateaux parisiens ticket",
    "bateaux parisiens karten",
    "bateaux parisiens buchen",
    "bateaux parisiens preise",
    "bateaux parisiens preis",
    "seine rundfahrt bateaux parisiens tickets"
]
for kw in de_keywords:
    mutate_operations.append({
        "adGroupCriterionOperation": {
            "create": {
                "adGroup": AG_DE_TEMP,
                "status": "ENABLED",
                "keyword": {
                    "text": kw,
                    "matchType": "EXACT"
                }
            }
        }
    })

it_keywords = [
    "biglietti bateaux parisiens",
    "biglietto bateaux parisiens",
    "comprare biglietti bateaux parisiens",
    "prenotazione bateaux parisiens",
    "prezzo bateaux parisiens",
    "prezzi bateaux parisiens",
    "tariffe bateaux parisiens"
]
for kw in it_keywords:
    mutate_operations.append({
        "adGroupCriterionOperation": {
            "create": {
                "adGroup": AG_IT_TEMP,
                "status": "ENABLED",
                "keyword": {
                    "text": kw,
                    "matchType": "EXACT"
                }
            }
        }
    })

nl_keywords = [
    "bateaux parisiens tickets",
    "bateaux parisiens ticket",
    "bateaux parisiens kaartjes",
    "bateaux parisiens boeken",
    "bateaux parisiens reserveren",
    "bateaux parisiens prijzen",
    "bateaux parisiens prijs"
]
for kw in nl_keywords:
    mutate_operations.append({
        "adGroupCriterionOperation": {
            "create": {
                "adGroup": AG_NL_TEMP,
                "status": "ENABLED",
                "keyword": {
                    "text": kw,
                    "matchType": "EXACT"
                }
            }
        }
    })

# 4. German RSAs
de_headlines = [
    {"text": "Bateaux Parisiens Tickets"},
    {"text": "Seine Rundfahrt Eiffelturm"},
    {"text": "Ohne Anstehen an Pier 3"},
    {"text": "Mobiler Pass Sofort"},
    {"text": "Abfahrt alle 30 Minuten"},
    {"text": "60-Minuten Panoramarunde"},
    {"text": "Erw. 18€ und Kinder 9€"},
    {"text": "Kostenlose 24h Storno"},
    {"text": "360 Grad Freideck"},
    {"text": "Flexibler Ganztagespass"},
    {"text": "Offizieller Tiqets Partner"},
    {"text": "Direkt zu den Drehkreuzen"},
    {"text": "Blick auf Notre-Dame"},
    {"text": "Unter 4 Jahren Kostenlos"},
    {"text": "Direkt am Smartphone"}
]
de_descriptions = [
    {"text": "Offizielle Bateaux Parisiens Tickets. Umgehen Sie die 45 Min Warteschlange an Pier 3."},
    {"text": "Direkter Einstieg am Fuß des Eiffelturms. 60-minütige Panoramarunde auf der Seine."},
    {"text": "Flexibler Ganztagespass: Abfahrten alle 30 Min. Erwachsene 18 €, Kinder 9 € (-50%)."},
    {"text": "Kostenlose Stornierung bis 24h vorher. Sofortiger QR-Code für den direkten Einlass."}
]

for h in de_headlines:
    assert len(h["text"]) <= 30, f"DE headline too long: {h['text']} ({len(h['text'])})"
for d in de_descriptions:
    assert len(d["text"]) <= 90, f"DE desc too long: {d['text']} ({len(d['text'])})"

mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_DE_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": ["https://deals.thecruisedetective.com/de/bateaux-parisiens-tickets-seine-rundfahrt-1"],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Tickets",
                    "headlines": de_headlines,
                    "descriptions": de_descriptions
                }
            }
        }
    }
})

mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_DE_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": ["https://deals.thecruisedetective.com/de/bateaux-parisiens-tickets-seine-rundfahrt-2"],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Pass",
                    "headlines": de_headlines,
                    "descriptions": de_descriptions
                }
            }
        }
    }
})

# 5. Italian RSAs
it_headlines = [
    {"text": "Biglietti Bateaux Parisiens"},
    {"text": "Crociera Senna Torre Eiffel"},
    {"text": "Salta la Coda al Molo 3"},
    {"text": "Pass Digitale Immediato"},
    {"text": "Partenze Ogni 30 Minuti"},
    {"text": "Giro Panoramico 60 Minuti"},
    {"text": "Adulti 18€ Bambini 9€"},
    {"text": "Cancellazione Gratis 24h"},
    {"text": "Ponte Scoperto 360 Gradi"},
    {"text": "Pass Flessibile Tutto Giorno"},
    {"text": "Partner Ufficiale Tiqets"},
    {"text": "Accesso Diretto ai Tornelli"},
    {"text": "Vista su Notre-Dame"},
    {"text": "Sotto i 4 Anni Gratis"},
    {"text": "Mostra il Tuo Smartphone"}
]
it_descriptions = [
    {"text": "Prenota i biglietti ufficiali Bateaux Parisiens. Salta la coda alla cassa al Molo 3."},
    {"text": "Imbarco diretto ai piedi della Torre Eiffel. Giro panoramico di 60 minuti sulla Senna."},
    {"text": "Pass flessibile tutto il giorno: sali all'orario che vuoi. Adulti 18 €, bambini 9 €."},
    {"text": "Cancellazione gratuita fino a 24h prima. Codice QR istantaneo sul tuo smartphone."}
]

for h in it_headlines:
    assert len(h["text"]) <= 30, f"IT headline too long: {h['text']} ({len(h['text'])})"
for d in it_descriptions:
    assert len(d["text"]) <= 90, f"IT desc too long: {d['text']} ({len(d['text'])})"

mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_IT_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": ["https://deals.thecruisedetective.com/it/bateaux-parisiens-biglietti-crociera-senna-1"],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Biglietti",
                    "headlines": it_headlines,
                    "descriptions": it_descriptions
                }
            }
        }
    }
})

mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_IT_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": ["https://deals.thecruisedetective.com/it/bateaux-parisiens-biglietti-crociera-senna-2"],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Pass",
                    "headlines": it_headlines,
                    "descriptions": it_descriptions
                }
            }
        }
    }
})

# 6. Dutch RSAs
nl_headlines = [
    {"text": "Bateaux Parisiens Tickets"},
    {"text": "Seine Rondvaart Eiffeltoren"},
    {"text": "Vermijd de Rij bij Pier 3"},
    {"text": "Mobiele Pas Direct"},
    {"text": "Vertrek Elke 30 Minuten"},
    {"text": "60-Minuten Rondvaart"},
    {"text": "Volw. 18€ en Kind 9€"},
    {"text": "Gratis Annuleren 24u"},
    {"text": "360 Graden Open Zonnedek"},
    {"text": "Flexibele Dagpas Parijs"},
    {"text": "Officiële Tiqets Partner"},
    {"text": "Directe Toegang Poortjes"},
    {"text": "Uitzicht op Notre-Dame"},
    {"text": "Onder 4 Jaar Gratis"},
    {"text": "Scan op uw Smartphone"}
]
nl_descriptions = [
    {"text": "Officiële Bateaux Parisiens tickets. Vermijd de 45 minuten kassa-wachtrij bij Pier 3."},
    {"text": "Direct instappen aan de voet van de Eiffeltoren. Panoramische tocht van 60 min over Seine."},
    {"text": "Flexibele dagpas: vertrek elke 30 minuten. Volwassene 18 €, kinderen 9 € (-50%)."},
    {"text": "Gratis annuleren tot 24u voor vertrek. Directe mobiele QR-code voor snelle toegang."}
]

for h in nl_headlines:
    assert len(h["text"]) <= 30, f"NL headline too long: {h['text']} ({len(h['text'])})"
for d in nl_descriptions:
    assert len(d["text"]) <= 90, f"NL desc too long: {d['text']} ({len(d['text'])})"

mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_NL_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": ["https://deals.thecruisedetective.com/nl/bateaux-parisiens-tickets-rondvaart-seine-1"],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Tickets",
                    "headlines": nl_headlines,
                    "descriptions": nl_descriptions
                }
            }
        }
    }
})

mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_NL_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": ["https://deals.thecruisedetective.com/nl/bateaux-parisiens-tickets-rondvaart-seine-2"],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Pass",
                    "headlines": nl_headlines,
                    "descriptions": nl_descriptions
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
        print("Validation successful! 0 errors detected across DE, IT, NL Targeting, Ad Groups, Keywords, and RSAs.")
    else:
        print("DE, IT, NL Ad Groups and Ads successfully created in Google Ads!")
        import json
        print(json.dumps(data, indent=2))
else:
    print("ERROR RESPONSE:")
    print(res.text)
