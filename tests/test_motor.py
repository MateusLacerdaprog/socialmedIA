"""Contratos do socialmedia_engine.py: plano por nicho, legenda, memes e auditorias."""
import json
from pathlib import Path

import pytest

import socialmedia_engine as sme
from conftest import cli

GOLDEN = Path(__file__).parent / "golden"


def _plano_estavel(n):
    plano = sme.build_editing_plan(n, "desafio_orcamento", "Teste")
    plano["editonny_project_json"].pop("skill")          # caminho da máquina
    return json.loads(json.dumps(plano, ensure_ascii=False))


@pytest.mark.parametrize("nicho", sorted(sme.NICHE_PROFILES))
def test_plano_igual_ao_golden(nicho):
    """Regressão: o plano de cada nicho só muda de propósito (regere o golden e revise o diff)."""
    esperado = json.loads((GOLDEN / f"plan_{nicho}.json").read_text(encoding="utf-8"))
    assert _plano_estavel(nicho) == esperado


@pytest.mark.parametrize("nicho", sorted(sme.NICHE_PROFILES))
def test_plano_sem_clipador(nicho):
    assert "clipador" not in json.dumps(sme.build_editing_plan(nicho, "x", "Teste")).lower()


@pytest.mark.parametrize("variante,esperado", [
    ("Loja Material Construcao", "material_construcao"), ("loja-material-construcao", "material_construcao"),
    (" Clinica ", "saude"), ("SUPERMERCADO", "varejo"), ("gastronomia", "gastronomia")])
def test_nicho_normalizado_igual_em_todo_o_motor(variante, esperado):
    assert sme.canonical_niche(variante) == esperado
    assert sme.resolve_niche(variante) is sme.NICHE_PROFILES[esperado]


def test_nicho_desconhecido_explica_opcoes():
    with pytest.raises(ValueError, match="Opções válidas"):
        sme.resolve_niche("astronautica")


def test_personagem_ia_exige_gemini():
    with pytest.raises(ValueError, match="Gemini"):
        sme.build_editing_plan("varejo", "x", "T", tipo="personagem_ia")
    assert sme.build_editing_plan("varejo", "x", "T", tipo="personagem_ia", plano_gemini="pro")["reel_type"]["tipo"] == "personagem_ia"


def test_limite_de_imagens():
    ev = [{"start": i, "end": i + 1, "file": f"{i}.jpg"} for i in range(3)]
    with pytest.raises(ValueError, match="Excesso de imagens"):
        sme.build_editing_plan("saude", "x", "T", evidence_moments=ev)


# ---------------------------------------------------------------- legenda do post
def test_legenda_longa_reprovada_sem_cortar_o_texto():
    gancho = "x" * 200
    r = sme.generate_post_caption("varejo", gancho, ["a"], cta_keyword="PROMO", hashtags=["#a"])
    assert not r["valid"] and r["preview_chars"] == 200 and not r["preview_under_125"]
    assert r["caption_text"].startswith(gancho)                 # o texto do usuário não foi mexido


def test_legenda_declara_padroes_do_nicho():
    r = sme.generate_post_caption("varejo", "Gancho", ["a"])
    assert r["valid"] and set(r["defaults_used"]) == {"cta_keyword", "hashtags"}
    r = sme.generate_post_caption("varejo", "Gancho", ["a"], cta_keyword="LISTA", hashtags=["#x"])
    assert r["defaults_used"] == []


def test_legenda_mais_de_5_hashtags_reprovada():
    r = sme.generate_post_caption("varejo", "G", ["a"], cta_keyword="K", hashtags=[f"#t{i}" for i in range(6)])
    assert not r["valid"] and r["hashtag_count"] == 6


def test_cli_legenda_codigo_de_saida():
    assert cli("caption", "--niche", "varejo", "--hook", "Ok", "--bullets", "a")[0] == 0
    assert cli("caption", "--niche", "varejo", "--hook", "y" * 130, "--bullets", "a")[0] == 1


# ---------------------------------------------------------------- memes
# Catálogo SINTÉTICO: o real é de terceiros e fica só na máquina (terceiros/memes.json).
CATALOGO_TESTE = {
    "versao": 1,
    "catalogo": {
        "a_reacao_surpresa.mp4": {"tier": 1, "intents": ["surpresa"], "chroma_green": True, "trim_s": [0.5, 2.2],
                                  "crop": "1920:1080:0:0", "lufs": -36.0, "gain_db_to_minus16": 20.0},
        "b_reacao_fome.mp4": {"tier": 1, "intents": ["fome"], "chroma_green": False, "trim_s": [0.0, 2.1],
                              "crop": "1440:1080:240:0", "lufs": -24.9, "gain_db_to_minus16": 8.9},
    },
    "bloqueados_tier3": ["c_palavrao.mp4"],
    "remix": {"a_reacao_surpresa.mp4": "pessoa da equipe com cara de surpresa"},
}


