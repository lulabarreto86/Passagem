"""Regras que decidem se uma oferta é promoção."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import median

from .modelos import Oferta, Promocao, Rota

# Quantas medições anteriores são necessárias antes de comparar com a média.
MIN_AMOSTRAS = 5
# Não repete o alerta da mesma rota antes disso, a não ser que o preço caia mais.
INTERVALO_REALERTA = timedelta(days=3)


def avaliar(
    rota: Rota,
    oferta: Oferta,
    precos_anteriores: list[float],
) -> Promocao | None:
    """Retorna uma Promocao se a oferta atender a algum critério."""
    motivos: list[str] = []
    referencia = median(precos_anteriores) if len(precos_anteriores) >= MIN_AMOSTRAS else None

    if rota.preco_maximo is not None and oferta.preco <= rota.preco_maximo:
        motivos.append(f"abaixo do seu limite de {_fmt(rota.preco_maximo, oferta.moeda)}")

    if referencia:
        queda = (referencia - oferta.preco) / referencia * 100
        if queda >= rota.queda_minima_pct:
            motivos.append(
                f"{queda:.0f}% abaixo do preço típico ({_fmt(referencia, oferta.moeda)})"
            )

    if oferta.nivel_preco == "low":
        motivos.append("Google Flights classifica como preço baixo")

    if not motivos:
        return None
    # Informação extra (sozinha não dispara alerta, para não avisar quedas de 1%).
    if len(precos_anteriores) >= MIN_AMOSTRAS and oferta.preco < min(precos_anteriores):
        motivos.append("menor preço já registrado")
    return Promocao(rota=rota, oferta=oferta, motivos=motivos, media_historica=referencia)


def deve_alertar(
    promocao: Promocao,
    ultimo_alerta: dict | None,
    agora: datetime | None = None,
) -> bool:
    """Evita mandar o mesmo alerta toda hora."""
    if not ultimo_alerta:
        return True
    agora = agora or datetime.now(timezone.utc)
    if promocao.oferta.preco < ultimo_alerta["preco"] * 0.97:
        return True  # caiu pelo menos mais 3% desde o último aviso
    quando = datetime.fromisoformat(ultimo_alerta["quando"])
    return agora - quando >= INTERVALO_REALERTA


def _fmt(valor: float, moeda: str) -> str:
    simbolo = {"BRL": "R$", "USD": "US$", "EUR": "€"}.get(moeda.upper(), moeda.upper())
    inteiro = f"{valor:,.0f}".replace(",", ".")
    return f"{simbolo} {inteiro}"


formatar_preco = _fmt
