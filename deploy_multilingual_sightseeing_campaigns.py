#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.parse
from dotenv import dotenv_values

ENV_PATH = "/Users/adamdimitrov/Development/tiqets-ads-sync/.env"
env = dotenv_values(ENV_PATH)

CUSTOMER_ID = "4899321613"
MANAGER_ID = "7269565229"
DEV_TOKEN = env["GOOGLE_DEV_TOKEN"]
BUDGET_MICROS = 20000000      # €20.00 / day
BID_CEILING_MICROS = 500000   # €0.50 Max CPC ceiling

# 1. Refresh OAuth token
token_data = urllib.parse.urlencode({
    "client_id": env["GOOGLE_CLIENT_ID"],
    "client_secret": env["GOOGLE_CLIENT_SECRET"],
    "refresh_token": env["GOOGLE_REFRESH_TOKEN"],
    "grant_type": "refresh_token"
}).encode("utf-8")

req = urllib.request.Request("https://oauth2.googleapis.com/token", data=token_data, method="POST")
with urllib.request.urlopen(req) as resp:
    token_json = json.loads(resp.read().decode())
    access_token = token_json["access_token"]

headers = {
    "Authorization": f"Bearer {access_token}",
    "developer-token": DEV_TOKEN,
    "login-customer-id": MANAGER_ID,
    "Content-Type": "application/json"
}

validate_only = "--live" not in sys.argv
mode_str = "VALIDATE ONLY (Dry Run)" if validate_only else "LIVE DEPLOYMENT"
print(f"=== {mode_str} ===")

