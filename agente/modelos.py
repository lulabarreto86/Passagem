"""Estruturas de dados usadas pelo agente."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Rota:
    """Uma rota monitorada, lida do config.yaml."""

    origem: str
    destino: str
    ida: str  # "AAAA-MM" (mês inteiro) ou "AAAA-MM-DD"
    volta: str | None = None
    preco_maximo: float | None = None
    queda_minima_pct: float = 20.0
    fonte: str = "travelpayouts"
    apenas_direto: bool = False
    nome: str | None = None

    @property
    def chave(self) -> str:
        volta = self.volta or "so-ida"
        return f"{self.origem}-{self.destino}_{self.ida}_{volta}_{self.fonte}"

    @property
    def descricao(self) -> str:
        if self.nome:
            return self.nome
        trecho = f"{self.origem} → {self.destino}"
        datas = f"ida {self.ida}" + (f", volta {self.volta}" if self.volta else " (só ida)")
        return f"{trecho} ({datas})"


@dataclass
class Oferta:
    """Uma passagem encontrada por uma fonte de preços."""

    preco: float
    moeda: str
    companhia: str | None = None
    data_ida: str | None = None
    data_volta: str | None = None
    escalas: int | None = None
    link: str | None = None
    # Avaliação da própria fonte, quando houver (ex.: Google Flights diz "low").
    nivel_preco: str | None = None
    extras: dict = field(default_factory=dict)


@dataclass
class Promocao:
    """Resultado da análise: uma oferta que vale a pena avisar."""

    rota: Rota
    oferta: Oferta
    motivos: list[str]
    media_historica: float | None = None
