"""Ponte SocialmedIA -> editonny: decisões puras (EDL, título dito, project.json) e a edição real (lenta)."""
import json
import os
import shutil
from pathlib import Path

import pytest

import editar_reel as er
import socialmedia_engine as sme
from conftest import requer_ffmpeg


def _w(texto, ini, fim):
    return {"text": texto, "start": ini, "end": fim}


FALA = [_w("Olá", 0.70, 0.95), _w("pessoal", 1.00, 1.40),                       # pausa curta (0,40 s)
        _w("hoje", 1.80, 2.10), _w("tem", 2.15, 2.30),                           # pausa longa (1,20 s)
        _w("oferta", 3.50, 3.90), _w("boa", 3.95, 4.20)]


def test_edl_fala_continua_corta_so_entre_paragrafos_e_nao_picota(monkeypatch):
    monkeypatch.setitem(sme.REEL_TYPES["fala_continua"], "max_cuts_per_minute", 1000)   # só a regra da pausa
    edl = er.montar_edl(FALA, "fala_continua", "v.mp4", 10.0)
    r = edl["ranges"]
    assert len(r) == 2 and all(x["dry"] is False for x in r)                     # só a pausa de 1,2 s corta
    assert r[0]["start"] == pytest.approx(0.70 - er.PAD_INICIO) and r[0]["quote"].startswith("Olá pessoal hoje")
    assert r[0]["end"] < r[1]["start"]                                           # trechos nunca se encostam
    assert edl["output"] == {"width": 1080, "height": 1920, "fps": 30} and edl["sources"] == {"C1": "v.mp4"}


def test_edl_montagem_corta_pausas_curtas_e_deixa_o_waveform_apertar():
    r = er.montar_edl(FALA, "montagem_criador", "v.mp4", 10.0)["ranges"]
    assert len(r) == 3 and all(x["dry"] is True for x in r)                      # pausas >= 0,35 s cortam


def test_edl_sem_fala_usa_o_video_inteiro():
    for tipo, palavras in (("produto_sem_fala", FALA), ("fala_continua", [])):
        r = er.montar_edl(palavras, tipo, "v.mp4", 8.0)["ranges"]
        assert r == [{"id": "r1", "source": "C1", "start": 0.0, "end": 8.0, "dry": False, "quote": "sem fala"}]


def test_edl_primeira_palavra_cai_dentro_do_gancho():
    r = er.montar_edl(FALA, "fala_continua", "v.mp4", 10.0)["ranges"]
    assert FALA[0]["start"] - r[0]["start"] <= 0.40                               # 1ª palavra até 0,40 s


@pytest.mark.parametrize("titulo,esperado", [
    ("Hoje tem oferta", 1.80), ("HOJE, tem OFERTA!", 1.80), ("olá pessoal", 0.70),
    ("oferta imperdível", None), ("tem hoje", None), ("", None),
])
def test_titulo_so_quando_foi_dito_em_sequencia(titulo, esperado):
    assert er.titulo_dito(titulo, FALA) == esperado


def test_titulo_ignora_acento():
    assert er.titulo_dito("ola pessoal", FALA) == 0.70


def test_projeto_editonny_mantem_caminhos_e_aplica_o_plano():
    plano = sme.build_editing_plan("saude", "reel", "T")
    cfg = {"skill": "/motor", "edit": "../edit", "title": "x", "style": "night", "blocks": [], "scenes": ["s"]}
    novo = er.projeto_editonny(cfg, plano)
    assert novo["skill"] == "/motor" and novo["edit"] == "../edit" and novo["scenes"] == ["s"]
    assert novo["style"] == "paper" and novo["captions"]["maxWords"] == 3 and novo["blocks"] == plano["editonny_project_json"]["blocks"]


def test_estado_refazer_etapa_invalida_as_seguintes(tmp_path):
    e = er.Estado(tmp_path)
    for etapa in er.ETAPAS:
        e.marcar(etapa, "k")
    e.marcar("cortar", "k2")
    assert set(er.Estado(tmp_path).d) == {"preparar", "transcrever", "cortar"}


# ---------------------------------------------------------------- edição real de ponta a ponta
TEM_EDITONNY = er.ENGINE.joinpath(".venv").is_dir() and bool(shutil.which("npx"))
AMOSTRA = os.environ.get("SOCIALMEDIA_AMOSTRA_FALA")          # vídeo local com fala (não vai para o Git)


@pytest.mark.lento
@requer_ffmpeg
@pytest.mark.skipif(not (TEM_EDITONNY and AMOSTRA and Path(AMOSTRA or "").is_file()),
                    reason="precisa do editonny instalado e de SOCIALMEDIA_AMOSTRA_FALA apontando para um vídeo com fala")
