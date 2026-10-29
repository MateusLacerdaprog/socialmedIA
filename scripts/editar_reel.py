#!/usr/bin/env python3
"""SocialmedIA -> editonny -> RASCUNHO verificado, em etapas com cache.

    python scripts/editar_reel.py VIDEO --niche saude --title "frase dita no vídeo" [--tipo fala_continua]
           [--images a.jpg b.jpg --momentos 4.5-8 20-24] [--modelo small] [--qualidade draft|standard]
           [--ate transcrever|cortar|projeto|render] [--refazer] [--sem-ocr]

Etapas (cada uma pula se a saída já existe com os mesmos parâmetros; --refazer força):
  1. preparar    projeto em <SOCIALMEDIA_DIR>/projetos/socialmedia_<video>/ + plano por nicho
  2. transcrever editonny transcribe (local)
  3. cortar      EDL pelo tipo de Reel -> waveform_cut (+ precise_edges em fala_continua) -> render_cut
  4. projeto     build.py new + plano da SocialmedIA (estilo, legenda, zoom, imagens com transições do editonny)
  5. render      compose + HyperFrames -> título do EffectCraft (só com palavras ditas) -> RASCUNHO_<video>.mp4
  6. portões     audit-project, verificar (com correção de loudness em 2 passadas) e quality_gate do editonny (OCR)

Nada sai como FINAL: o usuário assiste o RASCUNHO e aprova.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "effectcraft"))

import legenda_teleprompter  # noqa: E402
import qualidade  # noqa: E402
import receber_mp4  # noqa: E402
import socialmedia_engine as sme  # noqa: E402

EDITONNY = Path(os.environ.get("EDITONNY_DIR") or Path.home() / ".local" / "share" / "editonny")
ENGINE = EDITONNY / "engine"
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
ETAPAS = ("preparar", "transcrever", "cortar", "projeto", "render")
PAD_INICIO, PAD_FIM = 0.12, 0.20          # s antes da 1ª e depois da última palavra de cada trecho
DUR_TITULO = 3.0                          # s do título do gancho (PLAYBOOK: 3–8 s)
TITULO_ATE = 4.1                          # a pílula de título fica 0,05–4,1 s (padrão aprovado)
TITULO_MAX = 45                           # caracteres: resumo curto, cabe numa pílula
FILTRO_ENTREGA = "scale=1080:1920:flags=lanczos,setsar=1,format=yuv420p"
NITIDEZ = ",unsharp=5:5:0.35:3:3:0"        # só quando a gravação é menor que 1080 de largura
# gravação pequena (ex.: vídeo que passou pelo WhatsApp): tira blocos e ruído e amplia ANTES do corte, uma vez
RESTAURAR_ABAIXO = 1080
FILTRO_RESTAURO = ("deblock=filter=strong:block=8,hqdn3d=1.5:1.5:3:3,scale=1080:-2:flags=lanczos,"
                   "unsharp=5:5:0.6:5:5:0,format=yuv420p")
# taxa garantida (10 Mbps, mínimo 6): imagem limpa/restaurada não pode sair "econômica" e cheia de blocos
CODIFICACAO_ENTREGA = ["-c:v", "libx264", "-b:v", "10M", "-minrate", "6M", "-maxrate", "16M", "-bufsize", "20M",
                       "-preset", "slow", "-profile:v", "high", "-r", "30"]


class ErroEdicao(RuntimeError):
    pass


def log(msg: str) -> None:
    print(f"[socialmedia] {msg}", file=sys.stderr, flush=True)


# ------------------------------------------------------------------ chamadas ao editonny
def python_motor() -> Path:
    py = ENGINE / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not py.is_file():
        raise ErroEdicao(f"editonny não preparado em {EDITONNY} (rode o install dele ou defina EDITONNY_DIR)")
    return py


def ambiente() -> Dict[str, str]:
    return {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "EDITONNY_ENGINE_DIR": str(ENGINE),
            "HYPERFRAMES_NO_TELEMETRY": "1", "DO_NOT_TRACK": "1", "HF_CLI_TELEMETRY_DISABLED": "1",
            "HYPERFRAMES_NO_UPDATE_CHECK": "1", "HYPERFRAMES_NO_AUTO_INSTALL": "1", "HYPERFRAMES_NO_CAPTURE_DOTENV": "1",
            "HF_HUB_DISABLE_SYMLINKS_WARNING": "1"}


def rodar(cmd: List[Any], cwd: Path, tempo: int = 900) -> str:
    try:
        r = subprocess.run([str(c) for c in cmd], cwd=str(cwd), env=ambiente(), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=tempo, creationflags=SEM_JANELA)
    except subprocess.TimeoutExpired:
        raise ErroEdicao(f"{Path(str(cmd[1])).name if len(cmd) > 1 else cmd[0]} passou de {tempo} s e foi encerrado")
    if r.returncode != 0:
        raise ErroEdicao(((r.stdout or "") + (r.stderr or "")).strip()[-1500:] or f"falhou: {cmd[:2]}")
    return r.stdout


def helper(nome: str, *args: Any, cwd: Path, tempo: int = 900) -> str:
    return rodar([python_motor(), ENGINE / "helpers" / f"{nome}.py", *args], cwd, tempo)


def build(proj: Path, *args: Any, tempo: int = 900) -> str:
    return rodar([python_motor(), proj / "build.py", *args], proj, tempo)


def aplicar_cena(proj: Path, cena: str, ini: float, fim: float) -> None:
    rodar([python_motor(), EDITONNY / "visuals" / "apply.py", "--project", proj, "--use", cena,
           "--start", f"{max(0.0, ini):.2f}", "--end", f"{fim:.2f}"], proj, 300)


# ------------------------------------------------------------------ decisões da SocialmedIA (puras, testáveis)
def montar_edl(palavras: List[Dict[str, Any]], tipo: str, fonte: str, duracao: float) -> Dict[str, Any]:
    """EDL do editonny pelo tipo de Reel (PLAYBOOK §0).

    montagem_criador/personagem_ia: corta pausas >= 0,35 s; "dry": true (o waveform_cut ainda aperta as bordas).
    fala_continua: só corta entre parágrafos (pausa >= 0,65 s); "dry": false = bordas mantidas, sem picotar a fala
    (no editonny "dry": false também desliga o J-cut naquele trecho; as bordas vão para o precise_edges).
    produto_sem_fala ou sem fala: o vídeo inteiro.
    """
    regra = sme.REEL_TYPES[tipo]
    falas = [w for w in palavras if str(w.get("text", "")).strip()]
    base = {"sources": {"C1": fonte}, "jcut": {"lead_frames": 4, "tail_trim_frames": 2},
            "output": {"width": 1080, "height": 1920, "fps": 30}}
    pausa = regra.get("pause_cut_threshold_s")
    if not falas or pausa is None:
        return {**base, "ranges": [{"id": "r1", "source": "C1", "start": 0.0, "end": round(duracao, 3),
                                    "dry": False, "quote": "sem fala"}]}
    grupos, atual = [], [falas[0]]
    for a, b in zip(falas, falas[1:]):
        if float(b["start"]) - float(a["end"]) >= pausa:
            grupos.append(atual)
            atual = []
        atual.append(b)
    grupos.append(atual)
    limite = regra.get("max_cuts_per_minute")
    if tipo == "fala_continua" and limite:              # parcimônia: junta pelas menores pausas (a pausa fica)
        def por_minuto(gs):                             # mesma conta do audit_edl: emendas / minuto de corte
            dur_corte = sum(float(g[-1]["end"]) - float(g[0]["start"]) + PAD_INICIO + PAD_FIM for g in gs)
            return (len(gs) - 1) / max(dur_corte / 60.0, 1e-6)
        while len(grupos) > 1 and por_minuto(grupos) > limite:
            i = min(range(len(grupos) - 1),
                    key=lambda j: float(grupos[j + 1][0]["start"]) - float(grupos[j][-1]["end"]))
            grupos[i:i + 2] = [grupos[i] + grupos[i + 1]]
    seco = tipo != "fala_continua"
    ranges = []
    for i, g in enumerate(grupos):
        ini = max(0.0, float(g[0]["start"]) - PAD_INICIO)
        fim = min(duracao, float(g[-1]["end"]) + PAD_FIM)
        if i + 1 < len(grupos):                                    # nunca encosta no próximo trecho
            fim = min(fim, float(grupos[i + 1][0]["start"]) - PAD_INICIO - 0.01)
        if ranges:
            ini = max(ini, ranges[-1]["end"] + 0.01)
        ranges.append({"id": f"r{i + 1}", "source": "C1", "start": round(ini, 3), "end": round(fim, 3),
                       "dry": seco, "quote": " ".join(str(w["text"]).strip() for w in g)[:80]})
    return {**base, "ranges": ranges}


def _normal(t: str) -> List[str]:
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", t)


def titulo_dito(titulo: str, palavras: List[Dict[str, Any]]) -> Optional[float]:
    """Instante (s) em que o título aparece falado em sequência na transcrição do corte; None se não foi dito.
    Regra da SocialmedIA: título na tela só com palavras realmente faladas."""
    alvo, falas = _normal(titulo), [(_normal(str(w.get("text", ""))), w) for w in palavras]
    seq = [(tok, w) for toks, w in falas for tok in toks]
    n = len(alvo)
    if not n:
        return None
    for i in range(len(seq) - n + 1):
        if [s[0] for s in seq[i:i + n]] == alvo:
            return float(seq[i][1]["start"])
    return None


def projeto_editonny(cfg: Dict[str, Any], plano: Dict[str, Any]) -> Dict[str, Any]:
    """Mistura o plano da SocialmedIA no project.json criado pelo `build.py new` (mantém skill/edit/caminhos)."""
    p = plano["editonny_project_json"]
    novo = dict(cfg)
    for k in ("title", "format", "style", "zoom", "captions", "animations", "endHold", "endCard", "corrections"):
        if k in p:
            novo[k] = p[k]
    novo["blocks"] = p["blocks"]
    return novo


# ------------------------------------------------------------------ estado (cache por etapa)
class Estado:
    def __init__(self, pasta: Path):
        self.arq = pasta / "socialmedia_estado.json"
        try:
            self.d = json.loads(self.arq.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.d = {}

    @staticmethod
    def chave(*partes: Any) -> str:
        return hashlib.sha256(json.dumps(partes, sort_keys=True, default=str).encode()).hexdigest()[:16]

    def feito(self, etapa: str, chave: str, *saidas: Path) -> bool:
        return self.d.get(etapa) == chave and all(s.exists() for s in saidas)

    def marcar(self, etapa: str, chave: str) -> None:
        self.d[etapa] = chave
        for depois in ETAPAS[ETAPAS.index(etapa) + 1:]:            # etapa refeita invalida as seguintes
            self.d.pop(depois, None)
        self.arq.write_text(json.dumps(self.d, indent=1), encoding="utf-8")


def _assinatura(arq: Path) -> List[Any]:
    st = arq.stat()
    return [arq.name, st.st_size, st.st_mtime_ns]


def _palavras(edit: Path, stem: str) -> List[Dict[str, Any]]:
    d = json.loads((edit / "transcripts" / f"{stem}.json").read_text(encoding="utf-8"))
    return [w for w in d.get("words", []) if str(w.get("text", "")).strip()]


# ------------------------------------------------------------------ pipeline
def editar(video: Path, niche: str, titulo: str, tipo: Optional[str] = None, imagens: Optional[List[str]] = None,
           momentos: Optional[List[List[float]]] = None, modelo: str = "small", qualidade_hf: str = "looks",
           ate: str = "render", refazer: bool = False, ocr: bool = True,
           correcoes: Optional[Dict[str, str]] = None, rotulos: Optional[List[str]] = None,
           teleprompter: bool = True) -> Dict[str, Any]:
    imagens, momentos, correcoes, rotulos = imagens or [], momentos or [], correcoes or {}, rotulos or []
    if len(imagens) != len(momentos):
        raise ValueError("cada imagem precisa de um momento (--momentos 4.5-8 ...), na mesma ordem")
    if rotulos and len(rotulos) != len(imagens):
        raise ValueError("--rotulos: um título por imagem, na mesma ordem")
    validar_titulo(titulo)
    for r in rotulos:
        validar_titulo(r)
    tipo = sme.resolve_reel_type(niche, tipo, None)
    res: Dict[str, Any] = {"video": str(video), "tipo": tipo, "etapas": {}, "avisos": []}
    if not imagens:
        res["avisos"].append("sem imagens: o padrão aprovado usa 1–2 imagens do cliente em card (--images --momentos "
                             "--rotulos); peça as imagens deste vídeo")

    # 1. preparar
    job = receber_mp4.prepare_socialmedia_job(video_path=video, niche=niche, reel_format="reel", title=titulo,
                                              images=imagens)
    pasta = Path(job["pasta_projeto"])
    edit, proj = pasta / "edit", pasta / "proj"
    est = Estado(pasta) if not refazer else Estado.__new__(Estado)
    if refazer:
        est.arq, est.d = pasta / "socialmedia_estado.json", {}
    evid = [{"start": a, "end": b, "file": f"assets/{Path(img).name}", "label": (rotulos[i] if rotulos else "")}
            for i, (img, (a, b)) in enumerate(zip(imagens, momentos))]
    plano = sme.build_editing_plan(niche, "reel", titulo, tipo=tipo, evidence_moments=evid,
                                   max_evidence_moments=max(2, len(evid)))
    if titulo.strip():                                   # pílula de título do editonny (o padrão aprovado)
        plano["editonny_project_json"]["animations"].insert(0, pilula_titulo(titulo))
    res["etapas"]["preparar"] = str(pasta)

    # 2. transcrever (a fonte entra no edit/ por link, sem duplicar o arquivo)
    fonte = edit / "fontes" / video.name
    fonte.parent.mkdir(parents=True, exist_ok=True)
    if not fonte.exists() or fonte.stat().st_size != video.stat().st_size:
        fonte.unlink(missing_ok=True)
        try:
            os.link(video, fonte)
        except OSError:
            shutil.copy2(video, fonte)
    k = Estado.chave(_assinatura(video), modelo)
    tr = edit / "transcripts" / f"{fonte.stem}.json"
    if not est.feito("transcrever", k, tr):
        log(f"transcrevendo ({modelo})…")
        helper("transcribe", fonte, "--edit-dir", edit, "--language", "pt", "--model", modelo, cwd=pasta, tempo=1800)
        est.marcar("transcrever", k)
    palavras = _palavras(edit, fonte.stem)
    res["etapas"]["transcrever"] = {"palavras": len(palavras)}
    largura = int(qualidade.medir(fonte)["largura"] or 0)
    imagem = fonte                                       # vídeo que vai para o corte (a transcrição é a mesma)
    if 0 < largura < RESTAURAR_ABAIXO:
        imagem = restaurar(fonte, edit / "fontes" / f"{fonte.stem}_restaurado.mp4")
        res["etapas"]["restauro"] = {"de": largura, "para": 1080, "filtro": FILTRO_RESTAURO}
    if ate == "transcrever":
        return res

    # 3. cortar
    dur = float(qualidade.medir(fonte)["duracao_s"])
    edl = montar_edl(palavras, tipo, str(imagem), dur)
    k = Estado.chave(k, edl, FILTRO_RESTAURO if imagem != fonte else "")
    cut = edit / "cut.mp4"
    if not est.feito("cortar", k, cut, edit / "transcripts" / "cut.json"):
        log(f"cortando ({len(edl['ranges'])} trecho(s), {tipo})…")
        (edit / "edl_manual.json").write_text(json.dumps(edl, ensure_ascii=False, indent=1), encoding="utf-8")
        helper("waveform_cut", edit / "edl_manual.json", "-o", edit / "edl.json", cwd=pasta)
        if tipo == "fala_continua":                       # bordas "dry": false caem em pausas medidas
            helper("precise_edges", edit / "edl.json", "--apply", cwd=pasta)
        helper("render_cut", edit / "edl.json", cwd=pasta, tempo=1800)
        helper("transcribe", cut, "--edit-dir", edit, "--language", "pt", "--model", modelo, "--force",
               cwd=pasta, tempo=1800)
        for nome, args in (("face_layout", ("--edit-dir", edit, "--force")), ("align_words", (edit,))):
            try:                                          # melhoram enquadramento e tempo; sem rosto segue
                helper(nome, *args, cwd=pasta)
            except ErroEdicao as e:
                log(f"{nome} não rodou ({str(e)[-120:]}); seguindo")
        est.marcar("cortar", k)
    res["etapas"]["cortar"] = sme.audit_edl(edit / "edl.json", tipo)
    if ate == "cortar":
        return res

    # 4. projeto do editonny com o plano da SocialmedIA
    plano["editonny_project_json"]["corrections"] = correcoes      # legenda do editonny com as correções pedidas
    if teleprompter:                                   # a legenda teleprompter da SocialmedIA substitui a do editonny
        plano["editonny_project_json"]["captions"]["enabled"] = False
    k = Estado.chave(k, plano["editonny_project_json"], [_assinatura(Path(i)) for i in imagens])
    if not est.feito("projeto", k, proj / "project.json"):
        log("montando o projeto do editonny…")
        if proj.exists():                                  # nunca apaga: guarda o projeto anterior
            anterior = pasta / "_proj_anterior"
            shutil.rmtree(anterior, ignore_errors=True)
            proj.rename(anterior)
        rodar([python_motor(), ENGINE / "project-template" / "build.py", "new", proj, "--edit", edit,
               "--style", plano["editonny_project_json"]["style"]], pasta, 300)
        if imagens:
            (proj / "assets").mkdir(exist_ok=True)
            for img in imagens:
                shutil.copy2(img, proj / "assets" / Path(img).name)
        cfg = json.loads((proj / "project.json").read_text(encoding="utf-8"))
        (proj / "project.json").write_text(json.dumps(projeto_editonny(cfg, plano), ensure_ascii=False, indent=2),
                                           encoding="utf-8")
        for cena in plano["editonny_project_json"]["scenes"]:        # transições de verdade (cenas do editonny)
            aplicar_cena(proj, cena["sceneId"], cena["start"], cena["end"])
        est.marcar("projeto", k)
    res["etapas"]["projeto"] = sme.audit_project(proj, tipo=tipo, max_images=max(2, len(imagens)))
    if not res["etapas"]["projeto"]["passed_all"]:
        log("audit-project reprovou: veja etapas.projeto.project_checks (o render segue para revisão)")
    if ate == "projeto":
        return res

    # 5. render + título do EffectCraft (só se foi dito)
    rascunho = pasta / f"RASCUNHO_{video.stem}.mp4"
    hf = proj / "renders" / "rascunho.mp4"
    k = Estado.chave(k, qualidade_hf, titulo, correcoes, teleprompter, "entrega-5")
    if not est.feito("render", k, rascunho):
        log("compondo e renderizando (HyperFrames)…")
        build(proj, "prepare", tempo=600)
        build(proj, "compose", tempo=900)
        try:                                              # sons (pop/whoosh) nos gráficos, como no padrão aprovado
            helper("sound_plan", "--project", proj, "--mode", "visuals", cwd=pasta, tempo=600)
            build(proj, "compose", tempo=900)
        except ErroEdicao as e:
            res["avisos"].append(f"sons não aplicados: {str(e)[-160:]}")
        versao = re.search(r"hyperframes@(\d+\.\d+\.\d+)", (proj / "package.json").read_text(encoding="utf-8"))
        npx = shutil.which("npx")
        if not (versao and npx):
            raise ErroEdicao("HyperFrames: Node.js (npx) ou versão fixada no package.json não encontrados")
        rodar([npx, "--yes", f"hyperframes@{versao.group(1)}", "render", "--quiet", "--quality", qualidade_hf,
               "--resolution", "portrait", "--video-frame-format", "png", "--output", hf, "."], proj, 3600)
        tmp = rascunho.with_suffix(".tmp.mp4")
        falas = corrigir_palavras(_palavras(edit, "cut"), correcoes)
        ocupado = [(0.0, TITULO_ATE)] if titulo.strip() else []
        ocupado += [(a - 0.3, b + 0.3) for a, b in momentos]      # pílulas das imagens ficam no mesmo lugar
        plano_motion = planejar_motion(falas, _juncoes(edit), float(qualidade.medir(hf)["duracao_s"]),
                                       abertura=not titulo.strip(), ocupado=ocupado)
        legenda = None
        if teleprompter:
            legenda = pasta / "legenda_teleprompter.ass"
            n = legenda_teleprompter.gerar_ass(falas, legenda, plano["niche_profile"]["palette"]["accent_primary"],
                                               float(qualidade.medir(hf)["duracao_s"]))
            res["legenda"] = {"estilo": "teleprompter", "cartoes": n}
        res["motion"] = aplicar_motion(hf, tmp, plano_motion, pasta,
                                       nitidez=False, legenda=legenda)   # a nitidez já veio no restauro
        os.replace(tmp, rascunho)
        est.marcar("render", k)
    res["rascunho"] = str(rascunho)

    # 6. portões do arquivo final
    ver = qualidade.verificar(rascunho)
    regras_erro = {i["regra"] for i in ver["itens"] if i["nivel"] == "erro"}
    if regras_erro & {"loudness", "true_peak"}:
        log("loudness fora do alvo: 2ª passada do loudnorm…")
        qualidade.corrigir_loudness(rascunho)
        ver = qualidade.verificar(rascunho)
        ver["corrigido_loudness"] = True
    res["verificar"] = ver
    res["quadros"] = str(qualidade.folha_de_quadros(rascunho, pasta / "quadros_rascunho.png"))
    if ocr:
        try:
            r = subprocess.run([str(python_motor()), str(ENGINE / "helpers" / "quality_gate.py"), str(rascunho),
                                "--project", str(proj), "--json"], cwd=str(pasta), env=ambiente(), capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=1800, creationflags=SEM_JANELA)
            saida = r.stdout or ""
            qg = json.loads(saida[saida.find("{"):saida.rfind("}") + 1])      # reprovar é resultado, não erro
            qg["ocr_disponivel"] = qg.get("text_reader") is not None
            res["quality_gate_editonny"] = qg
        except (OSError, ValueError, subprocess.TimeoutExpired) as e:
            res["quality_gate_editonny"] = {"rodou": False, "motivo": str(e)[-300:]}
    (pasta / "socialmedia_resultado.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str),
                                                      encoding="utf-8")
    return res


CONECTORES = {"que", "mas", "e", "enquanto", "quando", "se", "porque", "pois", "para", "onde", "então", "entao"}


def _sem(texto: str) -> str:
    return " ".join(_normal(texto))


def _frases(palavras: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    frases, atual = [], []
    for w in palavras:
        atual.append(w)
        if str(w["text"]).strip()[-1:] in ".?!":
            frases.append(atual)
            atual = []
    return frases + ([atual] if atual else [])


def _aparar(ws: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Título nunca termina em artigo/preposição/conjunção."""
    from ec_grafico import LIGACAO
    while ws and _sem(ws[-1]["text"]) in LIGACAO:
        ws = ws[:-1]
    return ws


