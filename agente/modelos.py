"""Estruturas de dados usadas pelo agente."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

# Nomes amigáveis para as mensagens (códigos IATA de cidade/aeroporto).
CIDADES = {
    "NAT": "Natal", "JPA": "João Pessoa", "REC": "Recife", "FOR": "Fortaleza",
    "SSA": "Salvador", "SAO": "São Paulo", "GRU": "Guarulhos", "CGH": "Congonhas",
    "VCP": "Campinas", "RIO": "Rio de Janeiro", "GIG": "Galeão", "SDU": "Santos Dumont",
    "BHZ": "Belo Horizonte", "CNF": "Confins", "BSB": "Brasília", "POA": "Porto Alegre",
    "BUE": "Buenos Aires", "SCL": "Santiago", "MIA": "Miami", "ORL": "Orlando",
    "NYC": "Nova York", "LAX": "Los Angeles", "SFO": "São Francisco",
    "LIS": "Lisboa", "OPO": "Porto", "MAD": "Madri", "BCN": "Barcelona",
    "PAR": "Paris", "ROM": "Roma", "MIL": "Milão", "LON": "Londres",
    "AMS": "Amsterdã", "FRA": "Frankfurt", "MUC": "Munique", "ZRH": "Zurique",
    "BRU": "Bruxelas", "BER": "Berlim", "VIE": "Viena", "PRG": "Praga",
    "ATH": "Atenas", "DUB": "Dublin",
}
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def nome_cidade(codigo: str) -> str:
    return CIDADES.get(codigo, codigo)


def _data_legivel(valor: str) -> str:
    if len(valor) == 7:  # AAAA-MM
        return f"{MESES[int(valor[5:7]) - 1]}/{valor[:4]}"
    return f"{valor[8:10]}/{valor[5:7]}/{valor[:4]}"


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
    # Duração da viagem (ida e volta) em dias. Se definida, "volta" é opcional.
    dias_min: int | None = None
    dias_max: int | None = None

    @property
    def ida_e_volta(self) -> bool:
        return bool(self.volta or self.dias_min or self.dias_max)

    @property
    def chave(self) -> str:
        if self.volta:
            volta = self.volta
        elif self.dias_min or self.dias_max:
            volta = f"{self.dias_min or 1}a{self.dias_max or 99}dias"
        else:
            volta = "so-ida"
        return f"{self.origem}-{self.destino}_{self.ida}_{volta}_{self.fonte}"

    @property
    def descricao(self) -> str:
        trecho = f"{nome_cidade(self.origem)} → {nome_cidade(self.destino)}"
        if self.nome:
            trecho = f"{self.nome}: {trecho}"
        datas = f"ida {_data_legivel(self.ida)}"
        if self.volta:
            datas += f", volta {_data_legivel(self.volta)}"
        if self.dias_min or self.dias_max:
            datas += f", {self.dias_min or 1} a {self.dias_max or '∞'} dias"
        if not self.ida_e_volta:
            datas += " (só ida)"
        return f"{trecho} ({datas})"

    def duracao_ok(self, data_ida: str | None, data_volta: str | None) -> bool:
        """Confere se a oferta respeita dias_min/dias_max."""
        if not (self.dias_min or self.dias_max):
            return True
        if not (data_ida and data_volta):
            return False
        dias = (date.fromisoformat(data_volta[:10]) - date.fromisoformat(data_ida[:10])).days
        return (self.dias_min or 0) <= dias <= (self.dias_max or 10_000)


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