def test_edicao_real_ate_o_rascunho_verificado(tmp_path, monkeypatch):
    monkeypatch.setenv("SOCIALMEDIA_DIR", str(tmp_path))
    res = er.editar(Path(AMOSTRA), "saude", "", modelo="small", qualidade_hf="draft", ocr=False)
    assert Path(res["rascunho"]).is_file() and res["verificar"]["valido"], res["verificar"]["itens"]
    assert res["etapas"]["cortar"]["playbook_checks"]["no_auto_dry_chopping_in_fala_continua"] is True
    assert json.loads((tmp_path / "projetos").joinpath(next(os.walk(tmp_path / "projetos"))[1][0],
                                                       "socialmedia_estado.json").read_text())["render"]


def test_edl_fala_continua_junta_pelas_menores_pausas_ate_o_limite_de_cortes():
    # 8 frases de 1 s com pausas de 0,7 s (todas >= 0,65): sem limite seriam 7 cortes em ~14 s (~30/min)
    falas, t = [], 0.5
    for i in range(8):
        falas.append(_w(f"p{i}", t, t + 1.0))
        t += 1.0 + (0.7 if i != 3 else 2.0)                    # a pausa depois da 4ª frase é a maior
    r = er.montar_edl(falas, "fala_continua", "v.mp4", 30.0)["ranges"]
    fala = sum(x["end"] - x["start"] for x in r)
    assert (len(r) - 1) / (fala / 60) <= sme.REEL_TYPES["fala_continua"]["max_cuts_per_minute"]
    assert len(r) < 8 and any(x["quote"].endswith("p3") for x in r[:-1])   # a maior pausa continua sendo corte


# ---------------------------------------------------------------- motion (EffectCraft) só com palavras ditas
def _falas(texto, t0=0.1, passo=0.35):
    out, t = [], t0
    for tok in texto.split():
        out.append(_w(tok, round(t, 2), round(t + 0.3, 2)))
        t += passo + (0.8 if tok[-1] in ".?!" else 0)
    return out


ROTEIRO = _falas("Você tem uma loja que vende muito, mas sem controle. Isso custa caro. "
                 "Percebe o problema? Então organize enquanto ainda dá tempo de crescer.")


def test_motion_so_usa_sequencias_faladas_e_nao_termina_em_ligacao():
    from ec_grafico import LIGACAO
    itens = er.planejar_motion(ROTEIRO, [], 40.0)
    falado = " ".join(er._normal(" ".join(w["text"] for w in ROTEIRO)))
    for it in (i for i in itens if i.get("texto")):
        assert " ".join(er._normal(it["texto"])) in falado                 # nada que não foi dito
        assert er._normal(it["texto"])[-1] not in LIGACAO
        assert it["duracao"] >= 1.8
    textos = [i["texto"] for i in itens if i.get("texto")]
    assert textos[0] == "VOCÊ TEM UMA LOJA" and "PERCEBE O PROBLEMA?" in textos
    assert textos[-1] == "AINDA DÁ TEMPO DE CRESCER"


def test_motion_titulo_dado_so_entra_se_dito():
    assert er.planejar_motion(ROTEIRO, [], 40.0, "isso custa caro")[0]["texto"] == "ISSO CUSTA CARO"
    assert er.planejar_motion(ROTEIRO, [], 40.0, "frase inventada")[0]["texto"] == "VOCÊ TEM UMA LOJA"


def test_motion_sem_sobreposicao_e_flash_nas_emendas():
    itens = er.planejar_motion(ROTEIRO, [5.0, 12.5], 40.0)
    textos = [i for i in itens if i["receita"] != "flash"]
    for a, b in zip(textos, textos[1:]):
        assert a["inicio"] + a["duracao"] <= b["inicio"]
    assert [i["inicio"] for i in itens if i["receita"] == "flash"] == [4.8, 12.3]


def test_motion_numero_falado_vira_contador():
    itens = er.planejar_motion(_falas("Olha só isso. Foram 250 clientes atendidos. Obrigado."), [], 20.0)
    assert any(i["receita"] == "contador" and i["ate"] == 250 for i in itens)


def test_corrigir_palavras_troca_sequencia_e_mantem_tempo_e_pontuacao():
    ws = _falas("evita por meio de perder, ok.")
    out = er.corrigir_palavras(ws, {"por meio de": "por medo de"})
    assert [w["text"] for w in out] == ["evita", "por", "medo", "de", "perder,", "ok."]
    assert [w["start"] for w in out] == [w["start"] for w in ws]
    assert [w["text"] for w in ws][2] == "meio"                            # não altera a entrada


def test_quebra_de_linha_nao_deixa_ligacao_no_fim():
    import ec_grafico as ec
    assert ec.quebrar("AINDA TEMOS O QUE PRESERVAR") == "AINDA TEMOS\rO QUE PRESERVAR"
    assert ec.quebrar("CURTO") == "CURTO"
