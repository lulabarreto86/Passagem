"""Promoções de milhas: lê os feeds (RSS) de blogs de milhas e avisa as novidades.

Não acessa o site da Smiles (isso violaria os termos de uso e arriscaria a
conta). Em vez disso, acompanha os blogs que divulgam as promoções.
Configurado na seção `milhas:` do config.yaml.
"""

from __future__ import annotations

import html
import re
import sys
import xml.etree.ElementTree as ET

import requests

from .historico import Historico

MAX_VISTOS = 1000


def _texto(item: ET.Element, tag: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", item.findtext(tag) or "")).strip()


def ler_feed(url: str) -> list[dict]:
    resposta = requests.get(
        url, timeout=30, headers={"User-Agent": "Mozilla/5.0 (agente-passagens)"}
    )
    resposta.raise_for_status()
    itens = []
    for item in ET.fromstring(resposta.content).iter("item"):
        itens.append(
            {
                "titulo": _texto(item, "title"),
                "link": (item.findtext("link") or "").strip(),
                "id": (item.findtext("guid") or item.findtext("link") or "").strip(),
                "categorias": " ".join(c.text or "" for c in item.findall("category")),
            }
        )
    return itens


def combina(item: dict, palavras: list[str]) -> bool:
    texto = f"{item['titulo']} {item['categorias']}".lower()
    return any(p.lower() in texto for p in palavras)


def destaque(item: dict, palavras: list[str]) -> bool:
    titulo = item["titulo"].lower()
    return any(p.lower() in titulo for p in palavras)


def verificar(cfg: dict, historico: Historico) -> list[str]:
    """Retorna as mensagens das promoções novas."""
    if not cfg or not cfg.get("feeds"):
        return []
    palavras = cfg.get("palavras", ["smiles"])
    destaques = cfg.get("destaques", [])
    vistos: list[str] = historico.meta("milhas_vistos") or []
    primeira_vez = not vistos
    novos_ids: list[str] = []
    mensagens = []

    for feed in cfg["feeds"]:
        try:
            itens = ler_feed(feed)
        except Exception as erro:
            print(f"[erro] feed {feed}: {erro}", file=sys.stderr)
            continue
        for item in itens:
            if not item["id"] or item["id"] in vistos or item["id"] in novos_ids:
                continue
            novos_ids.append(item["id"])
            if not combina(item, palavras):
                continue
            print(f"[milhas] {item['titulo']}")
            estrela = "⭐ " if destaque(item, destaques) else ""
            mensagens.append(f"🎟️ {estrela}Milhas: {item['titulo']}\n🔗 {item['link']}")

    historico.definir_meta("milhas_vistos", (vistos + novos_ids)[-MAX_VISTOS:])
    if primeira_vez:
        # Na primeira execução só memoriza o que já existe, para não mandar
        # dezenas de notícias antigas de uma vez.
        print(f"[milhas] primeira execução: {len(mensagens)} notícias antigas memorizadas sem avisar")
        return []
    return mensagens
