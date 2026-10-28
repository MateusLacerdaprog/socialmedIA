#!/usr/bin/env python3
"""Regra do repositório: NADA de terceiros sobe para o Git (o repositório é público).

Barra: mídia/binários, pastas locais (terceiros/, _versoes/, memes_cortados/, entrada_mp4/, projetos/), links para
posts/vídeos/perfis, @perfis em textos, e-mails que não sejam genéricos, caminhos pessoais, chaves de API e os nomes
da lista local `terceiros/nomes_bloqueados.txt` (que também fica fora do Git).

    python scripts/verificar_terceiros.py              # todos os arquivos versionados
    python scripts/verificar_terceiros.py --staged     # só o que está no índice (o hook pre-commit usa este)
    python scripts/verificar_terceiros.py --instalar-hook

Material de terceiros mora em `terceiros/` (local). O que pode subir: código próprio, regras e conclusões com números
agregados sem identificar contas, e links para políticas/documentação oficial como fonte.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import List

RAIZ = Path(__file__).resolve().parent.parent
LISTA_LOCAL = RAIZ / "terceiros" / "nomes_bloqueados.txt"

PASTAS_PROIBIDAS = ("terceiros/", "_versoes/", "memes_cortados/", "entrada_mp4/", "projetos/")
EXTENSOES_PROIBIDAS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg",
                       ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".pdf", ".zip", ".7z",
                       ".rar", ".bundle", ".ecproj", ".pyc"}
TEXTO = {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".js", ".html", ".css", ".toml", ".cfg", ".ini", ".csv"}
PADROES = [
    (re.compile(r"(instagram\.com|tiktok\.com|youtu\.be|youtube\.com/(?:watch|shorts|@|channel|c/))", re.I),
     "link para post/vídeo/perfil de terceiro"),
    (re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+", re.I), "caminho pessoal"),
    (re.compile(r"\b(?:sk-(?:ant-)?[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,}|ghp_[A-Za-z0-9]{30,})"), "chave de API"),
]
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}\b")
EMAILS_OK = re.compile(r"@(localhost|anthropic\.com|example\.(com|org))$", re.I)
PERFIL = re.compile(r"(?<![\w.`/])@([A-Za-z0-9_.]{3,30})\b")
PERFIS_OK = {"perfil", "handle", "conta", "marca", "seuperfil", "localhost", "pytest", "keyframes", "media",
             "import", "font-face", "supports", "property"}


def _lista_local() -> List[str]:
    try:
        return [n.strip() for n in LISTA_LOCAL.read_text(encoding="utf-8").splitlines() if len(n.strip()) >= 4]
    except OSError:
        return []


def verificar_texto(caminho: str, texto: str, nomes: List[str]) -> List[str]:
    achados = []
    eh_codigo = caminho.endswith((".py", ".js"))
    for n, linha in enumerate(texto.splitlines(), 1):
        for padrao, motivo in PADROES:
            if padrao.search(linha):
                achados.append(f"{caminho}:{n}: {motivo}")
        for m in EMAIL.finditer(linha):
            if not EMAILS_OK.search(m.group(0)):
                achados.append(f"{caminho}:{n}: e-mail ({m.group(0).split('@')[1]})")
        if not eh_codigo:                                       # em código, @ é decorador
            for m in PERFIL.finditer(linha):
                if m.group(1).lower() not in PERFIS_OK and not EMAIL.search(linha[max(0, m.start() - 40):m.end()]):
                    achados.append(f"{caminho}:{n}: @perfil")
        baixa = linha.lower()
        for nome in nomes:
            if nome.lower() in baixa:
                achados.append(f"{caminho}:{n}: nome da lista local de terceiros")
                break
    return achados


def verificar(arquivos: List[str], ler) -> List[str]:
    nomes, achados = _lista_local(), []
    for arq in arquivos:
        a = arq.replace("\\", "/")
        if a == "scripts/verificar_terceiros.py":
            continue
        if a.startswith(PASTAS_PROIBIDAS):
            achados.append(f"{a}: pasta local (não versionar)")
            continue
        if Path(a).suffix.lower() in EXTENSOES_PROIBIDAS:
            achados.append(f"{a}: mídia/binário")
            continue
        if Path(a).suffix.lower() in TEXTO:
            texto = ler(a)
            if texto is not None:
                achados += verificar_texto(a, texto, nomes)
    return achados


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(RAIZ), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace").stdout


def main() -> int:
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace")
    if "--instalar-hook" in sys.argv:
        hook = RAIZ / ".git" / "hooks" / "pre-commit"
        hook.write_text('#!/bin/sh\npython -I scripts/verificar_terceiros.py --staged || {\n'
                        '  echo "commit bloqueado: conteúdo de terceiros (ver acima)"; exit 1; }\n', encoding="utf-8")
        print(f"hook instalado em {hook}")
        return 0
    if "--staged" in sys.argv:
        arquivos = [l for l in _git("diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines() if l]
        def ler(a):
            return _git("show", f":{a}")
    else:
        arquivos = [l for l in _git("ls-files").splitlines() if l]
        def ler(a):
            try:
                return (RAIZ / a).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                return None
    achados = verificar(arquivos, ler)
    for a in achados:
        print(a)
    print(f"{len(achados)} problema(s) em {len(arquivos)} arquivo(s)" if achados else f"ok: {len(arquivos)} arquivo(s) sem conteúdo de terceiros")
    return 1 if achados else 0


if __name__ == "__main__":
    sys.exit(main())
