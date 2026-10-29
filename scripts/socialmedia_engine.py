#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SocialmedIA Engine — Motor determinístico de regras de edição viral e posicionamento
empresarial para Instagram Reels (1080x1920).

Integra as regras do Instagram Viral Editing Playbook (PLAYBOOK.md) aos motores locais:
- editonny (~/.local/share/editonny) + hyperframes
- effectcraft (effectcraft/ec_grafico.py, junto desta skill)
- ffmpeg (cortes, overlays, legenda ASS e cadeia de áudio)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# 0. PRESETS (presets/*.json): dados editaveis sem mexer no codigo, validados ao carregar
# ============================================================================

PRESETS_DIR = Path(__file__).resolve().parent.parent / "presets"
ESTILOS_EDITONNY = ("amber", "paper", "night")
_COR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class PresetInvalido(ValueError):
    pass


def _carregar_preset(nome: str) -> Dict[str, Any]:
    caminho = PRESETS_DIR / nome
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise PresetInvalido(f"{caminho}: {e}") from e


def _validar_nichos(d: Dict[str, Any]) -> None:
    """Falha cedo, com o nicho e o campo, se um preset editado à mão ficou incompleto."""
    obrig = ("label", "editonny_style", "palette", "typography", "pacing", "zoom_plan", "safe_zones",
             "cta_keyword_default", "hashtags_default")
    for nome, p in d["perfis"].items():
        falta = [k for k in obrig if k not in p]
        if falta:
            raise PresetInvalido(f"nichos.json: perfil '{nome}' sem {falta}")
        if p["editonny_style"] not in ESTILOS_EDITONNY:
            raise PresetInvalido(f"nichos.json: '{nome}'.editonny_style deve ser um de {ESTILOS_EDITONNY}")
        cores = [v for k, v in p["palette"].items() if k != "stamp_color"]
        if not all(_COR.match(c) for c in cores):
            raise PresetInvalido(f"nichos.json: '{nome}'.palette tem cor fora de #RRGGBB")
        if len(p["hashtags_default"]) > 5:
            raise PresetInvalido(f"nichos.json: '{nome}' com mais de 5 hashtags padrão")
    for apelido, alvo in d["apelidos"].items():
        if alvo not in d["perfis"]:
            raise PresetInvalido(f"nichos.json: apelido '{apelido}' aponta para nicho inexistente '{alvo}'")
    for nicho, tipo in d["tipo_padrao"].items():
        if nicho not in d["perfis"] or tipo not in REEL_TYPES:
            raise PresetInvalido(f"nichos.json: tipo_padrao '{nicho}: {tipo}' inválido")


def _validar_memes(d: Dict[str, Any]) -> Dict[str, Any]:
    for nome in d["bloqueados_tier3"]:
        if nome in d["catalogo"]:
            raise PresetInvalido(f"memes.json: '{nome}' está bloqueado (tier 3) e no catálogo ao mesmo tempo")
    for nome in d["remix"]:
        if nome not in d["catalogo"]:
            raise PresetInvalido(f"memes.json: remix de '{nome}', que não está no catálogo")
    for nome, m in d["catalogo"].items():
        if not (isinstance(m.get("trim_s"), list) and len(m["trim_s"]) == 2 and m["trim_s"][0] < m["trim_s"][1]):
            raise PresetInvalido(f"memes.json: '{nome}'.trim_s inválido")
    return d


# ============================================================================
# 1. BANCO DE REGRAS DETERMINÍSTICAS POR NICHO / ARQUÉTIPO EMPRESARIAL
# ============================================================================

_NICHOS = _carregar_preset("nichos.json")
NICHE_PROFILES: Dict[str, Dict[str, Any]] = _NICHOS["perfis"]

NICHE_ALIASES: Dict[str, str] = _NICHOS["apelidos"]


def pasta_trabalho() -> Path:
    """Pasta de trabalho (entrada_mp4/, memes_cortados/, projetos/): SOCIALMEDIA_DIR ou a pasta atual."""
    return Path(os.environ.get("SOCIALMEDIA_DIR") or Path.cwd())


def canonical_niche(niche_key: str) -> str:
    """Nome canônico do nicho (minúsculas, '-'/' ' viram '_', apelidos resolvidos). Única normalização do motor."""
    key = niche_key.strip().lower().replace("-", "_").replace(" ", "_")
    return NICHE_ALIASES.get(key, key)