def _texto(ws: List[Dict[str, Any]]) -> str:
    t = " ".join(str(w["text"]).strip() for w in ws).strip()
    while t and t[-1] in ".,;:":
        t = t[:-1]
    return t.upper()


def restaurar(origem: Path, destino: Path) -> Path:
    """Versão de trabalho em 1080 de largura, sem blocos de compressão (cache: só refaz se a origem mudar)."""
    marca = destino.with_suffix(".json")
    assinatura = json.dumps([_assinatura(origem), FILTRO_RESTAURO])
    if destino.exists() and marca.exists() and marca.read_text(encoding="utf-8") == assinatura:
        return destino
    log("restaurando a gravação (deblock + lanczos 1080 + nitidez)…")
    tmp = destino.with_suffix(".tmp.mp4")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(origem), "-vf", FILTRO_RESTAURO, "-c:v", "libx264",
                        "-crf", "12", "-preset", "fast", "-c:a", "copy", str(tmp)],
                       capture_output=True, text=True, creationflags=SEM_JANELA)
    if r.returncode:
        tmp.unlink(missing_ok=True)
        raise ErroEdicao(f"restauro da gravação falhou: {r.stderr.strip()[-300:]}")
    os.replace(tmp, destino)
    marca.write_text(assinatura, encoding="utf-8")
    return destino