@pytest.fixture
def catalogo(monkeypatch, tmp_path):
    arq = tmp_path / "memes.json"
    arq.write_text(json.dumps(CATALOGO_TESTE), encoding="utf-8")
    monkeypatch.setenv("SOCIALMEDIA_MEMES_JSON", str(arq))
    return CATALOGO_TESTE


def test_meme_nunca_em_saude(catalogo):
    for n in ("saude", "Clinica", "odontologia"):
        assert sme.recommend_meme_insertion(n, "surpresa", "pessoal_sem_receita")["allowed"] is False


def test_meme_conta_empresa_so_remix_encenado(catalogo):
    r = sme.recommend_meme_insertion("varejo", "surpresa", "empresa")
    assert r["allowed"] is False and r["remix_do_formato"]["reacao_encenada"] == "pessoa da equipe com cara de surpresa"


def test_meme_seleciona_por_intencao_com_modo_e_ganho(catalogo, monkeypatch, tmp_path):
    monkeypatch.setenv("SOCIALMEDIA_DIR", str(tmp_path))
    r = sme.recommend_meme_insertion("varejo", "fome", "pessoal_sem_receita")
    assert r["allowed"] and Path(r["selected_file"]) == tmp_path / "memes_cortados" / "b_reacao_fome.mp4"
    assert r["insertion_mode"] == "PIP_CARD_OR_EMPILHADO" and "crop=1440:1080:240:0" in r["ffmpeg_snippet"]
    assert sme.recommend_meme_insertion("varejo", "surpresa", "pessoal_sem_receita")["insertion_mode"] == "CHROMA_OVERLAY"


def test_meme_sem_intencao_no_catalogo_nao_inventa(catalogo):
    r = sme.recommend_meme_insertion("varejo", "xyz", "pessoal_sem_receita")
    assert r["allowed"] is False and r["intencoes_disponiveis"] == ["fome", "surpresa"]
    with pytest.raises(ValueError, match="vazia"):
        sme.recommend_meme_insertion("varejo", "  ", "pessoal_sem_receita")


def test_meme_tier3_nunca_selecionado(catalogo, monkeypatch, tmp_path):
    cat = json.loads(json.dumps(CATALOGO_TESTE))
    cat["catalogo"]["a_reacao_surpresa.mp4"]["intents"].append("palavrao")
    cat["catalogo"]["c_palavrao.mp4"] = cat["catalogo"].pop("b_reacao_fome.mp4")
    cat["catalogo"]["c_palavrao.mp4"]["intents"] = ["palavrao"]
    arq = tmp_path / "m2.json"
    arq.write_text(json.dumps(cat), encoding="utf-8")
    monkeypatch.setenv("SOCIALMEDIA_MEMES_JSON", str(arq))
    with pytest.raises(sme.PresetInvalido, match="tier 3"):          # bloqueado no catálogo é recusado ao carregar
        sme.recommend_meme_insertion("varejo", "palavrao", "pessoal_sem_receita")


def test_meme_sem_catalogo_local(monkeypatch, tmp_path):
    monkeypatch.setenv("SOCIALMEDIA_MEMES_JSON", str(tmp_path / "nao_existe.json"))
    r = sme.recommend_meme_insertion("varejo", "surpresa", "pessoal_sem_receita")
    assert r["allowed"] is False and "ausente" in r["reason"]
    r = sme.recommend_meme_insertion("varejo", "surpresa", "empresa")      # empresa ainda recebe a receita encenada
    assert r["remix_do_formato"]["reacao_encenada"] == sme.REMIX_GENERICO


# ---------------------------------------------------------------- auditorias
def _edl(tmp_path, ranges, **extra):
    p = tmp_path / "edl.json"
    p.write_text(json.dumps({"ranges": ranges, "jcut": {"lead_frames": 4},
                             "output": {"width": 1080, "height": 1920}, **extra}), encoding="utf-8")
    return p


def test_auditoria_edl_fala_continua_boa(tmp_path):
    ranges = [{"id": i, "start": i * 8 + 0.2, "end": i * 8 + 6.2, "quote": "fala"} for i in range(6)]
    r = sme.audit_edl(_edl(tmp_path, ranges), "fala_continua")
    assert r["score_pct"] == 100.0, r["playbook_checks"]


def test_auditoria_edl_fala_continua_picotada(tmp_path):
    ranges = [{"id": i, "start": i * 0.5 + 0.2, "end": i * 0.5 + 0.5, "quote": "fala", "dry": True} for i in range(30)]
    r = sme.audit_edl(_edl(tmp_path, ranges), "fala_continua")
    c = r["playbook_checks"]
    assert not c["no_auto_dry_chopping_in_fala_continua"] and not c["cuts_per_minute_within_limit"]