# Language configurations
CONFIGS = [
    {
        "lang": "fr",
        "lang_id": "1002",
        "campaign_name": "[BOF] Paris - Sightseeing Cruise (FR)",
        "ad_group_name": "Paris Sightseeing Cruise BOF - FR",
        "landing_url": "https://deals.thecruisedetective.com/fr/croisiere-seine-paris",
        "path1": "Paris",
        "path2": "Croisiere-Seine",
        "keywords": [
            "croisiere seine",
            "croisiere seine paris",
            "croisiere sur la seine",
            "meilleure croisiere seine",
            "meilleure croisiere seine paris",
            "visite bateau paris",
            "croisiere promenade paris",
            "billet croisiere seine",
            "croisiere tour eiffel",
            "balade bateau seine",
            "bateau mouche seine paris",
            "croisiere paris 1h",
            "promenade en bateau paris",
            "croisiere seine pas cher"
        ],
        "negatives": [
            "diner", "dejeuner", "repas", "restaurant", "gratuit",
            "emploi", "recrutement", "stage", "wikipedia", "remboursement", "annulation"
        ],
        "headlines": [
            "Croisière Seine Paris 2026",
            "Top 5 Bateaux Paris Comparés",
            "Billets Croisière Seine 18€",
            "Meilleure Croisière Seine",
            "Enfants -50% (9€ 4-11 Ans)",
            "Départ Au Pied Tour Eiffel",
            "Bateaux Parisiens & Mouches",
            "Pont Supérieur 360° Ouvert",
            "Billets Mobiles Instantanés",
            "Évitez 60 Min File D'Attente",
            "Visite Guidée 1h Sur Seine",
            "Audioguide En 14 Langues",
            "Avis Testés Sur Place 2026",
            "Embarquement Quai Numéro 3",
            "Vue Panoramique Tour Eiffel"
        ],
        "descriptions": [
            "Nous avons testé les 5 croisières promenade à Paris. Comparez prix, terrasses et avis.",
            "Billets officiels dès 18€ Adulte & 9€ Enfant (-50%). Évitez les files en billetterie.",
            "Bateaux Parisiens, Bateaux-Mouches et Vedettes de Paris comparés avant de réserver.",
            "Départs toutes les 30 min au pied de la Tour Eiffel. Terrasses 360° et audioguide mobile."
        ]
    },
    {
        "lang": "es",
        "lang_id": "1003",
        "campaign_name": "[BOF] Paris - Sightseeing Cruise (ES)",
        "ad_group_name": "Paris Sightseeing Cruise BOF - ES",
        "landing_url": "https://deals.thecruisedetective.com/es/crucero-sena-paris",
        "path1": "Paris",
        "path2": "Crucero-Sena",
        "keywords": [
            "crucero sena",
            "crucero sena paris",
            "crucero por el sena",
            "mejor crucero sena",
            "mejor crucero sena paris",
            "paseo en barco sena",
            "paseo en barco sena paris",
            "entradas crucero sena",
            "crucero torre eiffel",
            "barco turistico paris",
            "paseo en barco por paris",
            "billetes crucero sena",
            "barco paseo sena",
            "crucero sena 1 hora"
        ],
        "negatives": [
            "cena", "almuerzo", "comida", "restaurante", "gratis",
            "empleo", "trabajo", "wikipedia", "cancelar", "reembolso"
        ],
        "headlines": [
            "Crucero Por El Sena París",
            "Mejor Crucero Sena 2026",
            "Entradas Crucero Sena 18€",
            "Top 5 Barcos Sena Comparados",
            "Niños 50% Dto (9€ 4-11 Años)",
            "Embarque Bajo Torre Eiffel",
            "Bateaux Parisiens y Mouches",
            "Cubierta Abierta 360°",
            "Entradas Móviles Inmediatas",
            "Sin Colas En Taquilla",
            "Paseo De 1 Hora Por El Sena",
            "Audioguía En Español",
            "Opiniones Probadas 2026",
            "Salidas Cada 30 Minutos",
            "Vistas Increíbles De París"
        ],
        "descriptions": [
            "Probamos y comparamos los 5 mejores paseos en barco por el Sena. Compara vistas y precios.",
            "Entradas oficiales desde 18€ Adultos y 9€ Niños (50% Dto). Sin esperas en taquillas.",
            "Compara Bateaux Parisiens, Bateaux-Mouches y Vedettes de Paris antes de comprar.",
            "Salidas cada 30 min junto a la Torre Eiffel. Cubiertas panorámicas 360° y audioguía."
        ]
    },
    {
        "lang": "de",
        "lang_id": "1001",
        "campaign_name": "[BOF] Paris - Sightseeing Cruise (DE)",
        "ad_group_name": "Paris Sightseeing Cruise BOF - DE",
        "landing_url": "https://deals.thecruisedetective.com/de/seine-rundfahrt-paris",
        "path1": "Paris",
        "path2": "Seine-Rundfahrt",
        "keywords": [
            "seine rundfahrt",
            "seine rundfahrt paris",
            "seine schifffahrt",
            "seine schifffahrt paris",
            "beste seine rundfahrt",
            "bootstour paris",
            "bootsfahrt paris seine",
            "seine bootsfahrt tickets",
            "eiffelturm schifffahrt",
            "paris sightseeing schifffahrt",
            "schifffahrt paris tickets",
            "seine schifffahrt 1 stunde",
            "bootstour seine paris",
            "schiffstour paris"
        ],
        "negatives": [
            "dinner", "abendessen", "mittagessen", "restaurant", "kostenlos",
            "gratis", "jobs", "karriere", "wikipedia", "stornierung"
        ],
        "headlines": [
            "Seine Rundfahrt Paris 2026",
            "Beste Seine Schifffahrt",
            "Seine Rundfahrt Tickets 18€",
            "Top 5 Paris Boote Im Test",
            "Kinder 50% Rabatt (9€ 4-11)",
            "Abfahrt Direkt Am Eiffelturm",
            "Bateaux Parisiens & Mouches",
            "360° Panorama Freideck",
            "Sofortige Smartphone Tickets",
            "Keine Warteschlange Kasse",
            "1 Stunde Seine Bootstour",
            "Audioguide Auf Deutsch",
            "Getestet Vor Ort 2026",
            "Abfahrt Alle 30 Minuten",
            "Bester Eiffelturm Blick"
        ],
        "descriptions": [
            "Wir haben die 5 beliebtesten Seine Rundfahrten getestet. Vergleichen Sie Boote & Preise.",
            "Offizielle Smartphone-Tickets ab 18€ Erw. & 9€ Kinder (50% Rabatt). Keine Kassen-Schlange.",
            "Bateaux Parisiens, Bateaux-Mouches & Vedettes de Paris im direkten Vergleich vor dem Kauf.",
            "Abfahrt alle 30 Min direkt am Eiffelturm. 360° Panorama-Aussichtsdeck & Audio-App."
        ]
    },
    {
        "lang": "nl",
        "lang_id": "1010",
        "campaign_name": "[BOF] Paris - Sightseeing Cruise (NL)",
        "ad_group_name": "Paris Sightseeing Cruise BOF - NL",
        "landing_url": "https://deals.thecruisedetective.com/nl/rondvaart-seine-parijs",
        "path1": "Parijs",
        "path2": "Rondvaart-Seine",
        "keywords": [
            "rondvaart seine",
            "rondvaart seine parijs",
            "boottocht parijs",
            "boottocht seine parijs",
            "beste rondvaart seine",
            "seine boottocht tickets",
            "rondvaart eiffeltoren",
            "boottocht parijs seine",
            "rondvaartboot parijs",
            "tickets boottocht parijs",
            "seine rondvaart parijs",
            "boottocht over de seine",
            "rondvaart parijs 1 uur",
            "boot huren parijs seine"
        ],
        "negatives": [
            "diner", "lunch", "eten", "restaurant", "gratis",
            "vacatures", "werk", "wikipedia", "annuleren"
        ],
        "headlines": [
            "Rondvaart Seine Parijs 2026",
            "Beste Rondvaart Seine",
            "Tickets Boottocht Seine 18€",
            "Top 5 Rondvaarten Getest",
            "Kinderen 50% Korting (9€)",
            "Vertrek Bij De Eiffeltoren",
            "Bateaux Parisiens & Mouches",
            "360° Open Panoramadek",
            "Direct Mobiele QR Tickets",
            "Sla De Kassarij Over",
            "1 Uur Boottocht Over Seine",
            "Audiogids In Het Nederlands",
            "Persoonlijk Getest 2026",
            "Elke 30 Minuten Afvaart",
            "Prachtig Uitzicht Eiffeltoren"
        ],
        "descriptions": [
            "We testten de 5 populairste rondvaarten op de Seine. Vergelijk dekken, routes & prijzen.",
            "Officiële mobiele tickets vanaf 18€ Volw. & 9€ Kind (50% korting). Sla de wachtrij over.",
            "Vergelijk Bateaux Parisiens, Bateaux-Mouches en Vedettes de Paris direct naast elkaar.",
            "Elke 30 minuten vertrek direct onder de Eiffeltoren. 360° open bovendek & audiogids."
        ]
    },
    {
        "lang": "it",
        "lang_id": "1004",
        "campaign_name": "[BOF] Paris - Sightseeing Cruise (IT)",
        "ad_group_name": "Paris Sightseeing Cruise BOF - IT",
        "landing_url": "https://deals.thecruisedetective.com/it/crociera-senna-parigi",
        "path1": "Parigi",
        "path2": "Crociera-Senna",
        "keywords": [
            "crociera senna",
            "crociera senna parigi",
            "crociera sulla senna",
            "migliore crociera senna",
            "giro in battello parigi",
            "giro in barca parigi senna",
            "biglietti crociera senna",
            "crociera tour eiffel",
            "battello senna parigi",
            "giro battello senna",
            "crociera senna 1 ora",
            "battelli parigini senna",
            "tour in barca parigi",
            "crociera promenade parigi"
        ],
        "negatives": [
            "cena", "pranzo", "ristorante", "gratis", "lavoro",
            "carriera", "wikipedia", "rimborso", "cancellazione"
        ],
        "headlines": [
            "Crociera Senna Parigi 2026",
            "Migliore Crociera Senna",
            "Biglietti Crociera Senna 18€",
            "Top 5 Battelli Confrontati",
            "Bambini -50% (9€ 4-11 Anni)",
            "Imbarco Sotto Torre Eiffel",
            "Bateaux Parisiens & Mouches",
            "Ponte Superiore Aperto 360°",
            "Biglietti Smartphone Subito",
            "Salta La Coda In Cassa",
            "Tour Di 1 Ora Sulla Senna",
            "Audioguida In Italiano",
            "Classifica Verificata 2026",
            "Partenze Ogni 30 Minuti",
            "Vista Iconica Torre Eiffel"
        ],
        "descriptions": [
            "Abbiamo provato i 5 battelli turistici sulla Senna. Confronta terrazze, orari e prezzi.",
            "Biglietti ufficiali da 18€ Adulti e 9€ Bambini (-50%). Salta le lunghe code alle casse.",
            "Confronta Bateaux Parisiens, Bateaux-Mouches e Vedettes de Paris prima di prenotare.",
            "Partenze ogni 30 min ai piedi della Torre Eiffel. Ponte aperto a 360° e audioguida mobile."
        ]
    }
]

