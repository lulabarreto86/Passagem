"""Histórico de preços salvo em JSON (versionado no próprio repositório)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

MAX_REGISTROS = 300


class Historico:
    def __init__(self, caminho: Path):
        self.caminho = caminho
        self.dados: dict = {}
        if caminho.exists():
            self.dados = json.loads(caminho.read_text(encoding="utf-8") or "{}")

    def _rota(self, chave: str) -> dict:
        return self.dados.setdefault(chave, {"precos": [], "ultimo_alerta": None})

    def precos(self, chave: str) -> list[float]:
        return [p["preco"] for p in self._rota(chave)["precos"]]

    def registrar(self, chave: str, preco: float, quando: datetime | None = None) -> None:
        quando = quando or datetime.now(timezone.utc)
        lista = self._rota(chave)["precos"]
        lista.append({"quando": quando.isoformat(timespec="seconds"), "preco": preco})
        del lista[:-MAX_REGISTROS]

    def ultimo_alerta(self, chave: str) -> dict | None:
        return self._rota(chave)["ultimo_alerta"]

    def marcar_alerta(self, chave: str, preco: float, quando: datetime | None = None) -> None:
        quando = quando or datetime.now(timezone.utc)
        self._rota(chave)["ultimo_alerta"] = {
            "quando": quando.isoformat(timespec="seconds"),
            "preco": preco,
        }

    def salvar(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho.write_text(
            json.dumps(self.dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
