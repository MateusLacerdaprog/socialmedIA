# Arquitetura da SocialmedIA

Estado em 28/10/2026. A SocialmedIA é independente: não importa nem lê nada de outro
projeto. Os motores pesados ficam fora do repositório e são chamados por linha de comando.

## Módulos

| Responsabilidade | Onde | Observação |
|---|---|---|
| Orquestração (o que fazer, em que ordem, quando parar) | `SKILL.md` | o próprio agente; sem subagentes, as etapas dependem umas das outras |
| Conhecimento (regras medidas) | `PLAYBOOK.md`, `modules/` | medido > observado > hipótese; detalhe por conta só local em `terceiros/` |
| Estilos e presets (cores, tipografia, ritmo, zoom, zonas, memes) | `presets/nichos.json`, `presets/memes.json` | editáveis sem Python; validados ao carregar (`PresetInvalido` diz o nicho e o campo) |
| Regras executáveis por nicho e tipo de Reel | `scripts/socialmedia_engine.py` (`REEL_TYPES`, `EVIDENCE_RULES`, plano, auditorias) | determinístico, sem IA |
| Ingestão segura | `scripts/receber_mp4.py` | `assets/` isolado por vídeo; troca vai para `_removidas/` |
| Edição audiovisual | editonny (`~/.local/share/editonny`) + HyperFrames | corte, legenda, cenas, câmera, render |
| Motion graphics avulso | `effectcraft/ec_grafico.py` + EffectCraft | WebM transparente para sobrepor |
| Portões de qualidade | `audit`, `audit-project` (projeto) e `verificar` / `scripts/qualidade.py` (arquivo final) | código de saída 1 reprova |
| Medição de referências | `scripts/medir_reels.py` | FFmpeg + faster-whisper; vídeos e medidas de terceiros fora do Git |
| Regra “nada de terceiros” | `scripts/verificar_terceiros.py` + hook `pre-commit` + teste | lista de nomes bloqueados é local (`terceiros/nomes_bloqueados.txt`) |
| Testes | `tests/` (`-m "not lento"` = ciclo rápido) | golden do plano dos 9 nichos |

Fluxo: `receber_mp4` → `plan` → editonny (transcrição, EDL, `project.json`) → `audit-project` → render →
`RASCUNHO_*.mp4` → `verificar` → quadros → `caption` → aprovação do usuário.

## Matriz de compatibilidade dos gráficos

| Recurso | editonny (cenas, 145) | EffectCraft (`ec_grafico.py`) | Decisão |
|---|---|---|---|
| Título do gancho | `text-bold-title`, `text-two-line-title`, `headline`… | `titulo` (pop com overshoot) | **Manter os dois**: dentro do build do editonny use a cena; vídeo editado fora dele, o EffectCraft |
| Texto animado por letra/palavra | parte dos 19 de “Captions and titles” | `texto` (8 presets: typewriter, scramble, blurIn…) | **Manter** o EffectCraft: presets por letra que o catálogo não cobre igual |
| Contador | `revenue-counter`, `time-counter`, `counter` (animação) | `contador` | **Preferir o editonny** no build (casa com a timeline); EffectCraft só fora dele |
| Círculo / apontador | `pointer-circle` + 16 apontadores | `circulo` | **Preferir o editonny**; o `circulo` fica para overlay avulso |
| Flash / transição | `transition-flash`, `transition-glow`, `transition-zoom` | `flash` | **Preferir o editonny** (as transições obrigatórias das imagens já são dele) |
| Efeitos além das receitas | 13 “Video effects” | 307 efeitos via JSX | EffectCraft quando o efeito não existir no catálogo |

Nada foi descontinuado: as receitas do EffectCraft são trabalho próprio e servem ao caso “sem editonny”.

## Origem e licenças

| Componente | Origem | Licença | Como entra |
|---|---|---|---|
| `SKILL.md`, `PLAYBOOK.md`, `modules/`, `scripts/`, `effectcraft/`, `tests/` | próprio | do autor do repositório | código e texto originais |
| material de apoio em `terceiros/` (textos adaptados de skills MIT, medições de contas) | terceiros | variada | **só na máquina**, nunca no Git |
| editonny | Matheus Gomes | MIT | instalado à parte, chamado pela CLI; nada copiado |
| EffectCraft | The EffectCraft contributors | MIT OR Apache-2.0 | instalado à parte, chamado pela CLI |
| HyperFrames | chamado pelo editonny | **não confirmada** (as skills instaladas não trazem licença) | não é redistribuído |
| `memes_cortados/` + `terceiros/memes.json` | trechos de TV/internet | **sem licença** | só na máquina; conta de empresa nunca usa o clipe |

## Medições (verificáveis, não estimadas)

| Métrica | Antes | Depois |
|---|---|---|
| Testes automatizados | 0 | 158 (ciclo rápido < 1 s; suíte toda ~15 s) |
| Tamanho do motor (`socialmedia_engine.py`) | 1.220 linhas | ~840 linhas (dados foram para `presets/`) |
| `audit-project` relendo imagens já vistas | todas, toda vez | só as novas ou alteradas (cache por tamanho + mtime) |
| Saída do `plan` nos 9 nichos | referência gravada antes das mudanças | idêntica, exceto as mudanças intencionais listadas abaixo |
| Render de um gráfico de 2 s no EffectCraft | — | ~17 s nesta máquina (RTX 4050) |
| Portão do arquivo final | nenhum | `verificar` (resolução, fps, codecs, sincronia, LUFS, pico, tela preta, nome) |

## Mudanças de 28/10/2026

1. Separação do editor de gameplay em que a skill nasceu (código, docs, `SOCIALMEDIA_DIR`); skill instalada por junção no usuário.
2. **Perda de dados corrigida:** `receber_mp4.py` apagava imagens antigas (e antes de validar as novas).
3. **Validador que mentia corrigido:** a legenda cortava o gancho > 125 e então dizia que estava ok.
4. **Instrução que quebrava o build corrigida:** zoom em `{at, end, scale}` (o `{start, zoom}` do SKILL.md antigo falhava no editonny).
5. Contradições unificadas: pausa de parágrafo 0,65 s; bloco 4,0–12,0 s; 1ª palavra ≤ 0,40 s (auditor tolera 0,45 s).
6. Novo: `verificar`, testes, mensagens de erro de uma linha, `canonical_niche()` único.
7. Presets em JSON validados e cache de hash no `audit-project` (saída do `plan` idêntica: golden).

Mudanças de saída do `plan`: saíram os dois campos de legenda do editor antigo (`*_caption_preset`,
`caption_*_xy`); o campo da legenda de empresa virou `legenda_empresa`; `evidence_rules.require_zoom_motion` virou `{scale: 1.1, ease: power2.out}`.

## Próximas melhorias (não feitas)

| Prioridade | Melhoria | Problema que resolve | Custo | Risco |
|---|---|---|---|---|
| P2 | Comando `render` que chama o editonny e já roda `verificar` | menos passos manuais | médio | médio (depende da CLI do editonny) |
| P3 | `verificar` com OCR das zonas seguras | hoje texto fora da zona só é pego a olho | alto | médio |
| P3 | Comparação visual entre versões (folha de quadros A×B) | revisar ajuste rápido | baixo | baixo |
| P3 | Fecho com métricas do Instagram (CSV) por tipo de Reel | validar as regras com resultado real | médio | dados pequenos dão conclusão fraca |
