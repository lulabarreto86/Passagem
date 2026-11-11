"""Fontes de preços de passagens.

Cada fonte expõe ``buscar(rota, moeda) -> list[Oferta]``.
"""

from __future__ import annotations

from typing import Callable

from ..modelos import Oferta, Rota
from . import google_flights, travelpayouts

FONTES: dict[str, Callable[[Rota, str], list[Oferta]]] = {
    "travelpayouts": travelpayouts.buscar,
    "google_flights": google_flights.buscar,
}


def buscar(rota: Rota, moeda: str) -> list[Oferta]:
    try:
        funcao = FONTES[rota.fonte]
    except KeyError:
        raise ValueError(
            f"Fonte desconhecida '{rota.fonte}'. Opções: {', '.join(FONTES)}"
        ) from None
    return funcao(rota, moeda)
