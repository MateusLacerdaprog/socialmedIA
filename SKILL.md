---
name: socialmedia
description: Sistema de edição, retenção, posicionamento empresarial e copywriting para Instagram Reels e Posts, guiado pelo Instagram Viral Editing Playbook (medido em 27 Reels virais) e executado nos motores locais editonny, HyperFrames, EffectCraft e FFmpeg. Use quando o usuário pedir para editar vídeos para Instagram, criar Reels empresariais, analisar retenção/viralidade, gerar legendas por nicho, definir hooks, escolher cortes/zoom/tipografia ou posicionar uma marca no Instagram.
---

# SocialmedIA — edição de Reels empresariais para Instagram

## 1. Objetivo e escopo

Transformar um vídeo bruto (ou um pedido de conteúdo) num **RASCUNHO** de Reel 1080×1920 e na legenda do post, com
decisões técnicas tiradas do [PLAYBOOK.md](PLAYBOOK.md) e da medição de 27 Reels virais de empresas (conclusões já no PLAYBOOK; o detalhe por conta fica em
`terceiros/medicao-2026-10/`, só na máquina).
**Quando um número medido contradiz outro arquivo, vale o medido.**

Fora do escopo: publicar, curtir, comentar ou seguir no Instagram; escrever texto pelo cliente; prometer views
(retenção e alcance dependem também de conteúdo, público e distribuição).

## 2. Entradas esperadas

| Entrada | Obrigatória | Observação |
|---|---|---|
| Vídeo (`.mp4`) | sim | caminho no chat ou o mais recente de `entrada_mp4/` |
| Nicho | sim | `varejo`, `saude`, `industria`, `material_construcao`, `gastronomia`, `servicos`, `educacao`, `ecommerce`, `empresas_locais` (apelidos: `supermercado`, `clinica`, `odontologia`, `restaurante`, `escritorio`…) |
| Tipo de Reel | não | `montagem_criador`, `fala_continua`, `produto_sem_fala`, `personagem_ia`; sem ele vale o padrão do nicho |
| Textos (gancho, títulos, CTA, hashtags) | sim, do cliente | ou palavras ditas na gravação; nunca do agente |
| Imagens do vídeo | não | só as enviadas para ESTE vídeo (máx. 2 momentos, salvo pedido) |
| Tipo de conta | para memes | `empresa` ou `pessoal_sem_receita` |

## 3. Pré-requisitos

- Python 3.9+, FFmpeg/ffprobe no PATH.
- **editonny** em `~/.local/share/editonny` (corte, legenda, cenas, render) com `uv`; HyperFrames é chamado por ele.
- **EffectCraft** 0.10+ (`effectcraft-cli.exe`) para os gráficos de [effectcraft/](effectcraft/SKILL.md). Opcional.
- `faster-whisper` + `soundfile` só para remedir Reels de referência.

`<SOCIALMEDIA>` = pasta deste `SKILL.md` (resolva links/junções). Pasta de trabalho (`entrada_mp4/`,
`memes_cortados/`, `projetos/`) = variável `SOCIALMEDIA_DIR` ou a pasta atual. Faltou um pré-requisito: diga qual e
continue nas etapas que não dependem dele.

## 4. Ferramentas

| Comando | Faz |
|---|---|
| `python <SOCIALMEDIA>/scripts/receber_mp4.py [VIDEO] --niche N --title T --images A B` | cria `projetos/socialmedia_<video>/` com `assets/` isolado + `socialmedia_plan.json` |
| `python <SOCIALMEDIA>/scripts/socialmedia_engine.py plan --niche N --title T [--tipo X]` | plano: `project.json` do editonny, legenda medida (`legenda_empresa`), gancho, áudio |
| `… socialmedia_engine.py caption --niche N --hook H --bullets … [--keyword K --hashtags …]` | monta e valida a legenda do post (sai 1 se inválida) |
| `… socialmedia_engine.py audit <edl.json> --tipo X` | confere o EDL contra o tipo de Reel |
| `… socialmedia_engine.py audit-project <proj/> --tipo X` | portão: imagem reutilizada, nº de imagens, transições, cortes |
| `… socialmedia_engine.py meme --niche N --intent I --conta C` | meme seguro (ou remix encenado em conta de empresa) |
| `… socialmedia_engine.py verificar RASCUNHO_x.mp4` | portão do vídeo exportado: 1080×1920, fps, codecs, sincronia, −14 LUFS ±0,5, pico ≤ −1,5 dBTP |
| `python <SOCIALMEDIA>/effectcraft/ec_grafico.py …` | título/texto animado/contador/círculo/flash em WebM transparente |
| `python <SOCIALMEDIA>/scripts/medir_reels.py <pasta>` | mede Reels de referência baixados (cortes, loudness, silêncio, fala); grave a saída em `terceiros/` |
| `python <SOCIALMEDIA>/scripts/verificar_terceiros.py` | regra do repositório: nada de terceiros versionado (também roda no `pre-commit`) |
| helpers do editonny (`transcribe_batch`, `pack_transcripts`, `noise_check`, `align_words`, `face_layout`, `sound_plan`) | via `uv run --directory "~/.local/share/editonny/engine" python helpers/<nome>.py …` |

