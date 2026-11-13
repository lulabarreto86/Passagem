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
import time
from datetime import date, timedelta

import requests

from ..modelos import Oferta, Rota

URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
SITE = "https://www.aviasales.com"
PAUSA_ENTRE_CHAMADAS = 0.4  # segundos, para respeitar o limite da API


def buscar(rota: Rota, moeda: str) -> list[Oferta]:
    token = os.environ.get("TRAVELPAYOUTS_TOKEN")
    if not token:
        raise RuntimeError("Defina a variável de ambiente TRAVELPAYOUTS_TOKEN.")

    ofertas: list[Oferta] = []
    for volta in _voltas(rota):
        ofertas += _consultar(rota, moeda, token, volta)
    return [o for o in ofertas if rota.duracao_ok(o.data_ida, o.data_volta)]


def _voltas(rota: Rota) -> list[str | None]:
    """Quais valores de return_at consultar.

    Com duração em dias e sem "volta" explícita, a volta pode cair no mesmo mês
    da ida ou no seguinte (ex.: ida 25/04, volta 05/05), então consulta os dois.
    """
    if rota.volta or not rota.ida_e_volta:
        return [rota.volta]
    ano, mes = int(rota.ida[:4]), int(rota.ida[5:7])
    if len(rota.ida) == 10:  # data exata: só os meses possíveis da volta
        ida = date.fromisoformat(rota.ida)
        inicio = ida + timedelta(days=rota.dias_min or 1)
        fim = ida + timedelta(days=rota.dias_max or 60)
        return sorted({inicio.strftime("%Y-%m"), fim.strftime("%Y-%m")})
    proximo = f"{ano + mes // 12}-{mes % 12 + 1:02d}"
    return [f"{ano}-{mes:02d}", proximo]


def _consultar(rota: Rota, moeda: str, token: str, volta: str | None) -> list[Oferta]:
    params = {
        "origin": rota.origem,
        "destination": rota.destino,
        "departure_at": rota.ida,
        "currency": moeda.lower(),
        "sorting": "price",
        "direct": "true" if rota.apenas_direto else "false",
        "limit": 100,
        "one_way": "false" if rota.ida_e_volta else "true",
    }
    if volta:
        params["return_at"] = volta

    for tentativa in range(3):
        time.sleep(PAUSA_ENTRE_CHAMADAS)
        resposta = requests.get(
            URL, params=params, headers={"X-Access-Token": token}, timeout=30
        )
        if resposta.status_code != 429:  # 429 = muitas chamadas; espera e tenta de novo
            break
        time.sleep(10 * (tentativa + 1))
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
                extras={"aeroporto_origem": item.get("origin_airport")},
            )
        )
    return ofertas
