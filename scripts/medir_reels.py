"""Mede cada Reel baixado: cortes (scene>0.3), loudness, silêncio, fala (Whisper) e folha de quadros."""
import json, re, subprocess, sys, pathlib

PASTA = pathlib.Path(sys.argv[1])
SAIDA = PASTA.parent / "medidas.json"
QUADROS = PASTA.parent / "quadros"
QUADROS.mkdir(exist_ok=True)
_MODELO = None


def transcrever(wav):
    """Palavras com tempo (faster-whisper small, CPU, pt) -> [{"w", "start", "end"}]. O wav ja e 16 kHz mono:
    vai lido pelo soundfile (o leitor do faster-whisper depende de uma versao certa do PyAV)."""
    global _MODELO
    import numpy as np
    import soundfile as sf
    from faster_whisper import WhisperModel
    _MODELO = _MODELO or WhisperModel("small", device="cpu", compute_type="int8")
    dados, _ = sf.read(wav, dtype="float32")
    segs, _ = _MODELO.transcribe(np.asarray(dados), language="pt", word_timestamps=True, vad_filter=True)
    return [{"w": p.word.strip(), "start": p.start, "end": p.end} for s in segs for p in (s.words or [])]


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")


def probe(f):
    r = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                        "-of", "json", str(f)]).stdout)
    v = next(s for s in r["streams"] if s["codec_type"] == "video")
    n, d = v["r_frame_rate"].split("/")
    return float(r["format"]["duration"]), v["width"], v["height"], round(int(n) / int(d), 2)


def cortes(f, limiar=0.3):
    err = run(["ffmpeg", "-hide_banner", "-i", str(f), "-vf", f"select='gt(scene,{limiar})',showinfo", "-an", "-f", "null", "-"]).stderr
    return [round(float(t), 2) for t in re.findall(r"pts_time:([\d.]+)", err)]


def loud(f):
    err = run(["ffmpeg", "-hide_banner", "-i", str(f), "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"]).stderr
    resumo = err[err.rfind("Summary:"):]
    g = lambda k: (m := re.search(k + r":\s+(-?[\d.]+)", resumo)) and float(m.group(1))
    return {"lufs": g("I"), "lra": g("LRA"), "true_peak": g("Peak")}


def silencio(f, dur):
    err = run(["ffmpeg", "-hide_banner", "-i", str(f), "-af", "silencedetect=noise=-40dB:d=0.3", "-vn", "-f", "null", "-"]).stderr
    total = sum(float(x) for x in re.findall(r"silence_duration: ([\d.]+)", err))
    return round(total / dur, 3)


def fala(f):
    wav = QUADROS / (f.stem + ".wav")
    run(["ffmpeg", "-y", "-hide_banner", "-i", str(f), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    try:
        w = transcrever(str(wav))
    finally:
        wav.unlink(missing_ok=True)
    if not w:
        return {"palavras": 0}
    span = w[-1]["end"] - w[0]["start"]
    pausas = [b["start"] - a["end"] for a, b in zip(w, w[1:])]
    return {"palavras": len(w), "primeira_palavra": round(w[0]["start"], 2),
            "ppm": round(len(w) / span * 60, 1) if span > 0 else None,
            "pausas_maiores_0_35": sum(1 for p in pausas if p >= 0.35),
            "texto_3s": " ".join(x["w"] for x in w if x["start"] < 3.0),
            "texto": " ".join(x["w"] for x in w)}


def folha(f, dur):
    ts = [0.0, 0.5, 1.5, 3.0, dur * 0.5, max(dur - 1.0, 0)]
    out = QUADROS / (f.stem + ".png")
    ins, flt = [], []
    for i, t in enumerate(ts):
        ins += ["-ss", f"{t:.2f}", "-i", str(f)]
        flt.append(f"[{i}:v]scale=270:480,setsar=1[v{i}]")  # drawtext trava o FFmpeg sem fontconfig
    flt.append("".join(f"[v{i}]" for i in range(len(ts))) + f"hstack=inputs={len(ts)}")
    run(["ffmpeg", "-y", "-hide_banner", *ins, "-filter_complex", ";".join(flt), "-frames:v", "1", str(out)])
    return out.name


medidas = json.loads(SAIDA.read_text(encoding="utf-8")) if SAIDA.exists() else {}
for f in sorted(PASTA.glob("*.mp4")):
    if f.stem in medidas:
        continue
    dur, w, h, fps = probe(f)
    c = cortes(f)
    bounds = [0.0] + c + [dur]
    planos = sorted(b - a for a, b in zip(bounds, bounds[1:]))
    m = {"dur": round(dur, 2), "res": f"{w}x{h}", "fps": fps, "cortes": len(c), "tempos_corte": c,
         "plano_medio": round(dur / (len(c) + 1), 2), "plano_mediana": round(planos[len(planos) // 2], 2),
         "plano_max": round(planos[-1], 2), "primeiro_corte": c[0] if c else None,
         "cortes_por_10s_inicio": sum(1 for t in c if t < 10), **loud(f), "silencio": silencio(f, dur),
         "fala": fala(f), "folha": folha(f, dur)}
    medidas[f.stem] = m
    SAIDA.write_text(json.dumps(medidas, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f.stem, m["dur"], m["cortes"], m["lufs"], m["fala"].get("palavras"), flush=True)
print("FIM")
