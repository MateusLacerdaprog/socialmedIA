#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Pipeline Direto de Ingestão e Edição de MP4 pela Skill SocialmedIA.

Como usar:
1. Coloque qualquer arquivo .mp4 na pasta `<pasta do projeto>/entrada_mp4`
   (ou passe o caminho completo do .mp4 no chat).
2. Este script:
   - Detecta automaticamente o arquivo .mp4;
   - Aplica as regras do Nicho escolhido no Instagram Viral Editing Playbook (estilo, zoom,
     máximo de palavras por bloco, zonas seguras, contadores, memes seguros e áudio -14 LUFS);
   - Aciona o motor local (editonny + hyperframes + effectcraft) e gera
     `RASCUNHO_<nome>.mp4` + a legenda otimizada do post.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import socialmedia_engine as sme  # noqa: E402

ROOT_DIR = sme.pasta_trabalho()
INBOX_DIR = ROOT_DIR / "entrada_mp4"


def find_latest_mp4(target: str | None = None) -> Path:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    if target:
        p = Path(target.strip().strip('"').strip("'"))
        if p.is_file():
            return p.resolve()
        candidate = INBOX_DIR / p.name
        if candidate.is_file():
            return candidate.resolve()
        raise FileNotFoundError(f"Arquivo MP4 não encontrado: {target}")

    mp4s = sorted(INBOX_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not mp4s:
        raise FileNotFoundError(
            f"Nenhum arquivo .mp4 encontrado na pasta de entrada: {INBOX_DIR}"
        )
    return mp4s[0].resolve()


def inspect_mp4(video_path: Path) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate",
        "-of",
        "json",
        str(video_path),
    ]
    raw = json.loads(subprocess.check_output(cmd).decode("utf-8", errors="replace"))
    v_stream = next((s for s in raw.get("streams", []) if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in raw.get("streams", []) if s.get("codec_type") == "audio"), None)
    return {
        "arquivo": str(video_path),
        "nome": video_path.name,
        "duracao_s": round(float(raw.get("format", {}).get("duration", 0.0)), 2),
        "tamanho_mb": round(int(raw.get("format", {}).get("size", 0)) / (1024 * 1024), 2),
        "largura": v_stream.get("width"),
        "altura": v_stream.get("height"),
        "fps": v_stream.get("r_frame_rate"),
        "tem_audio": a_stream is not None,
    }


def prepare_socialmedia_job(
    video_path: Path,
    niche: str = "varejo",
    reel_format: str = "desafio_orcamento",
    title: str = "",
    images: list[str] | None = None,
) -> dict:
    info = inspect_mp4(video_path)
    images = images or []
    if len(images) > 2:
        raise ValueError(
            f"Foram passadas {len(images)} imagens, mas a regra da skill permite no máximo 2 momentos cirúrgicos."
        )

    job_dir = ROOT_DIR / "projetos" / f"socialmedia_{video_path.stem}"
    job_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = job_dir / "proj" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    faltando = [img for img in images if not Path(img).resolve().is_file()]
    if faltando:
        raise FileNotFoundError(f"Imagem enviada não encontrada: {faltando[0]}")

    # Tira de assets/ as imagens que não foram enviadas para este vídeo (movidas para _removidas/, nunca apagadas)
    approved_names = {Path(img).name for img in images}
    if images:
        for old_img in assets_dir.iterdir():
            if old_img.is_file() and old_img.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                if old_img.name not in approved_names:
                    removidas = job_dir / "_removidas"
                    removidas.mkdir(exist_ok=True)
                    shutil.move(str(old_img), str(removidas / old_img.name))

    authorized_images = []
    for img_str in images:
        src_img = Path(img_str).resolve()
        if not src_img.is_file():
            raise FileNotFoundError(f"Imagem enviada não encontrada: {src_img}")
        dst_img = assets_dir / src_img.name
        if src_img != dst_img.resolve():
            shutil.copy2(src_img, dst_img)
        authorized_images.append(
            {
                "arquivo": f"assets/{dst_img.name}",
                "sha256": sme._sha256_file(dst_img),
            }
        )

    plan = sme.build_editing_plan(
        niche=niche,
        reel_format=reel_format,
        title=title or video_path.stem.replace("_", " "),
    )

    plan_file = job_dir / "socialmedia_plan.json"
    payload = {
        "video_origem": info,
        "imagens_autorizadas": authorized_images,
        "plano_socialmedia": plan,
        "pasta_projeto": str(job_dir),
        "saida_rascunho_esperada": str(job_dir / f"RASCUNHO_{video_path.stem}.mp4"),
    }
    plan_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace")

    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    parser = argparse.ArgumentParser(description="Ingestão e preparo de arquivo MP4 para edição SocialmedIA")
    parser.add_argument("video", nargs="?", default=None, help="Caminho do .mp4 (ou vazio para pegar o mais recente de entrada_mp4/)")
    parser.add_argument("--niche", default="varejo", help="Nicho empresarial (ex: varejo, supermercado, clinica, material_construcao, industria, restaurante, escritorio, ecommerce)")
    parser.add_argument("--format", default="desafio_orcamento", help="Formato do Reel")
    parser.add_argument("--title", default="", help="Título/Gancho principal")
    parser.add_argument("--images", nargs="*", default=[], help="Imagens exclusivas enviadas pelo usuário para este vídeo (máx. 2)")
    args = parser.parse_args()

    try:
        video_path = find_latest_mp4(args.video)
        result = prepare_socialmedia_job(
            video_path=video_path,
            niche=args.niche,
            reel_format=args.format,
            title=args.title,
            images=args.images,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