def validar_titulo(texto: str) -> None:
    """Título = resumo curto e fiel do que é dito (ex.: "Você tem *medo* de perder o dente?"), com a palavra-chave
    entre asteriscos (sai colorida na pílula). Nunca promessa, número ou dado que o vídeo não diz."""
    limpo = texto.replace("*", "").strip()
    if len(limpo) > TITULO_MAX:
        raise ValueError(f"título com {len(limpo)} caracteres: resuma em até {TITULO_MAX} (cabe numa pílula)")
    if texto.count("*") % 2:
        raise ValueError("destaque do título: use *palavra* (asteriscos em par)")


def pilula_titulo(texto: str, ate: float = TITULO_ATE) -> Dict[str, Any]:
    """Pílula de título do editonny (animação `label` no topo), igual ao padrão aprovado pelo usuário."""
    return {"type": "label", "id": "titulo", "at": 0.05, "exit": ate, "text": texto.strip(), "where": "top"}


def corrigir_palavras(palavras: List[Dict[str, Any]], correcoes: Dict[str, str]) -> List[Dict[str, Any]]:
    """Mesma ideia das `corrections` do editonny: troca uma sequência falada (sem acento/pontuação) mantendo o tempo."""
    out = [dict(w) for w in palavras]
    for de, para in correcoes.items():
        alvo, novo = _normal(de), para.split()
        if len(alvo) != len(novo):
            continue
        for i in range(len(out) - len(alvo) + 1):
            if [_sem(w["text"]) for w in out[i:i + len(alvo)]] == alvo:
                for k, t in enumerate(novo):
                    pont = "".join(ch for ch in str(out[i + k]["text"])[-1:] if ch in ".,?!")
                    out[i + k]["text"] = t + pont
    return out


