#!/usr/bin/env python3
"""Portão de qualidade do vídeo exportado (RASCUNHO_/FINAL_) contra as metas medidas do PLAYBOOK.

    python qualidade.py RASCUNHO_video.mp4

Lê o arquivo uma vez com o ffprobe e uma vez com o FFmpeg (ebur128 + blackdetect juntos). Saída em JSON;
código de saída 1 quando há algum `erro`. O que não dá para medir no arquivo (texto fora da zona segura,
legibilidade, português) continua sendo conferido nos quadros, a olho.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

# Metas (PLAYBOOK §1, §4 e bloco YAML; referências medidas em references/medicao-2026-10)
LARGURA, ALTURA = 1080, 1920
FPS_ACEITOS = (30.0, 60.0)
LUFS_ALVO, LUFS_TOLERANCIA = -14.0, 0.5
TRUE_PEAK_MAX = -1.5
DESVIO_AV_AVISO, DESVIO_AV_ERRO = 0.10, 0.50      # s entre o fim do vídeo e o fim do áudio
PRETO_INICIAL_MAX = 0.10                           # s de tela preta no começo (hook: proibido fade-in preto)
PREFIXOS = ("RASCUNHO_", "FINAL_")


def _rodar(args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")


def _fps(txt: str) -> float:
    n, _, d = (txt or "0/1").partition("/")
    return round(float(n) / float(d or 1), 3) if float(d or 1) else 0.0


def medir(video: Path) -> Dict[str, Any]:
    r = _rodar(["ffprobe", "-v", "error", "-show_entries",
                "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,duration",
                "-of", "json", str(video)])
    if r.returncode:
        raise ValueError(f"ffprobe não leu o arquivo: {r.stderr.strip()[-300:]}")
    info = json.loads(r.stdout or "{}")
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    m: Dict[str, Any] = {
        "duracao_s": round(float(info.get("format", {}).get("duration") or 0), 3),
        "largura": v.get("width"), "altura": v.get("height"), "fps": _fps(v.get("r_frame_rate")),
        "codec_video": v.get("codec_name"), "pix_fmt": v.get("pix_fmt"),
        "duracao_video_s": round(float(v.get("duration") or 0), 3),
        "tem_audio": a is not None, "codec_audio": a.get("codec_name") if a else None,
        "duracao_audio_s": round(float(a.get("duration") or 0), 3) if a else None,
    }
    filtros = ["-filter_complex", "[0:v]blackdetect=d=0.04:pix_th=0.10[vo]" + (";[0:a]ebur128=peak=true[ao]" if a else ""),
               "-map", "[vo]"] + (["-map", "[ao]"] if a else [])
    err = _rodar(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), *filtros, "-f", "null", "-"]).stderr
    preto = [(float(i), float(f)) for i, f in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    m["preto_inicial_s"] = round(next((f - i for i, f in preto if i <= 0.05), 0.0), 3)
    if a:
        resumo = err[err.rfind("Summary:"):] if "Summary:" in err else ""
        i = re.search(r"I:\s+(-?[\d.]+) LUFS", resumo)
        tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", resumo)
        m["lufs"] = float(i.group(1)) if i else None
        m["true_peak_dbtp"] = (float(tp.group(1)) if tp and tp.group(1) != "-inf" else None)
    return m


def verificar(video: Path) -> Dict[str, Any]:
    video = Path(video)
    if not video.is_file():
        return {"arquivo": str(video), "valido": False,
                "itens": [{"nivel": "erro", "regra": "arquivo", "detalhe": "arquivo não encontrado"}]}
    m = medir(video)
    itens: List[Dict[str, str]] = []

    def item(nivel: str, regra: str, detalhe: str) -> None:
        itens.append({"nivel": nivel, "regra": regra, "detalhe": detalhe})

    if (m["largura"], m["altura"]) != (LARGURA, ALTURA):
        item("erro", "resolucao", f"{m['largura']}x{m['altura']} (esperado {LARGURA}x{ALTURA}, 9:16)")
    if not any(abs(m["fps"] - f) < 0.05 for f in FPS_ACEITOS):
        item("aviso", "fps", f"{m['fps']} fps (PLAYBOOK: 30 ou 60)")
    if m["codec_video"] not in ("h264", "hevc"):
        item("aviso", "codec_video", f"{m['codec_video']} (use H.264 para o Instagram aceitar sem reprocessar)")
    if m["pix_fmt"] != "yuv420p":
        item("aviso", "pix_fmt", f"{m['pix_fmt']} (yuv420p é o que todo celular reproduz)")
    if m["duracao_s"] <= 0:
        item("erro", "duracao", "duração zero")
    if m["preto_inicial_s"] > PRETO_INICIAL_MAX:
        item("aviso", "inicio_preto", f"{m['preto_inicial_s']:.2f} s de tela preta no início (gancho começa no quadro 0)")
    if not m["tem_audio"]:
        item("erro", "audio", "sem trilha de áudio")
    else:
        if m["codec_audio"] != "aac":
            item("aviso", "codec_audio", f"{m['codec_audio']} (use AAC)")
        if m["duracao_audio_s"] and m["duracao_video_s"]:
            d = abs(m["duracao_video_s"] - m["duracao_audio_s"])
            if d > DESVIO_AV_AVISO:
                item("erro" if d > DESVIO_AV_ERRO else "aviso", "sincronia",
                     f"vídeo e áudio terminam {d:.2f} s fora um do outro")
        if m.get("lufs") is None:
            item("erro", "loudness", "não foi possível medir o loudness")
        elif abs(m["lufs"] - LUFS_ALVO) > LUFS_TOLERANCIA:
            item("erro", "loudness", f"{m['lufs']:.1f} LUFS (alvo {LUFS_ALVO:.0f} ± {LUFS_TOLERANCIA})")
        if m.get("true_peak_dbtp") is not None and m["true_peak_dbtp"] > TRUE_PEAK_MAX:
            item("erro", "true_peak", f"{m['true_peak_dbtp']:.1f} dBTP (máximo {TRUE_PEAK_MAX})")
    if not video.name.startswith(PREFIXOS):
        item("aviso", "nome", "o nome deve começar com RASCUNHO_ (FINAL_ só depois da aprovação do usuário)")
    return {"arquivo": str(video), "valido": not any(i["nivel"] == "erro" for i in itens), "medidas": m, "itens": itens}


def corrigir_loudness(video: Path) -> None:
    """2ª passada do loudnorm só no áudio (o vídeo é copiado): mede, aplica com os valores medidos e troca o
    arquivo no lugar (via .tmp). O loudnorm de uma passada erra 1–2 dB em vídeos curtos."""
    video = Path(video)
    alvo = f"I={LUFS_ALVO}:TP={TRUE_PEAK_MAX - 0.5}:LRA=11"   # folga: o AAC estoura um pouco o pico
    err = _rodar(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-af",
                  f"loudnorm={alvo}:print_format=json", "-vn", "-f", "null", "-"]).stderr
    bloco = err[err.rfind("{"):err.rfind("}") + 1]
    try:
        m = json.loads(bloco)
    except ValueError as e:
        raise ValueError(f"não consegui medir o loudness de {video.name}") from e
    filtro = (f"loudnorm={alvo}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
              f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    tmp = video.with_suffix(".loud.tmp.mp4")
    r = _rodar(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-map", "0:v", "-map", "0:a", "-c:v", "copy",
                "-af", filtro, "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(tmp)])
    if r.returncode or not tmp.is_file():
        tmp.unlink(missing_ok=True)
        raise ValueError(f"a correção de loudness falhou: {r.stderr.strip()[-300:]}")
    tmp.replace(video)


def folha_de_quadros(video: Path, saida: Path, n: int = 4, largura: int = 270) -> Path:
    """Quadros espalhados pelo vídeo, lado a lado, para revisar texto, zonas seguras e transições a olho."""
    dur = float(medir(Path(video))["duracao_s"]) or 1.0
    passo = dur / n
    filtro = f"fps=1/{passo:.4f}:start_time={passo / 2:.4f},scale={largura}:-2,tile={n}x1"
    r = _rodar(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", filtro, "-frames:v", "1", str(saida)])
    if r.returncode:
        raise ValueError(f"folha de quadros falhou: {r.stderr.strip()[-300:]}")
    return Path(saida)


def main() -> int:
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    try:
        res = verificar(Path(sys.argv[1]))
    except ValueError as e:
        res = {"arquivo": sys.argv[1], "valido": False, "itens": [{"nivel": "erro", "regra": "leitura", "detalhe": str(e)}]}
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["valido"] else 1


if __name__ == "__main__":
    sys.exit(main())
