"""scripts/qualidade.py (portão do vídeo exportado) e scripts/receber_mp4.py (ingestão sem perder arquivos)."""
import json
import os
import subprocess
import sys

import pytest

import qualidade
from conftest import RAIZ, requer_ffmpeg, video_teste

pytestmark = [pytest.mark.lento, requer_ffmpeg]


def _normalizado(tmp_path, nome):
    pre = video_teste(tmp_path / "pre.mp4", d=4)
    saida = tmp_path / nome
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-c:v", "copy", "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", str(saida)], check=True)
    m = qualidade.medir(saida)
    if abs(m["lufs"] + 14) > 0.5:            # 1 passada do loudnorm pode errar: ajusta o ganho que faltou
        corr = tmp_path / ("c_" + nome)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(saida), "-c:v", "copy", "-af",
                        f"volume={-14 - m['lufs']:.2f}dB", "-c:a", "aac", str(corr)], check=True)
        os.replace(corr, saida)
    return saida


def test_video_dentro_das_metas_passa(tmp_path):
    r = qualidade.verificar(_normalizado(tmp_path, "RASCUNHO_ok.mp4"))
    assert r["valido"], r["itens"]


def test_video_horizontal_e_alto_reprova(tmp_path):
    r = qualidade.verificar(video_teste(tmp_path / "x.mp4", s="1920x1080", r=25))
    regras = {i["regra"]: i["nivel"] for i in r["itens"]}
    assert not r["valido"] and regras["resolucao"] == "erro" and regras["fps"] == "aviso" and regras["nome"] == "aviso"


def test_sem_audio_reprova(tmp_path):
    v = tmp_path / "RASCUNHO_mudo.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=1",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(v)], check=True)
    assert any(i["regra"] == "audio" and i["nivel"] == "erro" for i in qualidade.verificar(v)["itens"])


def test_arquivo_inexistente(tmp_path):
    assert qualidade.verificar(tmp_path / "nada.mp4")["valido"] is False


# ---------------------------------------------------------------- ingestão
def _receber(pasta, *extra):
    env = {**os.environ, "SOCIALMEDIA_DIR": str(pasta)}
    return subprocess.run([sys.executable, "-I", str(RAIZ / "scripts" / "receber_mp4.py"), "--niche", "varejo",
                           "--title", "T", *extra], capture_output=True, text=True, encoding="utf-8", env=env, cwd=pasta)


@pytest.fixture
def pasta(tmp_path):
    (tmp_path / "entrada_mp4").mkdir()
    video_teste(tmp_path / "entrada_mp4" / "base.mp4", d=1)
    assets = tmp_path / "projetos" / "socialmedia_base" / "proj" / "assets"
    assets.mkdir(parents=True)
    (assets / "antiga.png").write_bytes(b"imagem-antiga")
    return tmp_path


def test_caminho_errado_nao_mexe_nas_imagens(pasta):
    r = _receber(pasta, "--images", str(pasta / "nao_existe.png"))
    assert r.returncode != 0
    assert (pasta / "projetos/socialmedia_base/proj/assets/antiga.png").is_file()


def test_imagem_antiga_vai_para_removidas_nunca_apagada(pasta):
    (pasta / "nova.png").write_bytes(b"imagem-nova")
    r = _receber(pasta, "--images", str(pasta / "nova.png"))
    assert r.returncode == 0, r.stderr
    proj = pasta / "projetos" / "socialmedia_base"
    assert (proj / "proj/assets/nova.png").is_file()
    assert (proj / "_removidas/antiga.png").read_bytes() == b"imagem-antiga"
    plano = json.loads((proj / "socialmedia_plan.json").read_text(encoding="utf-8"))
    assert "legenda_empresa" in plano["plano_socialmedia"]
