"""Diagnóstico temporário: formato da SerpApi (Travel Explore) e feeds de promoções."""
import json, os
import requests

KEY = os.environ.get("SERPAPI_KEY", "")
print("SERPAPI_KEY definida:", bool(KEY))

def mostrar(nome, params):
    print(f"\n===== {nome}")
    r = requests.get("https://serpapi.com/search.json", params={**params, "api_key": KEY}, timeout=90)
    print("HTTP", r.status_code)
    try:
        d = r.json()
    except Exception:
        print(r.text[:500]); return
    if "error" in d:
        print("ERRO:", d["error"])
    print("chaves:", list(d.keys()))
    print("search_parameters:", json.dumps(d.get("search_parameters"), ensure_ascii=False))
    for k, v in d.items():
        if isinstance(v, list):
            print(f"lista '{k}': {len(v)} itens")
            for item in v[:3]:
                print("   ", json.dumps(item, ensure_ascii=False)[:900])
            if v and isinstance(v[0], dict) and "name" in v[0]:
                print("    nomes:", [x.get("name") for x in v][:60])

if KEY:
    a = requests.get("https://serpapi.com/account.json", params={"api_key": KEY}, timeout=30).json()
    print("conta:", {k: a.get(k) for k in ("plan_name", "searches_per_month", "plan_searches_left", "this_month_usage", "account_rate_limit_per_hour")})
    base = {"engine": "google_travel_explore", "departure_id": "REC", "currency": "BRL", "hl": "pt-BR", "gl": "br"}
    mostrar("REC abril 1 semana", {**base, "month": "4", "travel_duration": "2"})
    mostrar("REC abril 2 semanas Europa", {**base, "month": "4", "travel_duration": "3", "arrival_area_id": "/m/02j9z"})
    mostrar("JPA datas exatas", {**base, "departure_id": "JPA", "outbound_date": "2027-04-10", "return_date": "2027-04-20"})

print("\n\n######## FEEDS")
feeds = [
    "https://www.melhoresdestinos.com.br/feed",
    "https://passageirodeprimeira.com/feed/",
    "https://pontospravoar.com/feed/",
    "https://www.mestredasmilhas.com/feeds/posts/default?alt=rss",
]
import xml.etree.ElementTree as ET
for f in feeds:
    try:
        r = requests.get(f, timeout=30, headers={"User-Agent": "Mozilla/5.0 (agente-passagens)"})
        itens = ET.fromstring(r.content).findall(".//item")
        titulos = [i.findtext("title") for i in itens]
        smiles = [t for t in titulos if t and "smiles" in t.lower()]
        print(f"\n{f}: HTTP {r.status_code}, {len(itens)} itens, {len(smiles)} com Smiles")
        for t in titulos[:5]: print("   -", t)
        for t in smiles[:5]: print("   [smiles]", t)
    except Exception as e:
        print(f"\n{f}: FALHOU {type(e).__name__}: {str(e)[:200]}")
