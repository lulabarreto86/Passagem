"""Ponto de entrada: python -m agente [--config config.yaml] [--simular]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from . import analise, fontes, notificacao
from .historico import Historico
from .modelos import Rota


def carregar_config(caminho: Path) -> tuple[str, list[Rota]]:
    cfg = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    padrao = cfg.get("padrao", {}) or {}
    rotas = []
    for item in cfg.get("rotas", []) or []:
        dados = {**padrao, **item}
        for campo in ("ida", "volta"):
            if dados.get(campo) is not None:
                dados[campo] = str(dados[campo]).strip()
        # "origem" e "destino" podem ser um código ou uma lista de códigos:
        # a regra vira uma rota para cada combinação.
        origens = _lista(dados.pop("origem"))
        destinos = _lista(dados.pop("destino"))
        for origem in origens:
            for destino in destinos:
                if origem != destino:
                    rotas.append(Rota(origem=origem, destino=destino, **dados))
    return str(cfg.get("moeda", "BRL")).upper(), rotas


def _lista(valor) -> list[str]:
    if isinstance(valor, str):
        valor = valor.split(",")
    return [str(v).strip().upper() for v in valor if str(v).strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agente de promoções de passagens aéreas")
    parser.add_argument("--config", default="config.yaml", type=Path)
    parser.add_argument("--historico", default="data/historico.json", type=Path)
    parser.add_argument(
        "--simular", action="store_true", help="não envia Telegram nem salva histórico"
    )
    args = parser.parse_args(argv)

    moeda, rotas = carregar_config(args.config)
    historico = Historico(args.historico)
    promocoes = []
    falhas = 0

    for rota in rotas:
        try:
            ofertas = fontes.buscar(rota, moeda)
        except Exception as erro:  # uma rota com problema não derruba as outras
            falhas += 1
            print(f"[erro] {rota.descricao}: {erro}", file=sys.stderr)
            continue
        if not ofertas:
            print(f"[--] {rota.descricao}: nenhuma oferta encontrada")
            continue

        melhor = min(ofertas, key=lambda o: o.preco)
        anteriores = historico.precos(rota.chave)
        promocao = analise.avaliar(rota, melhor, anteriores)
        historico.registrar(rota.chave, melhor.preco)

        status = "PROMO" if promocao else "ok"
        print(f"[{status}] {rota.descricao}: {analise.formatar_preco(melhor.preco, melhor.moeda)}")

        if promocao and analise.deve_alertar(promocao, historico.ultimo_alerta(rota.chave)):
            promocoes.append(promocao)
            historico.marcar_alerta(rota.chave, melhor.preco)

    notificacao.enviar(promocoes, simular=args.simular)
    if not args.simular:
        historico.salvar()

    # Só falha a execução se TODAS as rotas deram erro (ex.: token inválido).
    return 1 if rotas and falhas == len(rotas) else 0


if __name__ == "__main__":
    sys.exit(main())