def planejar_motion(palavras: List[Dict[str, Any]], juncoes: List[float], duracao: float,
                    titulo: str = "", abertura: bool = True,
                    ocupado: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """Gráficos do EffectCraft SÓ com palavras ditas (nunca texto do agente), no padrão do motion já aprovado:
    abertura (título dado e dito, ou o começo da 1ª frase), pergunta curta falada, número falado (contador),
    fechamento (fim da última frase) e flash em cada emenda de corte. Mínimo de 1,8 s na tela, sem sobreposição."""
    frases = [f for f in _frases(palavras) if f]
    flashes = [{"receita": "flash", "inicio": round(max(0.0, j - 0.2), 2), "duracao": 0.4} for j in juncoes]
    if not frases:
        return flashes

    def item(receita, ws, cor="#FFFFFF", animacao="typewriter", extra=0.8, maximo=3.0):
        ini = max(0.0, float(ws[0]["start"]) - 0.05)
        dur = min(max(float(ws[-1]["end"]) - ini + extra, 1.8), maximo, max(0.5, duracao - ini - 0.05))
        return {"receita": receita, "texto": _texto(ws), "inicio": round(ini, 2), "duracao": round(dur, 2),
                "cor": cor, "animacao": animacao}

    textos = []
    dito = titulo_dito(titulo, palavras) if titulo.strip() else None
    if not abertura:
        pass                                          # a pílula de título já abre o vídeo
    elif dito is not None:
        n = len(_normal(titulo))
        i0 = next(i for i, w in enumerate(palavras) if float(w["start"]) == dito)
        textos.append(item("titulo", palavras[i0:i0 + n]))
    else:
        primeira = frases[0]
        fim_clausula = next((i + 1 for i, w in enumerate(primeira) if str(w["text"]).strip()[-1:] == ","), len(primeira))
        clausula = primeira[:fim_clausula]
        if len(clausula) > 5:
            corte = next((i for i in range(3, len(clausula)) if _sem(clausula[i]["text"]) in CONECTORES), 5)
            clausula = clausula[:corte]
        clausula = _aparar(clausula)
        if len(clausula) >= 2:
            textos.append(item("titulo", clausula))
    for f in frases[1:]:
        if str(f[-1]["text"]).strip().endswith("?") and 2 <= len(f) <= 6:
            textos.append(item("texto", f, cor="#FFDE00", animacao="bounceInWords", maximo=2.6))
    for w in palavras:
        num = re.sub(r"\D", "", str(w["text"]))
        if num and len(num) <= 7:
            textos.append({"receita": "contador", "ate": int(num), "inicio": round(max(0.0, float(w["start"]) - 0.3), 2),
                           "duracao": 1.8, "cor": "#FFDE00"})
    ultima = frases[-1]
    if len(frases) > 1 or len(ultima) > 6:
        fim = ultima[-5:]
        pos = [i for i in range(1, len(ultima) - 2) if _sem(ultima[i]["text"]) in CONECTORES]
        if len(ultima) > 5 and pos and 3 <= len(ultima) - pos[-1] - 1 <= 6:
            fim = ultima[pos[-1] + 1:]
        textos.append(item("titulo", fim, extra=1.0))
    escolhidos, livre = [], -1.0
    janelas = list(ocupado or [])
    for t in sorted(textos, key=lambda x: x["inicio"]):
        bate = any(t["inicio"] < b and t["inicio"] + t["duracao"] > a for a, b in janelas)
        if t["inicio"] >= livre and t["inicio"] + 0.5 < duracao and not bate:
            escolhidos.append(t)
            livre = t["inicio"] + t["duracao"] + 0.1
    return sorted(escolhidos + flashes, key=lambda x: x["inicio"])


def aplicar_motion(video: Path, saida: Path, itens: List[Dict[str, Any]], pasta: Path,
                   nitidez: bool = False, legenda: Optional[Path] = None) -> Dict[str, Any]:
    """Entrega: gráficos do EffectCraft (cache por conteúdo) + 1080x1920 em alta qualidade, numa compressão só.
    Os arquivos intermediários ficam no tamanho de trabalho; só a entrega é convertida."""
    try:
        import ec_grafico as ec
        tem_ec = os.path.isfile(ec.CLI)
    except ImportError:
        tem_ec = False
    if not tem_ec:
        itens = []
    (pasta / "motion").mkdir(exist_ok=True)
    entradas, filtros, rot = [], [], "0:v"
    for k, it in enumerate(itens):
        a = argparse.Namespace(receita=it["receita"], texto=it.get("texto"), duracao=it["duracao"], x=540,
                               y=250 if it["receita"] != "contador" else 330, cor=it.get("cor", "#FFFFFF"),
                               tamanho=96, raio=150, animacao=it.get("animacao", "typewriter"), de=0,
                               ate=it.get("ate", 100), sufixo="", saida=None)
        ec.validar(a)
        webm = pasta / "motion" / f"{Estado.chave(vars(a))}.webm"
        if not webm.exists():
            ec.gerar(a, str(webm))
        entradas += ["-c:v", "libvpx-vp9", "-i", str(webm.resolve())]
        ini, fim = it["inicio"], it["inicio"] + it["duracao"]
        filtros.append(f"[{k + 1}:v]setpts=PTS-STARTPTS+{ini:.3f}/TB[g{k}]")
        filtros.append(f"[{rot}][g{k}]overlay=0:0:eof_action=pass:enable='between(t,{ini:.3f},{fim:.3f})'[v{k}]")
        rot = f"v{k}"
    # legenda por cima de tudo (o .ass vai pelo nome, com o FFmpeg rodando na pasta dele: sem escapar caminho)
    sub = f"subtitles={legenda.name}," if legenda else ""
    filtros.append(f"[{rot}]{sub}{FILTRO_ENTREGA}{NITIDEZ if nitidez else ''}[saida]")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(Path(video).resolve()), *entradas,
                        "-filter_complex", ";".join(filtros), "-map", "[saida]", "-map", "0:a?", *CODIFICACAO_ENTREGA,
                        "-c:a", "copy", "-movflags", "+faststart", str(Path(saida).resolve())],
                       cwd=str(legenda.parent if legenda else pasta),
                       capture_output=True, text=True, creationflags=SEM_JANELA)
    if r.returncode:
        saida.unlink(missing_ok=True)
        raise ErroEdicao(f"a entrega em 1080p falhou: {r.stderr.strip()[-400:]}")
    return {"aplicado": bool(itens), "itens": itens, "entrega": "1080x1920", "nitidez": nitidez}


