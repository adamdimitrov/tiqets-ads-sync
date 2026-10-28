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
print(f"Deploying FR & ES Ad Groups to Campaign {campaign_id} (validateOnly = {validate_only})...")

mutate_operations = []

# 1. Add Campaign Language Criteria: French (1002) and Spanish (1003)
mutate_operations.append({
    "campaignCriterionOperation": {
        "create": {
            "campaign": f"customers/{customer_id}/campaigns/{campaign_id}",
            "language": {
                "languageConstant": "languageConstants/1002"  # French
            }
        }
    }
})
mutate_operations.append({
    "campaignCriterionOperation": {
        "create": {
            "campaign": f"customers/{customer_id}/campaigns/{campaign_id}",
            "language": {
                "languageConstant": "languageConstants/1003"  # Spanish
            }
        }
    }
})

# 2. Ad Groups
AG_FR_TEMP = f"customers/{customer_id}/adGroups/-10"
AG_ES_TEMP = f"customers/{customer_id}/adGroups/-20"

mutate_operations.append({
    "adGroupOperation": {
        "create": {
            "resourceName": AG_FR_TEMP,
            "name": "Bateaux Parisiens BOF - FR",
            "campaign": f"customers/{customer_id}/campaigns/{campaign_id}",
            "status": "ENABLED",
            "type": "SEARCH_STANDARD",
            "cpcBidMicros": 450000
        }
    }
})

mutate_operations.append({
    "adGroupOperation": {
        "create": {
            "resourceName": AG_ES_TEMP,
            "name": "Bateaux Parisiens BOF - ES",
            "campaign": f"customers/{customer_id}/campaigns/{campaign_id}",
            "status": "ENABLED",
            "type": "SEARCH_STANDARD",
            "cpcBidMicros": 450000
        }
    }
})

# 3. Keywords (Exact Match only)
fr_keywords = [
    "billets bateaux parisiens",
    "billet bateaux parisiens",
    "acheter billets bateaux parisiens",
    "reservation bateaux parisiens",
    "prix bateaux parisiens",
    "tarif bateaux parisiens",
    "tarifs bateaux parisiens"
]
for kw in fr_keywords:
    mutate_operations.append({
        "adGroupCriterionOperation": {
            "create": {
                "adGroup": AG_FR_TEMP,
                "status": "ENABLED",
                "keyword": {
                    "text": kw,
                    "matchType": "EXACT"
                }
            }
        }
    })

es_keywords = [
    "entradas bateaux parisiens",
    "entrada bateaux parisiens",
    "comprar entradas bateaux parisiens",
    "reserva bateaux parisiens",
    "precio bateaux parisiens",
    "precios bateaux parisiens",
    "tarifas bateaux parisiens"
]
for kw in es_keywords:
    mutate_operations.append({
        "adGroupCriterionOperation": {
            "create": {
                "adGroup": AG_ES_TEMP,
                "status": "ENABLED",
                "keyword": {
                    "text": kw,
                    "matchType": "EXACT"
                }
            }
        }
    })

# 4. French RSAs (Ad 1: Ticket-1, Ad 2: Ticket-2)
fr_headlines = [
    {"text": "Billets Bateaux Parisiens"},      # 25
    {"text": "Croisière Promenade Seine"},      # 26
    {"text": "Évitez la File au Quai 3"},       # 24
    {"text": "Pass Mobile Instantané"},         # 23
    {"text": "Départ Pied Tour Eiffel"},        # 23
    {"text": "Boucle de 60 Minutes"},           # 20
    {"text": "Adulte 18€ et Enfant 9€"},        # 24
    {"text": "Annulation 24h Gratuite"},        # 23
    {"text": "Pont Supérieur Ouvert 360°"},     # 27
    {"text": "Billet Journée Flexible"},        # 24
    {"text": "Partenaire Certifié Tiqets"},     # 27
    {"text": "Accès Direct Tourniquets"},       # 24
    {"text": "Vue Panoramique Notre-Dame"},     # 27
    {"text": "Moins de 4 Ans Gratuit"},         # 23
    {"text": "Scannez Votre Smartphone"}        # 24
]
fr_descriptions = [
    {"text": "Réservez vos billets pour Bateaux Parisiens. Évitez la file d'attente au Quai 3."}, # 81
    {"text": "Embarquement direct au pied de la Tour Eiffel. Boucle complète de 60 minutes sur la Seine."}, # 90
    {"text": "Pass journée flexible : partez à votre heure. Adulte 18 €, -50% pour les enfants."}, # 81
    {"text": "Annulation gratuite 24h avant départ. QR code immédiat à scanner directement sur le quai."} # 89
]

