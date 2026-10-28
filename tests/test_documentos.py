"""Higiene do repositório: separação do Clipador, links internos, dados pessoais e sintaxe."""
import ast
import re
import subprocess

import pytest

from conftest import RAIZ

VERSIONADOS = subprocess.run(["git", "-C", str(RAIZ), "ls-files"], capture_output=True, text=True).stdout.split()
TEXTOS = [RAIZ / a for a in VERSIONADOS if a.endswith((".md", ".py", ".json")) and not a.endswith("test_documentos.py")]


@pytest.mark.parametrize("arq", TEXTOS, ids=lambda p: str(p.relative_to(RAIZ)))
def test_sem_clipador_nem_dados_pessoais(arq):
    t = arq.read_text(encoding="utf-8")
    if "tests" not in arq.relative_to(RAIZ).parts:           # os testes precisam citar o nome para conferir
        assert not re.search(r"clipador|CLIPADOR_DIR", t, re.I), "a SocialmedIA é independente do Clipador"
    assert not re.search(r"C:[\\/]+Users[\\/]|@gmail\.com|sk-[A-Za-z0-9]{20,}", t), "caminho pessoal, e-mail ou chave"


@pytest.mark.parametrize("arq", [p for p in TEXTOS if p.suffix == ".md"], ids=lambda p: str(p.relative_to(RAIZ)))
def test_links_internos_existem(arq):
    for alvo in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", arq.read_text(encoding="utf-8")):
        if alvo.startswith(("http://", "https://", "mailto:")):
            continue
        assert (arq.parent / alvo).exists(), f"link quebrado: {alvo}"


@pytest.mark.parametrize("arq", [p for p in TEXTOS if p.suffix == ".py"], ids=lambda p: str(p.relative_to(RAIZ)))
def test_python_compila_sem_bom(arq):
    dados = arq.read_bytes()
    assert not dados.startswith(b"\xef\xbb\xbf")
    ast.parse(dados.decode("utf-8"))


def test_skill_md_tem_frontmatter():
    for skill in (RAIZ / "SKILL.md", RAIZ / "effectcraft" / "SKILL.md"):
        cab = skill.read_text(encoding="utf-8").split("---")[1]
        assert re.search(r"^name: \S+", cab, re.M) and re.search(r"^description: .{40,}", cab, re.M)


# ---------------------------------------------------------------- regra: nada de terceiros no Git
import verificar_terceiros as vt   # noqa: E402


def test_repositorio_sem_conteudo_de_terceiros():
    achados = vt.verificar(VERSIONADOS, lambda a: (RAIZ / a).read_text(encoding="utf-8"))
    assert achados == [], "\n".join(achados)


# os exemplos proibidos são montados por partes para este arquivo não cair na própria regra
PROIBIDOS = [
    ("doc.md", "veja " + "instagram" + ".com/p/abc"), ("doc.md", "o Reel de " + "@" + "umaconta bombou"),
    ("doc.md", "falar com alguem" + "@" + "empresa.com.br"), ("doc.md", "C:" + "\\Users\\fulano\\x"),
    ("cfg.json", '{"k": "' + "sk-" + "ant-" + "a" * 24 + '"}'), ("doc.md", "youtube" + ".com/shorts/xyz"),
    ("doc.md", "a Marca Inventada fez isso"),
]


@pytest.mark.parametrize("arquivo,texto", PROIBIDOS)
def test_verificador_barra(arquivo, texto):
    assert vt.verificar_texto(arquivo, texto, ["Marca Inventada"])


@pytest.mark.parametrize("arquivo,texto", [
    ("x.py", "@pytest.mark.lento\ndef f(): pass"),("doc.md", "identidade socialmedia@localhost"),
    ("doc.md", "Co-Authored-By: x <noreply@anthropic.com>"), ("doc.md", "o @perfil da marca"),
    ("doc.md", "política oficial em https://help.example.com/regras"),
])
def test_verificador_deixa_passar(arquivo, texto):
    assert vt.verificar_texto(arquivo, texto, ["Marca Inventada"]) == []


@pytest.mark.parametrize("caminho", ["terceiros/x.md", "projetos/a/b.json", "foto.png", "v.mp4", "_versoes/a.zip"])
def test_verificador_barra_caminhos_e_midia(caminho):
    assert vt.verificar([caminho], lambda a: "") != []
