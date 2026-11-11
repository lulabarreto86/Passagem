"""Fonte gratuita: API de dados da Aviasales/Travelpayouts.

Os preços vêm do cache de buscas recentes feitas por usuários da Aviasales,
então não são em tempo real, mas servem bem para detectar quedas de preço.
Aceita o mês inteiro como data ("2027-01"), o que é ótimo para achar o dia
mais barato.

Token gratuito: https://www.travelpayouts.com/ (Perfil → API token).
Variável de ambiente: TRAVELPAYOUTS_TOKEN
"""

from __future__ import annotations

import os

import requests

from ..modelos import Oferta, Rota

URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
SITE = "https://www.aviasales.com"


def buscar(rota: Rota, moeda: str) -> list[Oferta]:
    token = os.environ.get("TRAVELPAYOUTS_TOKEN")
    if not token:
        raise RuntimeError("Defina a variável de ambiente TRAVELPAYOUTS_TOKEN.")

    params = {
        "origin": rota.origem,
        "destination": rota.destino,
        "departure_at": rota.ida,
        "currency": moeda.lower(),
        "sorting": "price",
        "direct": "true" if rota.apenas_direto else "false",
        "limit": 10,
        "one_way": "false" if rota.volta else "true",
    }
    if rota.volta:
        params["return_at"] = rota.volta

    resposta = requests.get(
        URL, params=params, headers={"X-Access-Token": token}, timeout=30
    )
    resposta.raise_for_status()
    corpo = resposta.json()
    if not corpo.get("success", True):
        raise RuntimeError(f"Travelpayouts retornou erro: {corpo.get('error')}")

    moeda_resp = (corpo.get("currency") or moeda).upper()
    ofertas = []
    for item in corpo.get("data", []):
        link = item.get("link")
        ofertas.append(
            Oferta(
                preco=float(item["price"]),
                moeda=moeda_resp,
                companhia=item.get("airline"),
                data_ida=(item.get("departure_at") or "")[:10] or None,
                data_volta=(item.get("return_at") or "")[:10] or None,
                escalas=item.get("transfers"),
                link=f"{SITE}{link}" if link else None,
            )
        )
    return ofertas
