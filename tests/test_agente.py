from datetime import datetime, timedelta, timezone

from agente import __main__ as principal
from agente import analise, fontes
from agente.historico import Historico
from agente.modelos import Oferta, Rota


def rota(**kw):
    base = dict(origem="SAO", destino="LIS", ida="2027-03", volta="2027-03")
    base.update(kw)
    return Rota(**base)


def test_abaixo_do_preco_maximo_e_promocao():
    p = analise.avaliar(rota(preco_maximo=3500), Oferta(3200, "BRL"), [])
    assert p and "limite" in p.motivos[0]


def test_preco_normal_sem_historico_nao_e_promocao():
    assert analise.avaliar(rota(), Oferta(4000, "BRL"), []) is None


def test_queda_em_relacao_ao_historico():
    hist = [5000, 5100, 4900, 5000, 5050]
    p = analise.avaliar(rota(queda_minima_pct=20), Oferta(3800, "BRL"), hist)
    assert p is not None
    assert any("abaixo do preço típico" in m for m in p.motivos)


def test_queda_pequena_nao_dispara():
    hist = [5000, 5100, 4900, 5000, 5050]
    assert analise.avaliar(rota(queda_minima_pct=20), Oferta(4950, "BRL"), hist) is None


def test_nao_repete_alerta_em_seguida():
    agora = datetime(2027, 1, 1, tzinfo=timezone.utc)
    p = analise.avaliar(rota(preco_maximo=3500), Oferta(3200, "BRL"), [])
    ultimo = {"quando": (agora - timedelta(hours=6)).isoformat(), "preco": 3200}
    assert not analise.deve_alertar(p, ultimo, agora)
    # mas avisa de novo se cair mais
    p2 = analise.avaliar(rota(preco_maximo=3500), Oferta(3000, "BRL"), [])
    assert analise.deve_alertar(p2, ultimo, agora)
    # ou depois de alguns dias
    assert analise.deve_alertar(p, ultimo, agora + timedelta(days=3))


def test_fluxo_completo(tmp_path, monkeypatch, capsys):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "moeda: BRL\nrotas:\n  - {origem: sao, destino: lis, ida: '2027-03', preco_maximo: 3500}\n"
    )
    hist = tmp_path / "historico.json"
    monkeypatch.setitem(
        fontes.FONTES, "travelpayouts", lambda r, m: [Oferta(4000, m), Oferta(3300, m, "TP")]
    )
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    assert principal.main(["--config", str(cfg), "--historico", str(hist)]) == 0
    saida = capsys.readouterr().out
    assert "Promoção: SAO → LIS" in saida and "R$ 3.300" in saida

    h = Historico(hist)
    chave = rota(volta=None).chave
    assert h.precos(chave) == [3300.0]
    assert h.ultimo_alerta(chave)["preco"] == 3300.0