for h in fr_headlines:
    assert len(h["text"]) <= 30, f"Headline too long: {h['text']} ({len(h['text'])})"
for d in fr_descriptions:
    assert len(d["text"]) <= 90, f"Description too long: {d['text']} ({len(d['text'])})"

mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_FR_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": ["https://deals.thecruisedetective.com/fr/bateaux-parisiens-billets-croisiere-seine-1"],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Billets",
                    "headlines": fr_headlines,
                    "descriptions": fr_descriptions
                }
            }
        }
    }
})

mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_FR_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": ["https://deals.thecruisedetective.com/fr/bateaux-parisiens-billets-croisiere-seine-2"],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Pass",
                    "headlines": fr_headlines,
                    "descriptions": fr_descriptions
                }
            }
        }
    }
})

# 5. Spanish RSAs (Ad 1: Ticket-1, Ad 2: Ticket-2)
es_headlines = [
    {"text": "Entradas Bateaux Parisiens"},      # 26
    {"text": "Crucero Sena Torre Eiffel"},      # 26
    {"text": "Evita la Cola en Muelle 3"},      # 25
    {"text": "Pase Móvil Instantáneo"},         # 22
    {"text": "Salidas Cada 30 Minutos"},        # 23
    {"text": "Recorrido de 60 Minutos"},        # 23
    {"text": "Adulto 18€ y Niño 9€"},           # 20
    {"text": "Cancelación Gratis 24h"},         # 22
    {"text": "Cubierta Abierta 360°"},          # 22
    {"text": "Pase Flexible Todo el Día"},      # 26
    {"text": "Socio Autorizado Tiqets"},        # 24
    {"text": "Acceso Directo a Tornos"},        # 24
    {"text": "Vistas a Notre-Dame"},            # 20
    {"text": "Menores de 4 Años Gratis"},       # 25
    {"text": "Escanea en tu Móvil"}             # 20
]
es_descriptions = [
    {"text": "Reserva tus entradas para Bateaux Parisiens. Evita la cola en el Muelle 3."}, # 75
    {"text": "Embarque directo al pie de la Torre Eiffel. Recorrido panorámico de 60 min por el Sena."}, # 88
    {"text": "Pase flexible todo el día: sube a la hora que quieras. Adultos 18 €, niños 9 € (-50%)."}, # 86
    {"text": "Cancelación gratuita hasta 24h antes. Código QR instantáneo en tu móvil para embarcar."} # 87
]

for h in es_headlines:
    assert len(h["text"]) <= 30, f"Headline too long: {h['text']} ({len(h['text'])})"
for d in es_descriptions:
    assert len(d["text"]) <= 90, f"Description too long: {d['text']} ({len(d['text'])})"

mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_ES_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": ["https://deals.thecruisedetective.com/es/bateaux-parisiens-entradas-crucero-sena-1"],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Entradas",
                    "headlines": es_headlines,
                    "descriptions": es_descriptions
                }
            }
        }
    }
})

mutate_operations.append({
    "adGroupAdOperation": {
        "create": {
            "adGroup": AG_ES_TEMP,
            "status": "ENABLED",
            "ad": {
                "finalUrls": ["https://deals.thecruisedetective.com/es/bateaux-parisiens-entradas-crucero-sena-2"],
                "responsiveSearchAd": {
                    "path1": "Paris",
                    "path2": "Pase",
                    "headlines": es_headlines,
                    "descriptions": es_descriptions
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
        print("Validation successful! 0 errors detected across Language Targeting, Ad Groups, Keywords, and French/Spanish RSAs.")
    else:
        print("French and Spanish Ad Groups and Ads successfully created in Google Ads!")
        import json
        print(json.dumps(data, indent=2))
else:
    print("ERROR RESPONSE:")
    print(res.text)
