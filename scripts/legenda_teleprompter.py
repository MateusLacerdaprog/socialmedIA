#!/usr/bin/env python3
"""Legenda "teleprompter": cartões curtos da fala com uma caixa colorida atrás da palavra que está sendo dita.

Gera um .ass (libass/FFmpeg) a partir das palavras com tempo (transcrição do corte). As posições das palavras são
medidas com a própria fonte (Pillow) para a caixa cair exatamente atrás de cada palavra. Entra na compressão final
de 1080x1920 (`editar_reel.aplicar_motion`), sem passada extra.

    python legenda_teleprompter.py palavras.json saida.ass --cor "#6B4C9A"
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

W, H = 1080, 1920
FONTE_ARQ = Path(os.environ.get("SOCIALMEDIA_FONTE_LEGENDA") or r"C:\Windows\Fonts\ariblk.ttf")
FONTE_NOME = "Arial Black"
TAM = 84                     # altura de linha do libass (letra ~60 px, igual à legenda do editonny)
Y = 1400                     # centro da linha (faixa segura 1290–1420; nada abaixo de 1530)
MAX_PALAVRAS, MAX_CARACTERES = 3, 18
PAUSA_QUEBRA = 0.6
FOLGA_FIM = 0.12             # o cartão some 0,12 s depois da última palavra (nunca invade o próximo)
PAD_X, PAD_Y, RAIO = 14, 8, 14
LIGACAO = {"o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das", "em", "no", "na", "nos",
           "nas", "por", "para", "pra", "com", "sem", "que", "e", "ou", "se", "ao", "aos", "à", "às"}
COR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _sem(t: str) -> str:
    return re.sub(r"[^\w]", "", t.lower())


def cartoes(palavras: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Frases por pontuação/pausa >= 0,6 s; cada frase em cartões de até 3 palavras e 18 caracteres, sem terminar
    em artigo/preposição quando a palavra seguinte cabe no mesmo cartão."""
    frases, atual = [], []
    for w in palavras:
        if atual and float(w["start"]) - float(atual[-1]["end"]) > PAUSA_QUEBRA:
            frases.append(atual)
            atual = []
        atual.append(w)
        if str(w["text"]).strip()[-1:] in ".?!…,":
            frases.append(atual)
            atual = []
    if atual:
        frases.append(atual)
    saida = []
    for f in frases:
        i = 0
        while i < len(f):
            j = i + 1
            while (j < len(f) and j - i < MAX_PALAVRAS
                   and len(" ".join(str(x["text"]).strip() for x in f[i:j + 1])) <= MAX_CARACTERES):
                j += 1
            while j - i > 1 and j < len(f) and _sem(str(f[j - 1]["text"])) in LIGACAO:
                j -= 1                                          # não deixa "O" / "DE" sozinho no fim do cartão
            saida.append(f[i:j])
            i = j
    return saida


def _cor_ass(hexa: str, alfa: str = "00") -> str:
    if not COR_RE.match(hexa):
        raise ValueError(f"cor inválida: {hexa} (use #RRGGBB)")
    return f"&H{alfa}{hexa[5:7]}{hexa[3:5]}{hexa[1:3]}".upper()


def _t(s: float) -> str:
    s = max(0.0, s)
    cs = int(round(s * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def _caixa(w: float, h: float, r: float) -> str:
    """Retângulo arredondado em desenho ASS (\\p1), origem no canto superior esquerdo."""
    r = min(r, h / 2, w / 2)
    k = r * 0.45
    return (f"m {r:.0f} 0 l {w - r:.0f} 0 b {w - k:.0f} 0 {w:.0f} {k:.0f} {w:.0f} {r:.0f} "
            f"l {w:.0f} {h - r:.0f} b {w:.0f} {h - k:.0f} {w - k:.0f} {h:.0f} {w - r:.0f} {h:.0f} "
            f"l {r:.0f} {h:.0f} b {k:.0f} {h:.0f} 0 {h - k:.0f} 0 {h - r:.0f} l 0 {r:.0f} b 0 {k:.0f} {k:.0f} 0 {r:.0f} 0")


def gerar_ass(palavras: List[Dict[str, Any]], destino: Path, cor: str = "#6B4C9A", duracao: Optional[float] = None,
              ocultar: Optional[List[Tuple[float, float]]] = None) -> int:
    """Escreve o .ass; devolve o número de cartões. `ocultar`: janelas sem legenda (ex.: imagem que cobre a tela)."""
    from PIL import ImageFont
    if not FONTE_ARQ.is_file():
        raise FileNotFoundError(f"fonte da legenda não encontrada: {FONTE_ARQ} (defina SOCIALMEDIA_FONTE_LEGENDA)")
    # o libass usa Fontsize = ascendente + descendente; o Pillow, o "em": converte para medir igual
    sonda = ImageFont.truetype(str(FONTE_ARQ), 1000)
    asc, desc = sonda.getmetrics()
    fonte = ImageFont.truetype(str(FONTE_ARQ), max(8, round(TAM * 1000 / (asc + desc))))
    espaco = fonte.getlength(" ")
    falas = [w for w in palavras if str(w.get("text", "")).strip()]
    cards = [c for c in cartoes(falas)
             if not any(a <= float(c[0]["start"]) < b for a, b in (ocultar or []))]
    linhas = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2",
        "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding",
        f"Style: Cap,{FONTE_NOME},{TAM},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,6,2,5,0,0,0,1",
        f"Style: Box,{FONTE_NOME},{TAM},{_cor_ass(cor)},{_cor_ass(cor)},{_cor_ass(cor)},&H00000000,0,0,0,0,100,100,0,0,"
        "1,0,0,7,0,0,0,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for i, c in enumerate(cards):
        ini = float(c[0]["start"])
        fim = float(c[-1]["end"]) + FOLGA_FIM
        if i + 1 < len(cards):
            fim = min(fim, float(cards[i + 1][0]["start"]) - 0.01)
        if duracao:
            fim = min(fim, duracao - 0.02)
        if fim <= ini:
            continue
        textos = [re.sub(r"[,.;:]+$", "", str(w["text"]).strip()).upper() for w in c]
        larguras = [fonte.getlength(t) for t in textos]
        total = sum(larguras) + espaco * (len(textos) - 1)
        x = W / 2 - total / 2
        topo = Y - TAM / 2
        linhas.append(f"Dialogue: 1,{_t(ini)},{_t(fim)},Cap,,0,0,0,,{{\\pos({W // 2},{Y})}}{' '.join(textos)}")
        for k, (w, larg) in enumerate(zip(c, larguras)):
            a = max(ini, float(w["start"]))
            b = float(c[k + 1]["start"]) if k + 1 < len(c) else fim
            b = min(max(b, a + 0.08), fim)
            caixa = _caixa(larg + 2 * PAD_X, TAM + 2 * PAD_Y, RAIO)
            linhas.append(f"Dialogue: 0,{_t(a)},{_t(b)},Box,,0,0,0,,"
                          f"{{\\pos({x - PAD_X:.0f},{topo - PAD_Y:.0f})\\bord0\\shad0\\p1}}{caixa}{{\\p0}}")
            x += larg + espaco
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return len(cards)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    cor = sys.argv[sys.argv.index("--cor") + 1] if "--cor" in sys.argv else "#6B4C9A"
    dados = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(gerar_ass(dados.get("words", dados), Path(sys.argv[2]), cor), "cartões")