def resolve_niche(niche_key: str) -> Dict[str, Any]:
    canonical = canonical_niche(niche_key)
    if canonical not in NICHE_PROFILES:
        raise ValueError(
            f"Nicho '{niche_key}' desconhecido. Opções válidas: "
            f"{sorted(list(NICHE_PROFILES.keys()) + list(NICHE_ALIASES.keys()))}"
        )
    return NICHE_PROFILES[canonical]


# Tipos de Reel medidos em 27 Reels virais de 14 empresas (20/10/2026,
# references/medicao-2026-10). O ritmo depende do tipo, não só do nicho.
REEL_TYPES: Dict[str, Dict[str, Any]] = {
    "montagem_criador": {
        "median_cut_s": [0.8, 1.6],
        "max_shot_s": 8.0,
        "first_cut_max_s": 1.2,
        "edl_dry_mode": True,
        "pause_cut_threshold_s": 0.35,
        "max_cuts_per_minute": 45.0,
    },
    "fala_continua": {
        "median_cut_s": [4.0, 12.0],
        "max_shot_s": 37.0,
        "moving_text_over_s": 8.0,
        "edl_dry_mode": False,
        "pause_cut_threshold_s": 0.65,
        "max_cuts_per_minute": 10.0,
    },
    "produto_sem_fala": {"median_cut_s": [4.0, 5.0], "max_shot_s": 10.0, "max_cuts_per_minute": 20.0},
    "personagem_ia": {
        "median_cut_s": [1.4, 2.0],
        "max_shot_s": 8.0,
        "first_cut_max_s": 2.5,
        "requires_gemini": ("pro", "enterprise"),
        "max_cuts_per_minute": 35.0,
    },
}

EVIDENCE_RULES: Dict[str, Any] = {
    "forbid_reuse_across_projects": True,
    "max_moments_default": 2,
    "default_fit": "contain",
    "card_box_px": [50, 520, 980, 654],
    "card_border_radius_px": 36,
    "require_entry_transition_scene": "compositions/scenes/transition-zoom-0X.html",
    "require_exit_transition_scene": "compositions/scenes/transition-glow-0X.html",
    "require_zoom_motion": {"scale": 1.10, "ease": "power2.out"},   # formato do editonny: zooms[] = {at, end, scale, ease}
    "require_sfx": ["whoosh", "photo", "pop"],
}

NICHE_DEFAULT_REEL_TYPE: Dict[str, str] = _NICHOS["tipo_padrao"]
_validar_nichos(_NICHOS)


