# SocialmedIA

Skill para criar **agentes de IA editores de vídeo**. A ideia é resolver um problema comum de pequenas e médias empresas: editar vídeos para redes sociais (Instagram Reels) sem equipe nem software especializado.

O agente transforma um pedido ("edita esse vídeo para o Instagram da loja") em decisões técnicas de edição: gancho dos primeiros segundos, cortes, zoom, tipografia, legendas por nicho, áudio e chamada para ação. Essas decisões partem de medições de Reels reais de empresas.

## Como funciona

- `SKILL.md`: instruções do agente (formato de skill do Claude Code).
- `PLAYBOOK.md`: medidas de edição (pixels, tempos, zoom, áudio em -14 LUFS).
- `modules/`: ganchos, legendas por nicho, tipografia, cortes/zoom/áudio, storytelling e CTA, posicionamento por tipo de empresa, Reels educativos e de vendas, memes.
- `scripts/medir_reels.py`: mede Reels de referência baixados (FFmpeg + faster-whisper). As conclusões da medição de 27 Reels estão no PLAYBOOK; os dados por conta ficam só na máquina.
- `scripts/socialmedia_engine.py`: motor de regras em Python (`plan`, `caption`, `audit`, `audit-project`, `meme`, `verificar`).
- `scripts/qualidade.py`: portão do vídeo exportado (resolução, fps, codecs, sincronia, −14 LUFS, pico).
- `effectcraft/`: gráficos de motion em WebM transparente feitos no EffectCraft.
- `tests/`: testes automatizados. Arquitetura, licenças e próximos passos em [ARQUITETURA.md](ARQUITETURA.md).
- `scripts/editar_reel.py`: **caminho principal** — do vídeo bruto ao `RASCUNHO_*.mp4` verificado (editonny + HyperFrames + motion do EffectCraft + portões), em etapas com cache.
- `scripts/receber_mp4.py`: recebe um MP4 numa pasta de entrada e gera o plano de edição.

Os motores de edição (editonny, HyperFrames, o programa EffectCraft e o FFmpeg) ficam fora deste repositório; a skill `effectcraft/` (script que gera os gráficos de motion no EffectCraft) vem junto. A pasta de trabalho (`entrada_mp4/`, `memes_cortados/`, `projetos/`) é a definida em `SOCIALMEDIA_DIR` ou a pasta atual.

```bash
python scripts/socialmedia_engine.py --help
python -m pytest tests -q                  # suíte toda (precisa de FFmpeg; o render real precisa do EffectCraft)
python -m pytest tests -q -m "not lento"   # ciclo rápido, sem FFmpeg
```

## Créditos

## Regra: nada de terceiros no Git

O repositório é público. Vídeos, quadros, áudios, prints, transcrições, textos ou código de outros autores, perfis,
IDs, links e números de contas específicas e dados de clientes **nunca** são versionados: ficam na pasta local
`terceiros/` (ou em `projetos/`, `memes_cortados/`), todas no `.gitignore`. Instale o bloqueio uma vez por clone:

```bash
python scripts/verificar_terceiros.py --instalar-hook
```

Programas usados e licenças: [TERCEIROS.md](TERCEIROS.md).