Estilos por nicho (cores, tipografia, ritmo, zoom, zonas seguras) e catálogo de memes ficam em `presets/*.json`;
para ajustar um estilo, edite o JSON e rode os testes.

Conhecimento por assunto (leia só o módulo da etapa): [01 hooks](modules/01-hooks.md) ·
[02 legendas por nicho](modules/02-legendas-por-nicho.md) · [03 tipografia e gráficos](modules/03-tipografia-e-elementos-graficos.md) ·
[04 cortes, zoom, câmera e áudio](modules/04-cortes-zoom-camera-audio.md) · [05 storytelling e CTA](modules/05-storytelling-e-cta.md) ·
[06 posicionamento por empresa](modules/06-posicionamento-empresarial.md) · [07 educativo × vendas](modules/07-reels-educativos-e-vendas.md) ·
[08 memes](modules/08-memes-cortados-e-insercao.md) · material de apoio local (de terceiros) em `terceiros/`, se existir.

## 5. Procedimento

**Passo 1 — Diagnóstico.** Defina nicho e **tipo de Reel** (PLAYBOOK §0); antes de editar, pergunte se cabe
**colaboração** (criador local, série numerada, evento): pelo menos 15 dos 27 virais medidos eram colab.

| Tipo | Plano | Corta pausas | Plano mais longo |
|---|---|---|---|
| `montagem_criador` (varejo, construção, gastronomia, indústria, e-commerce) | `0,8–1,6 s` | `≥ 0,35 s`, erros, bastidor (*"vem cá"*) | `≤ 8 s` |
| `fala_continua` (saúde, serviços, educação, empresa local) | blocos de `4,0–12,0 s`, 5 a 8 no vídeo | só entre parágrafos `≥ 0,65 s`; `"dry": false` | `≤ 37 s`, com texto em movimento acima de `8 s` |
| `produto_sem_fala` | `4–5 s` | — | `≤ 10 s` |
| `personagem_ia` (Argon) | `~1,7 s` | — | só com Gemini Pro/Enterprise (`--plano-gemini`) |

Rode `receber_mp4.py` (ou `plan`). Estilo do editonny por nicho: varejo/construção/gastronomia → `amber`;
saúde/serviços/educação → `paper` (`maxWords: 3`); indústria/e-commerce → `night`. Cores e zoom vêm do plano.

**Passo 2 — Transcrição e corte (editonny).** `transcribe_batch --language pt`, `pack_transcripts`, `noise_check`.
No `edl.json`: primeira palavra em `≤ 0,40 s` (o auditor tolera `0,45 s` pela imprecisão da transcrição);
`"jcut": {"lead_frames": 4, "tail_trim_frames": 2}`; em `fala_continua` nunca `"dry": true` nem picotar respiros
internos de `0,25–0,55 s`, e cubra 1 a 2 emendas com as imagens para restarem 3 a 4 cortes secos visíveis.

**Passo 3 — Direção visual (1080×1920).** `align_words` e `face_layout` sobre o `cut.mp4` definitivo.
- **Imagens (`scene: "evidence"`):** 2 momentos (dor/contexto `~4,5–8,5 s`; mecanismo/prova `~20–25 s`), `fit: "contain"`
  no card `x=50, y=520, w=980, h=654` (raio 36). **Toda imagem entra e sai com transição**: `transition-zoom` em
  `início ± 0,25 s` e `transition-glow` em `fim ± 0,20 s` (`overContent: true`), zoom no bloco
  `"zooms": [{"at": início, "end": fim, "scale": 1.10, "ease": "power2.out", "sound": "whoosh"}]` (formato do
  `build.py`: sem `at` o build falha) e sons pelo `sound_plan.py` (`whoosh`, `photo`, `pop`). Nunca imagem estática em corte seco.
- **Zonas seguras:** gancho em `y = 230–260` por `3–8 s` (editonny ou `ec_grafico.py titulo`); `counter` em
  `[330, 1170]`, `stamp` em `[230, 1150]`; legenda do editonny `standard`, `maxWords 3`, `y = 1380–1400`
  (`1290` durante `evidence`); legenda ASS própria de empresa: campo `legenda_empresa` do plano (44 px, caixa normal,
  `y = 1360`, no máximo 1 palavra de destaque por frase). Nada abaixo de `y = 1530`; ícones em `x = 920–1080`.
