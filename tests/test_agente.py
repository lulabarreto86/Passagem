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
    assert "Promoção: São Paulo → Lisboa" in saida and "R$ 3.300" in saida

    h = Historico(hist)
    chave = rota(volta=None).chave
    assert h.precos(chave) == [3300.0]
    assert h.ultimo_alerta(chave)["preco"] == 3300.0


def test_config_com_listas_gera_todas_as_combinacoes(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "rotas:\n"
        "  - {origem: [NAT, JPA, REC], destino: [LIS, MAD], ida: '2027-04', dias_min: 9, dias_max: 12}\n"
    )
    _, rotas = principal.carregar_config(cfg)
    assert len(rotas) == 6
    assert {(r.origem, r.destino) for r in rotas} >= {("NAT", "LIS"), ("REC", "MAD")}
    assert all(r.ida_e_volta and r.dias_max == 12 for r in rotas)


def test_duracao_da_viagem():
    r = rota(volta=None, dias_min=5, dias_max=7)
    assert r.duracao_ok("2027-04-10", "2027-04-15")
    assert r.duracao_ok("2027-04-28", "2027-05-05")
    assert not r.duracao_ok("2027-04-10", "2027-04-14")
    assert not r.duracao_ok("2027-04-10", "2027-04-18")
    assert not r.duracao_ok("2027-04-10", None)


def test_travelpayouts_consulta_mes_seguinte_e_filtra_duracao(monkeypatch):
    from agente.fontes import travelpayouts as tp

    chamadas = []

    class Resp:
        status_code = 200

        def __init__(self, dados):
            self.dados = dados

        def raise_for_status(self):
            pass

        def json(self):
            return {"success": True, "currency": "brl", "data": self.dados}

    def falso_get(url, params, headers, timeout):
        chamadas.append(params.get("return_at"))
        if params["return_at"] == "2027-04":
            return Resp([
                {"price": 900, "departure_at": "2027-04-01T10:00", "return_at": "2027-04-03T10:00"},
                {"price": 1500, "departure_at": "2027-04-10T10:00", "return_at": "2027-04-16T10:00"},
            ])
        return Resp([{"price": 1400, "departure_at": "2027-04-28T10:00", "return_at": "2027-05-04T10:00"}])

    monkeypatch.setenv("TRAVELPAYOUTS_TOKEN", "x")
    monkeypatch.setattr(tp, "PAUSA_ENTRE_CHAMADAS", 0)
    monkeypatch.setattr(tp.requests, "get", falso_get)

    ofertas = tp.buscar(rota(origem="REC", destino="RIO", ida="2027-04", volta=None, dias_min=5, dias_max=7), "BRL")
    assert chamadas == ["2027-04", "2027-05"]
    assert sorted(o.preco for o in ofertas) == [1400, 1500]  # a de 2 dias foi descartada


def test_mes_de_dezembro_vira_janeiro():
    from agente.fontes.travelpayouts import _voltas

    assert _voltas(rota(ida="2027-12", volta=None, dias_min=5)) == ["2027-12", "2028-01"]


def test_explorar_filtra_grupos_e_duracao(monkeypatch, tmp_path):
    from agente import explorar
    from agente.fontes import google_explore

    def falso(origem, mes, duracao, moeda):
        base = {"aeroporto": "X", "escalas": 1, "companhia": "Gol", "link": "l"}
        if duracao == "1 semana":
            return [
                {**base, "nome": "Lisboa", "pais": "Portugal", "preco": 4600, "ida": "2027-04-19", "volta": "2027-04-28"},
                {**base, "nome": "Paris", "pais": "França", "preco": 5100, "ida": "2027-04-05", "volta": "2027-04-12"},
                {**base, "nome": "Tóquio", "pais": "Japão", "preco": 9000, "ida": "2027-04-05", "volta": "2027-04-15"},
                {**base, "nome": "Rio de Janeiro", "pais": "Brasil", "preco": 1100, "ida": "2027-04-05", "volta": "2027-04-11"},
            ]
        return [{**base, "nome": "Lisboa", "pais": "Portugal", "preco": 4400, "ida": "2027-04-01", "volta": "2027-04-15"}]

    monkeypatch.setattr(google_explore, "explorar", falso)
    cfg = {
        "origens": ["REC"], "mes": "2027-04",
        "grupos": [
            {"nome": "Europa", "dias_min": 9, "dias_max": 12, "paises": ["Portugal", "França"], "preco_maximo": 5000},
            {"nome": "BR", "dias_min": 5, "dias_max": 7, "destinos": ["Rio de Janeiro"]},
        ],
    }
    h = Historico(tmp_path / "h.json")
    promos = explorar.executar(cfg, "BRL", h)
    # Lisboa 9 dias por 4600 entra (a de 14 dias, mais barata, fica de fora); Paris tem 7 dias.
    assert [(p.rota.destino, p.oferta.preco) for p in promos] == [("Lisboa", 4600)]
    assert h.precos("REC-Rio de Janeiro_2027-04_5a7dias_google_explore") == [1100]
    # Na segunda vez, no mesmo dia, não gasta cota.
    assert not explorar.deve_rodar(cfg, h)


def test_milhas_primeira_vez_so_memoriza(monkeypatch, tmp_path):
    from agente import milhas

    itens = [{"titulo": "Europa por 40 mil milhas Smiles", "link": "a", "id": "a", "categorias": ""},
             {"titulo": "Cartão novo", "link": "b", "id": "b", "categorias": ""}]
    monkeypatch.setattr(milhas, "ler_feed", lambda url: list(itens))
    cfg = {"feeds": ["f"], "palavras": ["smiles"], "destaques": ["europa"]}
    h = Historico(tmp_path / "h.json")
    assert milhas.verificar(cfg, h) == []
    itens.append({"titulo": "Recife: promoção Smiles com 50% de bônus", "link": "c", "id": "c", "categorias": ""})
    itens.append({"titulo": "Europa barata na Smiles", "link": "d", "id": "d", "categorias": ""})
    msgs = milhas.verificar(cfg, h)
    assert len(msgs) == 2 and "⭐" in msgs[1] and "⭐" not in msgs[0]
    assert milhas.verificar(cfg, h) == []
