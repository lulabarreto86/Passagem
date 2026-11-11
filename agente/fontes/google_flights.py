"""Fonte: Google Flights via SerpApi.

Preços em tempo real e, de quebra, o próprio Google diz se o preço está
"low"/"typical"/"high" para aquela rota. Exige datas exatas (AAAA-MM-DD).
O plano gratuito da SerpApi tem cota mensal pequena, então use com
moderação (poucas rotas e intervalo maior entre execuções).

Chave: https://serpapi.com/ — variável de ambiente: SERPAPI_KEY
"""

from __future__ import annotations

import os
import re

import requests

from ..modelos import Oferta, Rota

URL = "https://serpapi.com/search.json"
_DATA_EXATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def buscar(rota: Rota, moeda: str) -> list[Oferta]:
    chave = os.environ.get("SERPAPI_KEY")
    if not chave:
        raise RuntimeError("Defina a variável de ambiente SERPAPI_KEY.")
    for data in (rota.ida, rota.volta):
        if data and not _DATA_EXATA.match(data):
            raise ValueError(
                f"google_flights exige datas exatas (AAAA-MM-DD); recebeu '{data}'."
            )

    params = {
        "engine": "google_flights",
        "departure_id": rota.origem,
        "arrival_id": rota.destino,
        "outbound_date": rota.ida,
        "currency": moeda.upper(),
        "hl": "pt-BR",
        "gl": "br",
        "type": "1" if rota.volta else "2",
        "api_key": chave,
    }
    if rota.volta:
        params["return_date"] = rota.volta
    if rota.apenas_direto:
        params["stops"] = "1"

    resposta = requests.get(URL, params=params, timeout=60)
    resposta.raise_for_status()
    corpo = resposta.json()
    if "error" in corpo:
        raise RuntimeError(f"SerpApi retornou erro: {corpo['error']}")

    nivel = (corpo.get("price_insights") or {}).get("price_level")
    link = (corpo.get("search_metadata") or {}).get("google_flights_url")

    ofertas = []
    for grupo in corpo.get("best_flights", []) + corpo.get("other_flights", []):
        if "price" not in grupo:
            continue
        trechos = grupo.get("flights") or []
        companhias = sorted({t.get("airline") for t in trechos if t.get("airline")})
        ofertas.append(
            Oferta(
                preco=float(grupo["price"]),
                moeda=moeda.upper(),
                companhia=", ".join(companhias) or None,
                data_ida=rota.ida,
                data_volta=rota.volta,
                escalas=max(len(trechos) - 1, 0) if trechos else None,
                link=link,
                nivel_preco=nivel,
            )
        )
    return ofertas
