import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "effectcraft"))

TEM_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def pytest_configure(config):
    config.addinivalue_line("markers", "lento: usa FFmpeg ou o EffectCraft (ciclo rápido: -m 'not lento')")


def cli(*args, env=None):
    """Roda o motor como o agente roda (subprocesso) e devolve (código, JSON)."""
    r = subprocess.run([sys.executable, "-I", str(RAIZ / "scripts" / "socialmedia_engine.py"), *map(str, args)],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip().startswith("{") else r.stderr)


def video_teste(caminho: Path, s="1080x1920", r=30, d=2.0):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=s={s}:r={r}:d={d}",
                    "-f", "lavfi", "-i", f"sine=d={d}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-shortest", str(caminho)], check=True)
    return caminho


requer_ffmpeg = pytest.mark.skipif(not TEM_FFMPEG, reason="FFmpeg não instalado")
