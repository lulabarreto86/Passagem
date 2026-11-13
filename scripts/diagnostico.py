"""Diagnóstico temporário: quanto dado a Travelpayouts tem para cada tipo de consulta."""
import os, time
from collections import Counter
from datetime import date
import requests

URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
TOKEN = os.environ["TRAVELPAYOUTS_TOKEN"]

def q(**p):
    base = {"currency": "brl", "sorting": "price", "limit": 1000}
    base.update(p)
    time.sleep(0.5)
    r = requests.get(URL, params=base, headers={"X-Access-Token": TOKEN}, timeout=30)
    if r.status_code != 200:
        return f"HTTP {r.status_code}: {r.text[:150]}"
    dados = r.json().get("data", [])
    durs = Counter()
    for d in dados:
        if d.get("return_at"):
            durs[(date.fromisoformat(d["return_at"][:10]) - date.fromisoformat(d["departure_at"][:10])).days] += 1
    ex = [(d.get("destination"), d["price"], d["departure_at"][:10], (d.get("return_at") or "")[:10]) for d in dados[:4]]
    return f"{len(dados)} ofertas | durações {dict(sorted(durs.items()))} | ex {ex}"

pares = [("REC", "LIS"), ("NAT", "LIS"), ("REC", "MIA"), ("REC", "RIO"), ("JPA", "SAO"), ("NAT", "SAO")]
for o, d in pares:
    print(f"\n=== {o} -> {d}")
    print(" a) abr/abr      :", q(origin=o, destination=d, departure_at="2027-04", return_at="2027-04", one_way="false"))
    print(" b) abr/sem volta:", q(origin=o, destination=d, departure_at="2027-04", one_way="false"))
    print(" c) abr só ida   :", q(origin=o, destination=d, departure_at="2027-04", one_way="true"))
    print(" d) qualquer data:", q(origin=o, destination=d, one_way="false"))
    print(" e) dez/2026     :", q(origin=o, destination=d, departure_at="2026-12", one_way="false"))
for o in ("REC", "NAT", "JPA"):
    print(f"\n=== {o} -> qualquer destino, abril")
    print(" f)", q(origin=o, departure_at="2027-04", one_way="false"))
