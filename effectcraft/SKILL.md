---
name: effectcraft
description: Gráficos de motion (títulos com pop, texto animado por letra/palavra, contador, círculo "olha aqui", flash de corte) feitos no EffectCraft — motor local estilo After Effects, open source — como vídeo transparente 9:16 para sobrepor ao Reel. Parte da SocialmedIA.
---

# effectcraft (motion graphics da SocialmedIA)

**Objetivo:** gerar um WebM VP9 1080×1920 **com transparência** (`alpha_mode=1`) para sobrepor ao vídeo do Reel.
Não edita o vídeo: só cria a camada.

**Pré-requisitos:** EffectCraft 0.10+ (`C:\Program Files\EffectCraft`, licença MIT OR Apache-2.0; outro caminho via
variável `EFFECTCRAFT_CLI`), FFmpeg/ffprobe no PATH, Python 3.9+.

## Uso

```bash
python <SOCIALMEDIA>/effectcraft/ec_grafico.py receitas
python <SOCIALMEDIA>/effectcraft/ec_grafico.py quadros --receita titulo --texto "<do usuário>" --saida previa.png
python <SOCIALMEDIA>/effectcraft/ec_grafico.py gerar --receita titulo --texto "<do usuário>" --duracao 2.5 --saida titulo.webm
python <SOCIALMEDIA>/effectcraft/ec_grafico.py gerar --receita circulo --x 700 --y 820 --raio 150 --saida circulo.webm
```

Receitas: `titulo` (pop com overshoot), `texto` (`--animacao typewriter|fadeUpCharacters|bounceInWords|trackingIn|scramble|blurIn|jitter|dropInLines`),
`contador` (`--de --ate --sufixo`), `circulo` (desenha em volta de `--x --y`), `flash` (0,3–1 s, cobre a tela).
Opções: `--cor #RRGGBB` (padrão `#FFDE00`), `--tamanho`, `--x`, `--y` (padrão 230 = faixa do gancho), `--duracao`.

## Motion automático na edição

O `scripts/editar_reel.py` usa estas receitas sozinho, **só com palavras ditas** (transcrição do corte): abertura
(título dado e dito, ou o começo da 1ª frase), pergunta curta falada (`texto`, amarelo), número falado (`contador`),
fechamento (fim da última frase) e `flash` em cada emenda de corte. Títulos longos quebram em 2 linhas sem deixar
artigo/preposição no fim da linha; mínimo de 1,8 s na tela, sem sobreposição, y = 250 (acima do rosto e da legenda).

## Sobrepor ao vídeo (FFmpeg)

O decodificador nativo do FFmpeg ignora a transparência do VP9: declare `-c:v libvpx-vp9` **antes** do `-i` do gráfico.
Exemplo com o gráfico entrando aos 1,5 s:

```bash
ffmpeg -i video.mp4 -c:v libvpx-vp9 -i titulo.webm -filter_complex "[1:v]setpts=PTS-STARTPTS+1.5/TB[g];[0:v][g]overlay=0:0:eof_action=pass[v]" -map "[v]" -map 0:a -c:a copy RASCUNHO_video.mp4
```

No editonny/HyperFrames, use o WebM como vídeo de camada sobre o corte (mesmo tamanho do quadro).

## Regras

1. **Texto é sempre do usuário ou falado na gravação.** Peça o texto; o script recusa `titulo`/`texto` sem `--texto`.
   Revise o português com os quadros em tamanho real.
2. **Posição** (PLAYBOOK): gancho em `y = 230–260`; nada na faixa da legenda de fala (`y ≈ 1290–1420`) nem abaixo de
   `y ≈ 1530`; coluna de ícones do Reels em `x = 920–1080`.
3. **Revise antes de usar:** rode `quadros` (início/meio/fim sobre cinza) e olhe a imagem. O vídeo montado sai como
   `RASCUNHO_*` até a aprovação do usuário.
4. **Saída válida** = 1080×1920, alfa e duração pedida (±0,2 s). O script confere com ffprobe e falha se não bater.

## Erros comuns

- `EffectCraft não encontrado`: instale ou defina `EFFECTCRAFT_CLI`.
- Texto longo demais (>60 caracteres): recusado. O título encolhe sozinho até caber em 960 px.
- Gráfico preto no vídeo final: faltou `-c:v libvpx-vp9` antes do `-i` do WebM.

## Armadilhas do EffectCraft (descobertas testando)

- Em camada de forma, `layer.property("Position")` pega o transform do **grupo** interno. Use
  `layer.property("Transform").property("Position")`.
- Presets de texto não estão no JSX: aplique com `run layer.applyTextPreset '{"layer":"T","preset":"..."}' --save`.
- Expressão em `Source Text` funciona (`linear(time, ...)`), mas monte a string inteira e escape uma vez só.
- `render-frame` sem `--transparent` mostra fundo preto; o WebM sai com alfa mesmo assim.
- Efeitos além das receitas: JSX com o modelo AE (`effectcraft-cli script X.jsx --empty --save-as P.ecproj`) e
  `render --project P.ecproj --comp G --format webm --channels rgba --audio off`. Lista de efeitos:
  `effectcraft-cli exec effect.list --params '{"filter":"glow"}' --empty`.
