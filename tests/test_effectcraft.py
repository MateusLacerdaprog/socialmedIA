"""effectcraft/ec_grafico.py: validação e JSX sem render; um render real (lento) se o EffectCraft existir."""
import argparse
import json
import os
import subprocess

import pytest

import ec_grafico as ec
from conftest import requer_ffmpeg


def args(**kw):
    base = dict(receita="titulo", texto="TESTE", duracao=2.5, x=540, y=230, cor="#FFDE00", tamanho=110, raio=150,
                animacao="typewriter", de=0, ate=100, sufixo="", saida=None)
    base.update(kw)
    return argparse.Namespace(**base)


@pytest.mark.parametrize("kw,msg", [
    (dict(receita="titulo", texto=""), "precisa de --texto"),
    (dict(receita="texto", texto="ok", animacao="voar"), "--animacao"),
    (dict(receita="xyz"), "receita desconhecida"),
    (dict(texto="x" * 61), "60 caracteres"),
    (dict(receita="flash", duracao=2.0), "flash"),
    (dict(cor="amarelo"), "cor inválida"),
    (dict(y=5000), "fora da tela"),
    (dict(duracao=0.1), "duração"),
])
def test_validacao_recusa(kw, msg):
    with pytest.raises(ValueError, match=msg):
        ec.validar(args(**kw))


@pytest.mark.parametrize("receita", sorted(ec.RECEITAS))
def test_jsx_de_cada_receita(receita):
    a = args(receita=receita, duracao=0.5 if receita == "flash" else 2.5)
    ec.validar(a)
    js = ec.jsx(a)
    assert 'addComp("G", 1080, 1920' in js and js.rstrip().endswith('writeLn("ok");')


def test_circulo_posiciona_pela_camada_nao_pelo_grupo():
    js = ec.jsx(args(receita="circulo", x=700, y=800))
    assert 'L.property("Transform")' in js and "tr.property(\"Position\").setValue([700, 800])" in js


def test_texto_com_aspas_vira_string_js_segura():
    js = ec.jsx(args(texto='DIZ "OI" \\ TCHAU'))
    assert json.dumps('DIZ "OI" \\ TCHAU', ensure_ascii=False) in js


def test_contador_expressao_escapada_uma_vez():
    js = ec.jsx(args(receita="contador", sufixo=' "MIL"'))
    linha = next(x for x in js.splitlines() if ".expression =" in x)
    expr = json.loads(linha.split("=", 1)[1].strip().rstrip(";"))      # tem de ser um literal JSON válido
    assert expr.startswith("Math.round(linear(time") and expr.endswith(json.dumps(' "MIL"'))


def test_sem_modo_projeto_do_clipador():
    r = subprocess.run(["python", "-I", ec.__file__, "gerar", "--receita", "circulo", "--projeto", "x"],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "unrecognized arguments" in r.stderr


@pytest.mark.lento
@requer_ffmpeg
@pytest.mark.skipif(not os.path.isfile(ec.CLI), reason="EffectCraft não instalado")
def test_render_real_tem_alfa_e_duracao(tmp_path):
    saida = tmp_path / "g.webm"
    a = args(receita="circulo", duracao=1.0)
    ec.validar(a)
    ec.gerar(a, str(saida))
    ec.conferir(str(saida), 1.0)                                        # 1080x1920, alpha_mode=1, 1,0 s