- **Encerramento:** anúncio de marca = cartão de `0,8–1,2 s` com logo + 1 CTA; criador/série = termina na última fala;
  saúde = responsável técnico + CRO/CRM na tela.
- **Memes:** só pelo comando `meme`. Conta de empresa nunca usa o clipe (recebe a reação encenada); saúde nunca usa meme.

**Passo 4 — Áudio.** Voz a `−14 LUFS` integrado, pico `≤ −1,5 dBTP`, música com ducking a `−26 dB` sob a fala
(cadeia no campo `audio_dsp_spec` do plano). Nunca `zoompan` no FFmpeg: use `perspective` ou o zoom do editonny.

**Passo 5 — Render e portões.** `audit-project` → render → copie a saída para `RASCUNHO_<nome>.mp4` → `verificar` →
quadros das transições/imagens com FFmpeg, olhados em tamanho real (português, zonas seguras, legibilidade).

**Passo 6 — Legenda do post.** `caption` com o texto do cliente: linha 1 `≤ 125` caracteres que não repete a
primeira fala; corpo escaneável (itens/preços ou 3 pontos); **um CTA só** (palavra-código **ou** envio por DM; nos
virais o fecho mais comum é uma pergunta); localização + no máximo 5 hashtags. Se o JSON trouxer `defaults_used`,
confirme a palavra-código e as hashtags com o cliente.

## 6. Critérios de decisão

- Tipo de Reel decide o ritmo; o nicho só dá o padrão.
- Medido (`[MEDIDO]` no PLAYBOOK) > `[OBSERVADO]` > hipótese. Marque hipótese como hipótese.
- Na dúvida entre mais cortes e menos cortes em fala de especialista: menos.
- Regras de plataforma são do Instagram; não aplique TikTok/Shorts sem dizer que é adaptação.

## 7. Regras de segurança

1. **RASCUNHO antes do FINAL:** nada sai como `FINAL_` sem o usuário assistir e aprovar.
2. **Sem invenção:** títulos, contadores, selos e legendas só com palavras faladas (confirmadas na transcrição) ou
   dados do cliente. Nunca invente preço, depoimento, estatística ou promessa clínica.
3. **Instagram só leitura** no navegador: nunca publicar, curtir, comentar ou seguir.
4. **Imagens isoladas por vídeo:** nunca reutilizar imagem de projeto anterior (`audit-project` compara SHA-256).
   Imagens trocadas vão para `_removidas/`, nunca são apagadas.
5. **Direitos:** clipe de TV/celebridade não entra em conta de empresa. IA (Argon, para mascote da marca ou plano
   impossível de filmar) nunca imita pessoa real, é rotulada como IA e só gera depois que o usuário aprova o roteiro.
6. **Nada de terceiros no Git** (o repositório é público): vídeos, quadros, áudios, prints, transcrições, textos ou
   código de outros autores, perfis/IDs/links/números de contas específicas e dados de clientes ficam **só na máquina**
   (`terceiros/`, `projetos/`, `memes_cortados/`). Sobe só o que é próprio: código, regras e conclusões com números
   agregados sem identificar contas. Nada de chave, e-mail ou caminho pessoal. `verificar_terceiros.py` bloqueia o commit.

## 8. Validação dos resultados (pronto = tudo verde)

- `audit-project` com `passed_all: true`;
- `verificar` com `valido: true` no `RASCUNHO_*.mp4`;
- quadros revisados a olho (texto, zonas seguras, transições);
- `caption` com `valid: true` e padrões confirmados com o cliente.

## 9. Tratamento de erros

| Sintoma | Ação |
|---|---|
| `erro: Nicho '…' desconhecido` | use um dos nichos listados na mensagem |
| `Excesso de imagens` | peça ao usuário quais 2 momentos ficam, ou use `--max-images` se ele pediu mais |
| `audit-project` reprova imagem reutilizada | troque pela imagem enviada para este vídeo |
| `verificar` reprova loudness/pico | rode a 2ª passada do `loudnorm` (medição + `measured_*`) e verifique de novo |
| build do editonny: `missing "at"` | o zoom precisa de `at`/`scale` (Passo 3) |
| EffectCraft ausente | use as cenas do editonny para o gráfico e avise |

## 10. Formato de saída

Para o usuário: caminho do `RASCUNHO_*.mp4`, os quadros revisados, o resultado dos portões (o que passou e o que
ficou como aviso) e a legenda do post pronta para colar. Arquivos do projeto em
`projetos/socialmedia_<video>/` (`socialmedia_plan.json`, `proj/`, `edit/`).

## 11. Quando parar ou perguntar

Pergunte antes de seguir se faltar: o texto do gancho/CTA, o nicho, as imagens de um momento, ou a autorização para
usar um meme. Pare e mostre o RASCUNHO quando os portões do item 8 passarem; o FINAL só com aprovação.
