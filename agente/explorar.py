"""Busca "Explorar" do Google: várias origens × qualquer destino de uma lista.

Configurada na seção `explorar:` do config.yaml. Como a SerpApi grátis tem
250 buscas/mês, roda no máximo uma vez a cada `intervalo_horas`.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

from . import analise
from .fontes import google_explore
from .historico import Historico
from .modelos import Oferta, Promocao, Rota


def _normalizar(texto: str | None) -> str:
    return (texto or "").strip().lower()


def deve_rodar(cfg: dict, historico: Historico, agora: datetime | None = None) -> bool:
    agora = agora or datetime.now(timezone.utc)
    ultima = historico.meta("explorar_ultima_execucao")
    if not ultima:
        return True
    intervalo = timedelta(hours=float(cfg.get("intervalo_horas", 23)))
    return agora - datetime.fromisoformat(ultima) >= intervalo


def executar(cfg: dict, moeda: str, historico: Historico, forcar: bool = False) -> list[Promocao]:
    if not cfg or not cfg.get("grupos"):
        return []
    if not forcar and not deve_rodar(cfg, historico):
        print("[explorar] já rodou nas últimas horas; pulando para poupar a cota da SerpApi")
        return []

    mes = str(cfg["mes"])
    duracoes = cfg.get("duracoes", ["1 semana", "2 semanas"])
    queda = float(cfg.get("queda_minima_pct", 20))
    promocoes: list[Promocao] = []
    falhas = 0

    for origem in [o.upper() for o in cfg["origens"]]:
        resultados: list[dict] = []
        for duracao in duracoes:
            try:
                resultados += google_explore.explorar(origem, mes, duracao, moeda)
            except Exception as erro:
                falhas += 1
                print(f"[erro] explorar {origem} ({duracao}): {erro}", file=sys.stderr)

        for grupo in cfg["grupos"]:
            promocoes += _avaliar_grupo(origem, mes, grupo, resultados, queda, moeda, historico)

    if falhas < len(cfg["origens"]) * len(duracoes):
        historico.definir_meta(
            "explorar_ultima_execucao", datetime.now(timezone.utc).isoformat(timespec="seconds")
        )
    return promocoes


def _avaliar_grupo(origem, mes, grupo, resultados, queda, moeda, historico) -> list[Promocao]:
    destinos = {_normalizar(d) for d in grupo.get("destinos", [])}
    paises = {_normalizar(p) for p in grupo.get("paises", [])}
    promocoes = []

    # Melhor oferta por destino, respeitando a duração do grupo.
    melhores: dict[str, dict] = {}
    for r in resultados:
        if _normalizar(r["nome"]) not in destinos and _normalizar(r["pais"]) not in paises:
            continue
        rota = _rota(origem, r["nome"], mes, grupo)
        if not rota.duracao_ok(r["ida"], r["volta"]):
            continue
        atual = melhores.get(r["nome"])
        if atual is None or r["preco"] < atual["preco"]:
            melhores[r["nome"]] = r

    for nome, r in sorted(melhores.items()):
        rota = _rota(origem, nome, mes, grupo)
        rota.queda_minima_pct = float(grupo.get("queda_minima_pct", queda))
        oferta = Oferta(
            preco=r["preco"],
            moeda=moeda,
            companhia=r["companhia"],
            data_ida=r["ida"],
            data_volta=r["volta"],
            escalas=r["escalas"],
            link=r["link"],
            extras={"aeroporto_destino": r["aeroporto"]},
        )
        anteriores = historico.precos(rota.chave)
        promocao = analise.avaliar(rota, oferta, anteriores)
        historico.registrar(rota.chave, oferta.preco, info=rota.info)
        print(
            f"[{'PROMO' if promocao else 'ok'}] {rota.descricao}: "
            f"{analise.formatar_preco(oferta.preco, moeda)} ({r['ida']} a {r['volta']})"
        )
        if promocao and analise.deve_alertar(promocao, historico.ultimo_alerta(rota.chave)):
            promocoes.append(promocao)
            historico.marcar_alerta(rota.chave, oferta.preco)
    return promocoes


def _rota(origem: str, destino: str, mes: str, grupo: dict) -> Rota:
    return Rota(
        origem=origem,
        destino=destino,
        ida=mes,
        dias_min=grupo.get("dias_min"),
        dias_max=grupo.get("dias_max"),
        preco_maximo=grupo.get("preco_maximo"),
        fonte="google_explore",
        nome=grupo.get("nome"),
    )
