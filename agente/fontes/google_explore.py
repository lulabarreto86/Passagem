"""Fonte: "Explorar" do Google Flights via SerpApi (engine google_travel_explore).

Uma única busca devolve ~90 destinos a partir de uma cidade de origem, com o
preço mais barato, as datas e a companhia de cada um. Ideal para "qualquer
destino na Europa" e para origens menores (Natal, João Pessoa), onde a base
da Travelpayouts tem poucos dados.

Chave: https://serpapi.com/ — variável de ambiente: SERPAPI_KEY
Plano gratuito: 250 buscas por mês.
"""

from __future__ import annotations

import os

import requests

URL = "https://serpapi.com/search.json"

# Valores de travel_duration aceitos pela SerpApi.
DURACOES = {"fim de semana": 1, "1 semana": 2, "2 semanas": 3}


def explorar(origem: str, mes: str, duracao: str, moeda: str) -> list[dict]:
    """Retorna os destinos encontrados, já normalizados.

    mes: "AAAA-MM". O Google só aceita o número do mês (próximos meses).
    duracao: uma das chaves de DURACOES.
    """
    chave = os.environ.get("SERPAPI_KEY")
    if not chave:
        raise RuntimeError("Defina a variável de ambiente SERPAPI_KEY.")
    if duracao not in DURACOES:
        raise ValueError(f"Duração '{duracao}' inválida. Opções: {', '.join(DURACOES)}")

    params = {
        "engine": "google_travel_explore",
        "departure_id": origem,
        "month": str(int(mes[5:7])),
        "travel_duration": DURACOES[duracao],
        "currency": moeda.upper(),
        "hl": "pt-BR",
        "gl": "br",
        "api_key": chave,
    }
    resposta = requests.get(URL, params=params, timeout=90)
    resposta.raise_for_status()
    corpo = resposta.json()
    if "error" in corpo:
        if "Empty results" in corpo["error"]:
            return []
        raise RuntimeError(f"SerpApi retornou erro: {corpo['error']}")

    destinos = []
    for d in corpo.get("destinations", []):
        if d.get("flight_price") is None or not d.get("start_date"):
            continue  # o Google às vezes lista o destino sem preço de voo
        if not d["start_date"].startswith(mes):
            continue
        destinos.append(
            {
                "nome": d.get("name"),
                "pais": d.get("country"),
                "aeroporto": (d.get("destination_airport") or {}).get("code"),
                "preco": float(d["flight_price"]),
                "ida": d.get("start_date"),
                "volta": d.get("end_date"),
                "escalas": d.get("number_of_stops"),
                "companhia": d.get("airline"),
                "link": d.get("link"),
            }
        )
    return destinos