def _projeto(raiz, nome, imagens=(), blocks=None, scenes=None):
    proj = raiz / nome / "proj"
    (proj / "assets").mkdir(parents=True)
    for nome_img, conteudo in imagens:
        (proj / "assets" / nome_img).write_bytes(conteudo)
    (proj / "project.json").write_text(json.dumps({"blocks": blocks or [], "scenes": scenes or []}), encoding="utf-8")
    return proj


def test_auditoria_projeto_detecta_imagem_reutilizada(tmp_path):
    _projeto(tmp_path, "antigo", [("foto.jpg", b"mesma-imagem")])
    atual = _projeto(tmp_path, "novo", [("outra.jpg", b"mesma-imagem")])
    r = sme.audit_project(atual)
    assert r["passed_all"] is False and r["reused_images_detected"]


def test_auditoria_projeto_ignora_removidas(tmp_path):
    antigo = _projeto(tmp_path, "antigo")
    (antigo.parent / "_removidas").mkdir()
    (antigo.parent / "_removidas" / "x.jpg").write_bytes(b"img")
    atual = _projeto(tmp_path, "novo", [("y.jpg", b"img")])
    assert not sme.audit_project(atual)["reused_images_detected"]


def test_contrato_editonny_evidencia_com_zoom_e_transicoes():
    """build.py do editonny exige zooms[] com "at" (e lê "scale"); cada imagem tem cena de entrada e de saída."""
    ev = [{"start": 5.0, "end": 8.0, "file": "assets/a.jpg"}, {"start": 20.0, "end": 24.0, "file": "assets/b.jpg"}]
    proj = sme.build_editing_plan("saude", "x", "T", evidence_moments=ev)["editonny_project_json"]
    blocos = [b for b in proj["blocks"] if b["scene"] == "evidence"]
    assert len(blocos) == 2
    for b in blocos:
        z = b["zooms"][0]
        assert {"at", "end", "scale"} <= set(z) and "zoom" not in z and "start" not in z
        assert b["start"] - 0.35 <= z["at"] < b["end"] - 0.1                 # mesma faixa que o build.py aceita
    ids = [s["sceneId"] for s in proj["scenes"]]
    assert ids.count("transition-zoom") == 2 and ids.count("transition-glow") == 2


def test_cache_de_hash_evita_reler_imagens(tmp_path, monkeypatch):
    _projeto(tmp_path, "antigo", [(f"f{i}.jpg", bytes([i]) * 100) for i in range(5)])
    atual = _projeto(tmp_path, "novo", [("n.jpg", b"nova")])
    chamadas = []
    original = sme._sha256_file
    monkeypatch.setattr(sme, "_sha256_file", lambda p: chamadas.append(p) or original(p))
    sme.audit_project(atual)
    primeira = len(chamadas)
    chamadas.clear()
    r = sme.audit_project(atual)
    assert primeira == 6 and len(chamadas) == 1          # só a imagem do projeto atual é relida
    assert not r["reused_images_detected"]


def test_cache_de_hash_percebe_imagem_alterada(tmp_path):
    antigo = _projeto(tmp_path, "antigo", [("f.jpg", b"original")])
    atual = _projeto(tmp_path, "novo", [("n.jpg", b"igual-depois")])
    sme.audit_project(atual)
    (antigo / "assets" / "f.jpg").write_bytes(b"igual-depois")        # muda tamanho/mtime
    assert sme.audit_project(atual)["reused_images_detected"]


# ---------------------------------------------------------------- presets
def test_presets_atuais_validos():
    sme._validar_nichos(sme._carregar_preset("nichos.json"))
    sme._validar_memes(json.loads(json.dumps(CATALOGO_TESTE)))


@pytest.mark.parametrize("estraga,msg", [
    (lambda d: d["perfis"]["varejo"].pop("palette"), "sem"),
    (lambda d: d["perfis"]["varejo"].__setitem__("editonny_style", "neon"), "editonny_style"),
    (lambda d: d["perfis"]["varejo"]["palette"].__setitem__("accent_primary", "amarelo"), "#RRGGBB"),
    (lambda d: d["apelidos"].__setitem__("padaria", "panificacao"), "inexistente"),
    (lambda d: d["tipo_padrao"].__setitem__("varejo", "longo"), "tipo_padrao"),
])
def test_preset_de_nicho_estragado_falha_com_mensagem(estraga, msg):
    d = sme._carregar_preset("nichos.json")
    estraga(d)
    with pytest.raises(sme.PresetInvalido, match=msg):
        sme._validar_nichos(d)


def test_preset_de_meme_bloqueado_no_catalogo_falha():
    d = json.loads(json.dumps(CATALOGO_TESTE))
    d["bloqueados_tier3"].append("a_reacao_surpresa.mp4")
    with pytest.raises(sme.PresetInvalido, match="tier 3"):
        sme._validar_memes(d)