def _juncoes(edit: Path) -> List[float]:
    """Instantes (s, no corte) das emendas entre trechos, pelo cut_timeline.json do editonny."""
    try:
        t = json.loads((edit / "cut_timeline.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    segs = t.get("segments") or t.get("ranges") or []
    return [round(float(s["out_start"]), 3) for s in segs[1:] if "out_start" in s]


def _momento(txt: str) -> List[float]:
    a, _, b = txt.partition("-")
    return [float(a.replace(",", ".")), float(b.replace(",", "."))]


def main() -> int:
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("--niche", required=True)
    ap.add_argument("--title", default="", help='título-resumo do que é dito, com *palavra* destacada '
                    '(ex.: "Você tem *medo* de perder o dente?"); entra na pílula de título do editonny')
    ap.add_argument("--sem-teleprompter", action="store_true",
                    help="usa a legenda do editonny em vez da teleprompter (caixa colorida na palavra falada)")
    ap.add_argument("--rotulos", nargs="*", default=[], help="título da pílula de cada imagem, na ordem das --images")
    ap.add_argument("--tipo", choices=sorted(sme.REEL_TYPES), default=None)
    ap.add_argument("--images", nargs="*", default=[])
    ap.add_argument("--momentos", nargs="*", default=[], type=_momento, help="início-fim de cada imagem, em s do corte")
    ap.add_argument("--modelo", default="small", help="Whisper do editonny (small já fica em cache; large-v3-turbo é melhor)")
    ap.add_argument("--qualidade", default="looks", choices=("draft", "looks", "delivery"),
                    help="render do HyperFrames: looks = CRF 16 (padrão, igual ao aprovado)")
    ap.add_argument("--ate", default="render", choices=ETAPAS[1:])
    ap.add_argument("--refazer", action="store_true")
    ap.add_argument("--sem-ocr", action="store_true", help="pula o quality_gate (OCR) do editonny")
    ap.add_argument("--corrigir", nargs="*", default=[], metavar="ERRADO=CERTO",
                    help='corrige a transcrição na legenda e no motion (ex.: "por meio de=por medo de")')
    a = ap.parse_args()
    try:
        res = editar(a.video.resolve(), a.niche, a.title, a.tipo, a.images, a.momentos, a.modelo, a.qualidade,
                     a.ate, a.refazer, not a.sem_ocr, dict(c.split("=", 1) for c in a.corrigir if "=" in c), a.rotulos,
                     not a.sem_teleprompter)
    except (ErroEdicao, ValueError, FileNotFoundError, sme.PresetInvalido) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    return 0 if res.get("verificar", {}).get("valido", True) else 1


if __name__ == "__main__":
    sys.exit(main())
