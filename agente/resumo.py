"""Resumo semanal: menor preço atual de cada destino, por grupo, com a tendência."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .analise import formatar_preco
from .historico import Historico
from .modelos import nome_cidade

DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
BANDEIRAS = {"Europa": "🇪🇺", "Estados Unidos": "🇺🇸", "Brasil e América do Sul": "🌎", "Nacional": "🇧🇷"}


def _agora_local(cfg: dict, agora: datetime | None) -> datetime:
    fuso = ZoneInfo(cfg.get("fuso", "America/Recife"))
    return (agora or datetime.now(timezone.utc)).astimezone(fuso)


def deve_enviar(cfg: dict, historico: Historico, agora: datetime | None = None) -> bool:
    local = _agora_local(cfg, agora)
    dia = DIAS.index(str(cfg.get("dia", "domingo")).lower())
    if local.weekday() != dia or local.hour < int(cfg.get("hora", 9)):
        return False
    return historico.meta("resumo_ultimo_envio") != local.date().isoformat()


def marcar_enviado(cfg: dict, historico: Historico, agora: datetime | None = None) -> None:
    historico.definir_meta("resumo_ultimo_envio", _agora_local(cfg, agora).date().isoformat())


def _preco_ha_uma_semana(precos: list[dict], agora: datetime) -> float | None:
    limite = agora - timedelta(days=6)
    antigos = [p for p in precos if datetime.fromisoformat(p["quando"]) <= limite]
    return antigos[-1]["preco"] if antigos else None


def montar(cfg: dict, historico: Historico, agora: datetime | None = None) -> str:
    agora = agora or datetime.now(timezone.utc)
    por_grupo = int(cfg.get("por_grupo", 6))
    recentes = agora - timedelta(days=8)

    # grupo -> destino -> (preço, origem, preço de uma semana atrás)
    grupos: dict[str, dict[str, tuple]] = {}
    for dados in historico.rotas().values():
        info, precos = dados.get("info"), dados.get("precos") or []
        if not info or not precos or datetime.fromisoformat(precos[-1]["quando"]) < recentes:
            continue  # rota antiga ou removida do config
        atual = precos[-1]["preco"]
        destino = nome_cidade(info["destino"])
        melhor = grupos.setdefault(info["grupo"], {}).get(destino)
        if melhor is None or atual < melhor[0]:
            grupos[info["grupo"]][destino] = (
                atual, nome_cidade(info["origem"]), _preco_ha_uma_semana(precos, agora)
            )

    if not grupos:
        return "📊 Resumo semanal\nAinda não há preços coletados."

    linhas = ["📊 Resumo semanal", "Menor preço ida e volta de cada destino:"]
    for grupo in sorted(grupos, key=lambda g: min(v[0] for v in grupos[g].values())):
        linhas.append(f"\n{BANDEIRAS.get(grupo, '✈️')} {grupo}")
        itens = sorted(grupos[grupo].items(), key=lambda kv: kv[1][0])
        for destino, (preco, origem, antes) in itens[:por_grupo]:
            linha = f"• {destino}: {formatar_preco(preco, 'BRL')} (de {origem})"
            if antes:
                variacao = (preco - antes) / antes * 100
                if abs(variacao) >= 1:
                    linha += f" {'🔻' if variacao < 0 else '🔺'}{abs(variacao):.0f}%"
                else:
                    linha += " ➖"
            linhas.append(linha)
        if len(itens) > por_grupo:
            linhas.append(f"  …e mais {len(itens) - por_grupo} destinos")
    linhas.append("\n🔻/🔺 = variação em relação à semana passada")
    return "\n".join(linhas)