# Validate headline and description lengths
for cfg in CONFIGS:
    lang = cfg["lang"]
    assert len(cfg["headlines"]) == 15, f"{lang}: Expected 15 headlines, got {len(cfg['headlines'])}"
    assert len(cfg["descriptions"]) == 4, f"{lang}: Expected 4 descriptions, got {len(cfg['descriptions'])}"
    for h in cfg["headlines"]:
        assert len(h) <= 30, f"{lang}: Headline >30 chars: '{h}' ({len(h)})"
    for d in cfg["descriptions"]:
        assert len(d) <= 90, f"{lang}: Description >90 chars: '{d}' ({len(d)})"

print("All headlines and descriptions validated within strict character limits.")

# Build atomic mutate operations per campaign or all together
for i, cfg in enumerate(CONFIGS):
    base_idx = (i + 1) * 100
    budget_temp = f"customers/{CUSTOMER_ID}/campaignBudgets/-{base_idx + 1}"
    campaign_temp = f"customers/{CUSTOMER_ID}/campaigns/-{base_idx + 2}"
    adgroup_temp = f"customers/{CUSTOMER_ID}/adGroups/-{base_idx + 3}"

    ops = []

    # 1. Budget
    ops.append({
        "campaignBudgetOperation": {
            "create": {
                "resourceName": budget_temp,
                "name": f"{cfg['campaign_name']} Budget €20",
                "amountMicros": BUDGET_MICROS,
                "deliveryMethod": "STANDARD"
            }
        }
    })

    # 2. Campaign (Search Only, Target Spend w/ €0.50 Max CPC Ceiling)
    ops.append({
        "campaignOperation": {
            "create": {
                "resourceName": campaign_temp,
                "name": cfg["campaign_name"],
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

    # 3. Language Criterion
    ops.append({
        "campaignCriterionOperation": {
            "create": {
                "campaign": campaign_temp,
                "language": {
                    "languageConstant": f"languageConstants/{cfg['lang_id']}"
                }
            }
        }
    })

    # 4. Negative Keywords
    for neg in cfg["negatives"]:
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
                "name": cfg["ad_group_name"],
                "campaign": campaign_temp,
                "status": "ENABLED",
                "type": "SEARCH_STANDARD",
                "cpcBidMicros": BID_CEILING_MICROS
            }
        }
    })

    # 6. Exact Match Keywords
    for kw in cfg["keywords"]:
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

    # 7. Responsive Search Ad
    rsa_headlines = [{"text": h} for h in cfg["headlines"]]
    rsa_descriptions = [{"text": d} for d in cfg["descriptions"]]

    ops.append({
        "adGroupAdOperation": {
            "create": {
                "adGroup": adgroup_temp,
                "status": "ENABLED",
                "ad": {
                    "finalUrls": [cfg["landing_url"]],
                    "responsiveSearchAd": {
                        "path1": cfg["path1"],
                        "path2": cfg["path2"],
                        "headlines": rsa_headlines,
                        "descriptions": rsa_descriptions
                    }
                }
            }
        }
    })

    url = f"https://googleads.googleapis.com/v26/customers/{CUSTOMER_ID}/googleAds:mutate"
    body = {
        "mutateOperations": ops,
        "validateOnly": validate_only
    }
    req_mutate = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req_mutate) as r:
            res_json = json.loads(r.read().decode())
            print(f"[{cfg['campaign_name']}] SUCCESS! Operations: {len(ops)}")
    except urllib.error.HTTPError as e:
        print(f"[{cfg['campaign_name']}] FAILED ({e.code}):", e.read().decode())
        if not validate_only:
            sys.exit(1)

print(f"\nAll 5 campaigns processed ({mode_str}).")