def business_caption_style(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Legenda de fala medida nos Reels de empresa (40-48 px, caixa normal, y 1330-1400)."""
    return {"estilo": "karaoke", "tamanho": 44, "maiusculas": False, "contorno": 2, "sombra": 2,
            "cor": "#FFFFFF", "destaque": profile["palette"]["accent_primary"], "animacao": "nenhuma",
            "pos_y": 1360}


def resolve_reel_type(niche: str, tipo: Optional[str], plano_gemini: Optional[str]) -> str:
    canonical = canonical_niche(niche)
    tipo = tipo or NICHE_DEFAULT_REEL_TYPE.get(canonical, "fala_continua")
    if tipo not in REEL_TYPES:
        raise ValueError(f"Tipo de Reel '{tipo}' desconhecido. Opções: {sorted(REEL_TYPES)}")
    needs = REEL_TYPES[tipo].get("requires_gemini")
    if needs and (plano_gemini or "").lower() not in needs:
        raise ValueError("personagem_ia (Argon) só com cliente no plano Gemini Pro ou Enterprise "
                         "(--plano-gemini pro|enterprise).")
    return tipo


# ============================================================================
# 2. GERADOR DE PLANO DE EDIÇÃO E PROJECT.JSON (EDITONNY + EFFECTCRAFT)
# ============================================================================

def build_editing_plan(
    niche: str,
    reel_format: str,
    title: str,
    items: Optional[List[Dict[str, Any]]] = None,
    tipo: Optional[str] = None,
    plano_gemini: Optional[str] = None,
    evidence_moments: Optional[List[Dict[str, Any]]] = None,
    max_evidence_moments: int = 2,
) -> Dict[str, Any]:
    profile = resolve_niche(niche)
    tipo = resolve_reel_type(niche, tipo, plano_gemini)
    items = items or []
    evidence_moments = evidence_moments or []

    if len(evidence_moments) > max_evidence_moments:
        raise ValueError(
            f"Excesso de imagens: foram solicitados {len(evidence_moments)} momentos, "
            f"mas o limite máximo permitido é {max_evidence_moments} (Regra #6 do Playbook)."
        )

    animations: List[Dict[str, Any]] = []
    running_total = 0.0
    for idx, item in enumerate(items, start=1):
        val = float(item.get("price", 0.0))
        at_sec = float(item.get("at", idx * 4.0))
        exit_sec = float(item.get("exit", at_sec + 3.0))
        new_total = round(running_total + val, 2)
        animations.append(
            {
                "type": "counter",
                "id": f"carrinho{idx:02d}",
                "at": at_sec,
                "exit": exit_sec,
                "initialValue": running_total,
                "finalValue": new_total,
                "decimals": 2,
                "prefix": "R$",
                "duration": 0.6,
                "where": profile["safe_zones"]["counter_xy"],
            }
        )
        running_total = new_total

    if items:
        last_exit = animations[-1]["exit"]
        animations.append(
            {
                "type": "stamp",
                "id": "total",
                "at": round(last_exit + 0.15, 2),
                "exit": round(last_exit + 6.50, 2),
                "text": f"R$ {running_total:.0f} · {len(items)} ITENS",
                "color": profile["palette"]["stamp_color"],
                "where": profile["safe_zones"]["stamp_xy"],
            }
        )

    blocks: List[Dict[str, Any]] = []
    scenes_list: List[Dict[str, Any]] = []
    base_zoom = profile["zoom_plan"]["base_scale"]
    if not evidence_moments:
        blocks.append(
            {
                "scene": "fullscreen",
                "start": 0,
                "zoom": base_zoom,
            }
        )
    else:
        for idx, ev in enumerate(sorted(evidence_moments, key=lambda x: float(x["start"])), start=1):
            ev_start = round(float(ev["start"]), 2)
            ev_end = round(float(ev["end"]), 2)
            ev_dur = round(ev_end - ev_start, 2)
            ev_file = str(ev["file"])
            ev_label = str(ev.get("label", ""))
            ev_fit = str(ev.get("fit", EVIDENCE_RULES["default_fit"]))
            ev_block: Dict[str, Any] = {
                "scene": "evidence",
                "start": ev_start,
                "end": ev_end,
                "file": ev_file,
                "fit": ev_fit,
                "zooms": [
                    {
                        "at": ev_start,
                        "end": ev_end,
                        "scale": 1.10,
                        "duration": round(max(1.0, ev_dur - 0.2), 2),
                        "ease": "power2.out",
                        "sound": "whoosh",
                    }
                ],
            }
            if ev_label:
                ev_block["label"] = ev_label
            blocks.append(ev_block)
            scenes_list.append(
                {
                    "file": f"compositions/scenes/transition-zoom-{idx:02d}.html",
                    "start": round(max(0.0, ev_start - 0.25), 2),
                    "end": round(ev_start + 0.25, 2),
                    "name": f"Transition zoom {idx}",
                    "sceneId": "transition-zoom",
                }
            )
            scenes_list.append(
                {
                    "file": f"compositions/scenes/transition-glow-{idx:02d}.html",
                    "start": round(max(0.0, ev_end - 0.20), 2),
                    "end": round(ev_end + 0.20, 2),
                    "name": f"Transition glow {idx}",
                    "sceneId": "transition-glow",
                }
            )

    editonny_project = {
        "title": title,
        "skill": str(Path.home() / ".local" / "share" / "editonny" / "engine"),
        "edit": "../edit",
        "format": "9:16",
        "style": profile["editonny_style"],
        "zoom": base_zoom,
        "corrections": {},
        "blocks": blocks,
        "captions": {
            "enabled": True,
            "style": "standard",
            "maxWords": profile["typography"]["max_words_per_block"],
            "inFrame": False,
        },
        "animations": animations,
        "scenes": scenes_list,
        "sounds": [],
        "endHold": 0,
        "endCard": {
            "enabled": False,
            "seconds": 1.8,
            "title": "",
            "sub": "",
            "button": "Tap Learn more",
            "logo": "",
        },
    }

    return {
        "niche_profile": profile,
        "reel_format": reel_format,
        "reel_type": {"tipo": tipo, **REEL_TYPES[tipo]},
        "evidence_rules": EVIDENCE_RULES,
        "legenda_empresa": business_caption_style(profile),
        "encerramento": (
            "anúncio de marca: cartão de 0,8-1,2 s com logo + 1 CTA; "
            "conteúdo de criador/série: sem cartão, termina na última fala"
            + ("; saúde: responsável técnico + CRO/CRM fixo na tela" if profile is NICHE_PROFILES["saude"] else "")
        ),
        "editonny_project_json": editonny_project,
        "effectcraft_hook_spec": {
            "type": "titulo",
            "text_must_match_speech": title,
            "position_xy": profile["safe_zones"]["hook_xy"],
            "font_size_px": profile["typography"]["pill_px"],
            "stroke_px": profile["typography"]["stroke_px"],
            "duration_s": 5.0,
        },
        "audio_dsp_spec": {
            "target_lufs": -14.0,
            "max_true_peak_dbtp": -1.5,
            "music_bed_speech_db": -26.0,
            "ffmpeg_voice_chain": (
                "highpass=f=80,"
                "equalizer=f=3000:t=q:w=1:g=2,"
                "acompressor=threshold=-18dB:ratio=3:attack=5:release=50,"
                "loudnorm=I=-14:TP=-1.5:LRA=11"
            ),
        },
    }


# ============================================================================
# 3. GERADOR E VALIDADOR DE LEGENDAS DE POST POR NICHO
# ============================================================================

def generate_post_caption(
    niche: str,
    hook_line: str,
    bullets: List[str],
    location_or_proof: str = "",
    cta_keyword: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    profile = resolve_niche(niche)
    padroes_usados = [nome for nome, dado in (("cta_keyword", cta_keyword), ("hashtags", hashtags)) if not dado]
    kw = cta_keyword or profile["cta_keyword_default"]
    tags = hashtags or profile["hashtags_default"]

    # O texto é do usuário: nunca é cortado nem reescrito aqui, só validado.
    hook_clean = hook_line.strip()
    erros = []
    if not hook_clean:
        erros.append("gancho (linha 1) vazio")
    if len(hook_clean) > 125:
        erros.append(f"gancho com {len(hook_clean)} caracteres: a prévia do Instagram mostra ~125")
    if len(tags) > 5:
        erros.append(f"{len(tags)} hashtags: o Instagram aceita no máximo 5")

    bullet_block = "\n".join(f"• {b.strip()}" for b in bullets if b.strip())
    loc_block = f"\n\n📍 {location_or_proof.strip()}" if location_or_proof.strip() else ""
    cta_block = f"\n\n💬 Comente \"{kw}\" para receber os detalhes no Direct."  # um CTA só
    tag_block = "\n\n" + " ".join(tags)

    full_caption = f"{hook_clean}\n\n{bullet_block}{loc_block}{cta_block}{tag_block}"

    return {
        "niche": profile["label"],
        "preview_line_1": hook_clean,
        "preview_chars": len(hook_clean),
        "preview_under_125": len(hook_clean) <= 125,
        "total_chars": len(full_caption),
        "hashtag_count": len(tags),
        "hashtags_under_5": len(tags) <= 5,
        "valid": not erros,
        "errors": erros,
        "defaults_used": padroes_usados,
        "caption_text": full_caption,
    }


# ============================================================================
# 4. AUDITOR DE EDL.JSON CONTRA O INSTAGRAM VIRAL EDITING PLAYBOOK
# ============================================================================

MEMES_PADRAO = Path(__file__).resolve().parent.parent / "terceiros" / "memes.json"
REMIX_GENERICO = "reação equivalente encenada pela equipe (surpresa, erro, comemoração, suspense)"


def catalogo_memes() -> Optional[Dict[str, Any]]:
    """Catálogo LOCAL de memes: os clipes são de terceiros, então o catálogo (nomes, recorte, crop, LUFS) fica fora
    do Git, em terceiros/memes.json (ou no caminho de SOCIALMEDIA_MEMES_JSON). None quando não existe."""
    caminho = Path(os.environ.get("SOCIALMEDIA_MEMES_JSON") or MEMES_PADRAO)
    if not caminho.is_file():
        return None
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise PresetInvalido(f"{caminho}: {e}") from e
    return _validar_memes(dados)


def recommend_meme_insertion(niche: str, intent: str, conta: str = "empresa") -> Dict[str, Any]:
    profile = resolve_niche(niche)
    canonical = canonical_niche(niche)
    if conta not in ("empresa", "pessoal_sem_receita"):
        raise ValueError("conta deve ser 'empresa' ou 'pessoal_sem_receita'")
    if canonical in ("saude",):
        return {
            "allowed": False,
            "niche": profile["label"],
            "reason": (
                "Posicionamento Clínico/Saúde (style: paper): o uso de memes é desativado "
                "para preservar autoridade médica/odontológica e confiança do paciente."
            ),
        }

    intent_key = intent.strip().lower()
    if not intent_key:
        raise ValueError("intenção vazia: diga a reação (ex.: surpresa, erro_compra, suspense, fome)")
    cat = catalogo_memes()
    matches = [] if cat is None else [
        (fname, meta)
        for fname, meta in cat["catalogo"].items()
        if fname not in cat["bloqueados_tier3"]
        and any(intent_key in tag or tag in intent_key for tag in meta["intents"])
    ]
    fname = matches[0][0] if matches else None

    if conta == "empresa":
        # Clipes de TV/celebridade/personagem: uso comercial sem licença = risco de
        # indenização (Súmula 403 STJ) e de bloqueio pelo Rights Manager. Ver módulo 08 §0.
        return {
            "allowed": False,
            "niche": profile["label"],
            "intent": intent,
            "reason": "Conta de empresa não usa clipe de terceiro (direito de imagem/autoral).",
            "remix_do_formato": {
                "reacao_encenada": (cat["remix"].get(fname) if cat and fname else None) or REMIX_GENERICO,
                "duracao_s": [0.8, 2.0],
                "som": "efeito sonoro licenciado (biblioteca efeitos/), nunca o áudio do programa",
                "insercao": "corte seco no meio do vídeo (nunca antes de 3 s)",
                "referencia_tom": fname,
            },
        }
    if cat is None:
        return {"allowed": False, "niche": profile["label"], "intent": intent,
                "reason": f"catálogo local de memes ausente ({MEMES_PADRAO.parent.name}/memes.json): os clipes são de "
                          "terceiros e o catálogo fica só na máquina"}
    if not matches:
        return {"allowed": False, "niche": profile["label"], "intent": intent,
                "reason": f"nenhum meme do catálogo local para a intenção '{intent}'",
                "intencoes_disponiveis": sorted({t for m in cat["catalogo"].values() for t in m["intents"]})}
    meta = matches[0][1]
    in_s, out_s = meta["trim_s"]
    dur = round(out_s - in_s, 2)
    gain = meta["gain_db_to_minus16"]
    crop = meta["crop"]

    if canonical in ("industria", "servicos"):
        mode = "SFX_ONLY"
        ffmpeg_filter = (
            f"-ss {in_s:.2f} -to {out_s:.2f} -i \"memes_cortados/{fname}\" "
            f"-af \"volume={gain:+.1f}dB\""
        )
    elif meta["chroma_green"]:
        mode = "CHROMA_OVERLAY"
        ffmpeg_filter = (
            f"[1:v]trim=start={in_s:.2f}:end={out_s:.2f},setpts=PTS-STARTPTS,"
            f"chromakey=0x00FF00:0.26:0.08,despill=green,scale=620:-1[meme];"
            f"[0:v][meme]overlay=x=W-w-40:y=1180:eof_action=pass"
        )
    else:
        mode = "PIP_CARD_OR_EMPILHADO"
        ffmpeg_filter = (
            f"[1:v]trim=start={in_s:.2f}:end={out_s:.2f},setpts=PTS-STARTPTS,"
            f"crop={crop},scale=840:630:flags=lanczos[meme];"
            f"[0:v][meme]overlay=x=120:y=280:eof_action=pass"
        )

    return {
        "allowed": True,
        "niche": profile["label"],
        "intent": intent,
        "selected_file": str(pasta_trabalho() / "memes_cortados" / fname),
        "insertion_mode": mode,
        "trim_window_s": [in_s, out_s],
        "effective_duration_s": dur,
        "active_crop": crop,
        "measured_lufs": meta["lufs"],
        "audio_gain_adjustment_db": gain,
        "ffmpeg_snippet": ffmpeg_filter,
        "blocked_tier3_files": cat["bloqueados_tier3"],
    }

def audit_edl(edl_path: Path, tipo: str = "montagem_criador") -> Dict[str, Any]:
    if tipo not in REEL_TYPES:
        raise ValueError(f"Tipo de Reel '{tipo}' desconhecido. Opções: {sorted(REEL_TYPES)}")
    regra = REEL_TYPES[tipo]
    data = json.loads(edl_path.read_text(encoding="utf-8"))
    ranges = data.get("ranges", [])
    if not ranges:
        return {"valid": False, "error": "Nenhum intervalo encontrado em ranges."}

    durations = [round(float(r["end"]) - float(r["start"]), 3) for r in ranges]
    speech_durations = [
        round(float(r["end"]) - float(r["start"]), 3)
        for r in ranges
        if "sem fala" not in r.get("quote", "").lower()
    ]
    # 1ª palavra no tempo do VÍDEO CORTADO (transcrição do corte ou alinhamento do editonny). O início do trecho
    # no original não serve: 3 s de silêncio antes da fala não atrasam o gancho se o corte começa na fala.
    first_start: Optional[float] = None
    for nome in ("waveform_words.json", "transcripts/cut.json"):
        try:
            words = json.loads((edl_path.parent / nome).read_text(encoding="utf-8")).get("words", [])
        except (OSError, ValueError):
            continue
        falas = [w for w in words if str(w.get("text", w.get("word", ""))).strip()]
        if falas:
            first_start = float(falas[0]["start"])
            break
    total_duration = round(sum(durations), 2)
    median_cut = round(statistics.median(speech_durations), 2) if speech_durations else 0.0
    mean_cut = round(statistics.mean(speech_durations), 2) if speech_durations else 0.0
    max_cut = max(speech_durations) if speech_durations else 0.0
    min_cut = min(speech_durations) if speech_durations else 0.0
    # corte = emenda entre dois trechos (trechos - 1): uma tomada única tem zero cortes
    cuts_per_minute = round((len(ranges) - 1) / (total_duration / 60.0), 2) if total_duration > 0 else 0.0
    any_dry_true = any(bool(r.get("dry", False)) for r in ranges)

    # Also check edl_manual.json next to edl.json if present
    manual_edl = edl_path.parent / "edl_manual.json"
    if manual_edl.is_file():
        try:
            manual_data = json.loads(manual_edl.read_text(encoding="utf-8"))
            if any(bool(r.get("dry", False)) for r in manual_data.get("ranges", [])):
                any_dry_true = True
        except Exception:
            pass

    long_cuts = [
        {"id": r.get("id"), "duration_s": round(float(r["end"]) - float(r["start"]), 2), "quote": r.get("quote", "")[:50]}
        for r in ranges
        if "sem fala" not in r.get("quote", "").lower() and (float(r["end"]) - float(r["start"])) > regra["max_shot_s"]
    ]
    lo, hi = regra["median_cut_s"]
    if tipo == "fala_continua":            # tomada longa é aceita até max_shot_s (PLAYBOOK §0), com texto em movimento
        hi = regra["max_shot_s"]
    max_cpm = float(regra.get("max_cuts_per_minute", 45.0))

    jcut = data.get("jcut", {})
    checks = {
        "hook_starts_under_0_45s": None if first_start is None else first_start <= 0.45,
        "median_cut_in_reel_type_band": lo <= median_cut <= hi,
        "jcut_configured": bool(jcut.get("lead_frames", 0) >= 2),
        "output_is_vertical_1080x1920": (
            data.get("output", {}).get("width") == 1080 and data.get("output", {}).get("height") == 1920
        ),
        "zero_speech_cuts_over_reel_type_max": len(long_cuts) == 0,
        "cuts_per_minute_within_limit": cuts_per_minute <= max_cpm,
        "no_auto_dry_chopping_in_fala_continua": (not any_dry_true) if tipo == "fala_continua" else True,
    }

    avaliados = {k: v for k, v in checks.items() if v is not None}
    return {
        "file": str(edl_path),
        "reel_type": {"tipo": tipo, **regra},
        "total_ranges": len(ranges),
        "total_duration_s": total_duration,
        "cuts_per_minute": cuts_per_minute,
        "any_dry_true": any_dry_true,
        "first_word_start_s": first_start,
        "speech_cut_stats_s": {
            "min": min_cut,
            "median": median_cut,
            "mean": mean_cut,
            "max": max_cut,
        },
        "cuts_exceeding_max_shot": long_cuts,
        "playbook_checks": checks,
        "score_pct": round(100.0 * sum(1 for v in avaliados.values() if v) / max(1, len(avaliados)), 1),
        "not_evaluated": [k for k, v in checks.items() if v is None],
    }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class _CacheHash:
    """SHA-256 por (tamanho, mtime) para o audit-project não reler todas as imagens de todos os projetos."""

    def __init__(self, arquivo: Path):
        self.arquivo, self.mudou = arquivo, False
        try:
            self.dados = json.loads(arquivo.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.dados = {}

    def hash(self, caminho: Path) -> str:
        st = caminho.stat()
        chave, assinatura = str(caminho.resolve()), [st.st_size, st.st_mtime_ns]
        item = self.dados.get(chave)
        if item and item[:2] == assinatura:
            return item[2]
        digest = _sha256_file(caminho)
        self.dados[chave], self.mudou = assinatura + [digest], True
        return digest

    def salvar(self) -> None:
        if self.mudou and self.arquivo.parent.is_dir():
            try:
                tmp = self.arquivo.with_suffix(".tmp")
                tmp.write_text(json.dumps(self.dados), encoding="utf-8")
                tmp.replace(self.arquivo)
            except OSError:
                pass                                   # cache é só aceleração: sem ele o resultado é o mesmo


def audit_project(
    proj_dir: Path,
    tipo: str = "fala_continua",
    max_images: int = 2,
) -> Dict[str, Any]:
    """
    Portão de qualidade bloqueante para projetos editonny/socialmedia:
    1. Proíbe reutilização de imagens de outros projetos (comparação SHA-256 em projetos/*/proj/assets/);
    2. Garante que haja no máximo `max_images` momentos de imagem (`scene: "evidence"`);
    3. Garante que TODA imagem tenha cena de transição na entrada e na saída + movimento de zoom;
    4. Audita a parcimônia de cortes na fala (`edl.json` e `edl_manual.json`).
    """
    proj_dir = proj_dir.resolve()
    proj_json_path = proj_dir / "project.json"
    if not proj_json_path.is_file():
        return {"valid": False, "error": f"project.json não encontrado em {proj_dir}"}

    proj_data = json.loads(proj_json_path.read_text(encoding="utf-8"))
    blocks = proj_data.get("blocks", [])
    animations = proj_data.get("animations", [])
    evidence_blocks = [b for b in blocks if b.get("scene") == "evidence"]

    # 1. Check image reuse across other projects in `projetos/`
    current_project_root = proj_dir.parent.resolve()
    projetos_root = current_project_root.parent
    other_project_hashes: Dict[str, str] = {}
    cache = _CacheHash(projetos_root / ".socialmedia_hashes.json")
    if projetos_root.is_dir():
        for other_proj in projetos_root.iterdir():
            if not other_proj.is_dir() or other_proj.resolve() == current_project_root:
                continue
            for img_path in other_proj.rglob("*"):
                if img_path.is_file() and img_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                    if {"_pieces", "renders", "_removidas"} & set(img_path.parts):
                        continue
                    try:
                        other_project_hashes[cache.hash(img_path)] = str(img_path)
                    except OSError:
                        pass
    cache.salvar()

    reused_images: List[Dict[str, str]] = []
    assets_dir = proj_dir / "assets"
    if assets_dir.is_dir():
        for img_path in assets_dir.iterdir():
            if img_path.is_file() and img_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                digest = _sha256_file(img_path)
                if digest in other_project_hashes:
                    reused_images.append(
                        {
                            "file": str(img_path.name),
                            "reused_from": other_project_hashes[digest],
                            "sha256": digest,
                        }
                    )

    # 2. Check transitions and zoom on every evidence block
    scene_anims = [
        {"start": float(a.get("at", a.get("start", -999))), "end": float(a.get("exit", a.get("end", -999)))}
        for a in animations
        if a.get("type") == "scene"
    ] + [
        {"start": float(s.get("start", s.get("at", -999))), "end": float(s.get("end", s.get("exit", -999)))}
        for s in proj_data.get("scenes", [])
    ]
    missing_transitions: List[Dict[str, Any]] = []
    for idx, b in enumerate(evidence_blocks, start=1):
        b_start = float(b.get("start", 0.0))
        b_end = float(b.get("end", 0.0))
        has_entry_trans = any(
            abs(s["start"] - b_start) <= 0.40 or (s["start"] <= b_start <= s["end"])
            for s in scene_anims
        )
        has_exit_trans = any(
            abs(s["start"] - b_end) <= 0.40 or (s["start"] <= b_end <= s["end"])
            for s in scene_anims
        )
        has_zoom = bool(b.get("zooms"))
        if not (has_entry_trans and has_exit_trans and has_zoom):
            missing_transitions.append(
                {
                    "evidence_index": idx,
                    "file": b.get("file"),
                    "start": b_start,
                    "end": b_end,
                    "has_entry_transition": has_entry_trans,
                    "has_exit_transition": has_exit_trans,
                    "has_zoom_motion": has_zoom,
                }
            )

    # 3. Audit EDL
    edl_rel = proj_data.get("edit", "../edit")
    edl_path = (proj_dir / edl_rel / "edl.json").resolve()
    edl_report = audit_edl(edl_path, tipo=tipo) if edl_path.is_file() else {"score_pct": 0.0, "playbook_checks": {}}

    checks = {
        "no_reused_images_from_previous_projects": len(reused_images) == 0,
        "evidence_moments_within_limit": 0 < len(evidence_blocks) <= max_images if evidence_blocks else True,
        "every_image_has_entry_and_exit_transition_and_zoom": len(missing_transitions) == 0,
        "edl_passes_playbook_and_parcimony": edl_report.get("score_pct", 0.0) == 100.0,
    }

    return {
        "project_dir": str(proj_dir),
        "reel_type": tipo,
        "evidence_moments_count": len(evidence_blocks),
        "max_images_allowed": max_images,
        "reused_images_detected": reused_images,
        "images_missing_transition_or_zoom": missing_transitions,
        "edl_audit": edl_report,
        "project_checks": checks,
        "passed_all": all(checks.values()),
    }


# ============================================================================
# CLI ENTRYPOINT
# ============================================================================

def main() -> int:
    try:
        return _main()
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1


def _main() -> int:
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="SocialmedIA — Motor de Regras de Edição Viral para Instagram")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan", help="Gera plano de edição e project.json para um nicho e formato")
    p_plan.add_argument("--niche", required=True, help="Nicho empresarial (ex: varejo, saude, industria, material_construcao)")
    p_plan.add_argument("--format", default="desafio_orcamento", help="Formato do Reel")
    p_plan.add_argument("--title", required=True, help="Título falado no gancho")
    p_plan.add_argument("--tipo", choices=sorted(REEL_TYPES), default=None,
                        help="Tipo de Reel (padrão: o do nicho)")
    p_plan.add_argument("--plano-gemini", default=None, help="pro|enterprise libera personagem_ia (Argon)")

    p_cap = sub.add_parser("caption", help="Gera e valida legenda de Instagram por nicho")
    p_cap.add_argument("--niche", required=True, help="Nicho empresarial")
    p_cap.add_argument("--hook", required=True, help="Primeira linha da legenda (<= 125 chars)")
    p_cap.add_argument("--bullets", nargs="+", required=True, help="Itens ou pontos principais")
    p_cap.add_argument("--location", default="", help="Endereço ou prova operacional")
    p_cap.add_argument("--keyword", default="", help="Palavra-código do CTA (vazio = padrão do nicho, a confirmar com o cliente)")
    p_cap.add_argument("--hashtags", nargs="*", default=None, help="Até 5 hashtags (vazio = padrão do nicho, a confirmar)")

    p_audit = sub.add_parser("audit", help="Audita um arquivo edl.json contra o Instagram Viral Editing Playbook")
    p_audit.add_argument("edl_path", type=Path, help="Caminho para edl.json")
    p_audit.add_argument("--tipo", choices=sorted(REEL_TYPES), default="montagem_criador", help="Tipo de Reel")

    p_audit_proj = sub.add_parser(
        "audit-project",
        help="Portão bloqueante: audita imagens reutilizadas, limite de 2 momentos, transições obrigatórias e cortes da fala",
    )
    p_audit_proj.add_argument("proj_dir", type=Path, help="Caminho para a pasta proj/ do projeto")
    p_audit_proj.add_argument("--tipo", choices=sorted(REEL_TYPES), default="fala_continua", help="Tipo de Reel")
    p_audit_proj.add_argument("--max-images", type=int, default=2, help="Máximo permitido de momentos de imagem (padrão: 2)")

    p_meme = sub.add_parser("meme", help="Recomenda meme seguro de memes_cortados com crop, trim e ganho exatos")
    p_meme.add_argument("--niche", required=True, help="Nicho empresarial")
    p_meme.add_argument("--intent", required=True, help="Intenção (ex: erro_compra, surpresa, suspense, fome, gambiarra)")
    p_meme.add_argument("--conta", choices=["empresa", "pessoal_sem_receita"], default="empresa",
                        help="empresa = só remix encenado; pessoal_sem_receita = pode usar o clipe")

    p_ver = sub.add_parser("verificar", help="Portão de qualidade do vídeo exportado (resolução, fps, loudness, pico, sincronia)")
    p_ver.add_argument("video", type=Path, help="RASCUNHO_*.mp4 ou FINAL_*.mp4")

    args = parser.parse_args()
    if args.cmd == "verificar":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import qualidade
        res = qualidade.verificar(args.video)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["valido"] else 1
    if args.cmd == "plan":
        res = build_editing_plan(args.niche, args.format, args.title, tipo=args.tipo, plano_gemini=args.plano_gemini)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "caption":
        res = generate_post_caption(
            niche=args.niche,
            hook_line=args.hook,
            bullets=args.bullets,
            location_or_proof=args.location,
            cta_keyword=args.keyword or None,
            hashtags=args.hashtags or None,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["valid"] else 1
    elif args.cmd == "audit":
        res = audit_edl(args.edl_path, args.tipo)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("score_pct", 0.0) == 100.0 else 1
    elif args.cmd == "audit-project":
        res = audit_project(args.proj_dir, tipo=args.tipo, max_images=args.max_images)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("passed_all", False) else 1
    elif args.cmd == "meme":
        res = recommend_meme_insertion(args.niche, args.intent, args.conta)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
