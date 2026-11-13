"""Envio dos alertas (Telegram e/ou terminal)."""

from __future__ import annotations

import os
from datetime import date

import requests

from .analise import formatar_preco
from .modelos import Promocao, _data_legivel


def montar_mensagem(p: Promocao) -> str:
    o = p.oferta
    linhas = [
        f"✈️ Promoção: {p.rota.descricao}",
        f"💰 {formatar_preco(o.preco, o.moeda)}",
    ]
    datas = " a ".join(_data_legivel(d) for d in (o.data_ida, o.data_volta) if d)
    if o.data_ida and o.data_volta:
        dias = (date.fromisoformat(o.data_volta) - date.fromisoformat(o.data_ida)).days
        datas += f" ({dias} dias)"
    if datas:
        linhas.append(f"📅 {datas}")
    aeroporto = o.extras.get("aeroporto_origem")
    if aeroporto and aeroporto != p.rota.origem:
        linhas.append(f"🛬 Saindo do aeroporto {aeroporto}")
    detalhes = []
    if o.companhia:
        detalhes.append(o.companhia)
    if o.escalas is not None:
        detalhes.append("voo direto" if o.escalas == 0 else f"{o.escalas} escala(s)")
    if detalhes:
        linhas.append("🛫 " + " · ".join(detalhes))
    linhas.append("📉 " + "; ".join(p.motivos))
    if o.link:
        linhas.append(f"🔗 {o.link}")
    return "\n".join(linhas)


def enviar(promocoes: list[Promocao], simular: bool = False) -> None:
    if not promocoes:
        return
    mensagens = [montar_mensagem(p) for p in promocoes]
    for m in mensagens:
        print(m, end="\n\n")

    _resumo_github(mensagens)

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if simular or not (token and chat_id):
        if not simular:
            print("(Telegram não configurado: defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID)")
        return
    for m in mensagens:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": m, "disable_web_page_preview": True},
            timeout=30,
        )
        r.raise_for_status()


def _resumo_github(mensagens: list[str]) -> None:
    """Quando roda no GitHub Actions, mostra os alertas no resumo da execução."""
    caminho = os.environ.get("GITHUB_STEP_SUMMARY")
    if not caminho:
        return
    with open(caminho, "a", encoding="utf-8") as f:
        f.write("## Promoções encontradas\n\n")
        for m in mensagens:
            f.write(m.replace("\n", "  \n") + "\n\n---\n\n")
