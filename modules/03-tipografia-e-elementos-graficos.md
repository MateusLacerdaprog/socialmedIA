# Módulo 03 — Tipografia, Posicionamento e Elementos Gráficos (`1080×1920`)

> **Base Empírica (`[OBSERVADO]`):** Medições diretas em quadros de vídeos de clientes (fora do repositório) e no código do `editonny`.

---

## 1. Especificação Reproduzível de Tipografia

### 1.1. Padrão de Pixels, Contorno, Sombra e Permanência (`1080×1920`)

| Elemento | Tamanho (`px`) | Peso | Caixa Alta | Cor Texto | Contorno (`Stroke`) | Sombra (`Shadow`) | Transparência | Permanência |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gancho Impacto** | **`90 px`** (`88–108 px`) | `900` (Black) | Sim (`ALL CAPS`) | `#FFFFFF` / Destaque `#FFDE00` | `8 – 10 px` `#000000` | `25% – 40%` (`4 px` offset) | `0%` (Opaco `100%`) | `1,5 s – 3,0 s` |
| **Gancho Pílula Topo** | **`58 px`** (`52–64 px`) | `800` (ExtraBold) | Não (`Sentence`) | `#1A1A2E` ou `#FFFFFF` | `0 px` (dentro de box) ou `7 px` | `25%` (`18 px` blur) | Box `5%` (`95%` opaco) | `3,0 s – 8,0 s` |
| **Subtítulo / Apoio** | **`58 px`** (`54–60 px`) | `700` (Bold) | Não (`Sentence`) | `#FFFFFF` | `6 px` `#000000` | `25%` (`2 px` offset) | `0%` (Opaco `100%`) | `1,8 s – 3,5 s` |
| **Legenda de fala de empresa (padrão)** `[MEDIDO n=14]` | **`40 – 48 px`** | `600 – 700` | Não (`Sentence`) | `#FFFFFF`; 1 palavra de destaque na **cor da marca** | `0 – 2 px` | suave (`2 px`) | `0%` | frase curta, 1–2 linhas, centro `y = 1330 – 1400` |
| **Legenda palavra por palavra** `[MEDIDO n=3]` | **`55 – 65 px`** | `800` | Sim, ou pílula preta | `#FFFFFF` + palavra-chave na cor da marca | `0 px` | — | pílula `#000000` | 1 palavra por vez |
| **Palavra-chave gigante (cinética)** `[MEDIDO n=3]` | **`150 – 260 px`** | `900` | livre | cor da marca | — | — | sem fundo | 1–2 palavras, centro `y = 860 – 1000` |
| **Legenda Karaokê (Corpo)** — estilo de entretenimento/gameplay; **0 de 27 Reels de empresa usam** `[MEDIDO n=27]` | **`88 px`** (`ASS`) / **`68 px`** (`HTML`) | `900` (Black) | Sim (`ALL CAPS`) | Corpo `#FFFFFF` / Ativa **`#FFDE00`** | `7 px` `#000000` | `25% – 50%` (`2 px`) | Palavra inativa `0%` (ou `15%` dim) | `0,6 s – 1,8 s` (máx. 3–5 palavras) |
| **Contador (`counter`)** | **`92 px`** (valor) / **`44 px`** (`R$`) | `900` (Black) | Sim (`R$`) | Valor `#FFFFFF` / `R$` `#FF6B00` | Borda card `2 px` `#FF8800` | `50%` (`24 px` blur) | Card `8%` (`92%` opaco `#121318`) | Acumulativo (`0,6s` roll-up) |
| **Selo Final (`stamp`)** | **`64 px`** | `900` (Black) | Sim (`ALL CAPS`) | `#FFFFFF` | Borda `4 px` `#22C55E` | `40%` (`12 px` blur) | Fundo `5%` (`95%` `#16A34A`) | `3,0 s – 6,5 s` |

---

## 2. Posicionamento Espacial e Animações de Entrada/Saída

### 2.1. Coordenadas Exatas e Alinhamentos (`1080×1920`)
1. **Título / Gancho Superior (`Hook Header`)**:
   - **Coordenada `(X, Y)`**: `X = 540` (alinhamento central `text-align: center`), **`Y = 230 a 260 px`**.
   - **Margens Laterais**: `X_min = 100 px`, `X_max = 980 px` (largura útil `880 px`).
   - **Animação de Entrada**: `scale(0.88) -> scale(1.00)` + `opacity(0 -> 1)` em **`180 ms` (`0,18 s`)** com curva `cubic-bezier(0.22, 1, 0.36, 1)` (`back.out(1.4)` no GSAP).
   - **Animação de Saída**: `opacity(1 -> 0)` + `translateY(-12px)` em **`150 ms` (`0,15 s`)**.

2. **Card de Contador / Soma Progressiva (`counter`) `[OBSERVADO — cliente]`**:
   - **Coordenada `(X, Y)`**: **`X = 330 px, Y = 1170 px`** (ancorado à direita para não cobrir o produto na mão esquerda do apresentador, como visto em `q1.png`–`q8.png`).
   - **Animação de Entrada**: Slide horizontal da direita (`translateX(120px -> 0)`) em **`220 ms`** + interpolação numérica (`countUp`) de **`600 ms` (`0,60 s`)**.

3. **Legendas Sincronizadas (`Captions`)**:
   - **Modo `editonny` (`captions.style = "standard"`, `maxWords = 3`)**:
     - `X = 540 px`, **`Y = 1350 a 1400 px`** (validado por `face_layout.py` quando o rosto está no terço superior `y < 850 px`).
   - **Medido nos Reels virais de empresa** `[MEDIDO n=14]`:
     - Centro da legenda de fala entre **`y = 1310` e `1500`**, mediana **`~1385`** (72 % da altura).
     - **Nada abaixo de `y ≈ 1530`**: um Reel de fast-food com legenda a `y ≈ 1575` ficou sob a descrição do post.
     - Legenda ASS própria: fonte `44 px`, caixa normal, contorno `2 px`, sombra `2 px`, texto `#FFFFFF`, destaque na cor da marca, `y = 1360` (campo `legenda_empresa` do `plan`).
   - **Elementos fixos observados** `[OBSERVADO]`:
     - logo pequeno no canto superior (`y ≈ 100–140`, `~120–160 px` de largura) — varejo e educação;
     - caixa branca fixa com o gancho/prazo (`y ≈ 1480`, texto preto `~60 px`) o vídeo inteiro — escritório contábil (85×);
     - título de série com número do episódio no topo (`y ≈ 380–440`, `~90 px`, contorno) — material de construção (43×);
     - crédito (nome + cargo) em caixa da cor da marca (`y ≈ 1000–1250`) — indústria e educação;
     - **em saúde**, responsável técnico + CRO/CRM fixo na borda — rede de clínicas.
   - **Animação da Palavra Ativa**: Transição instantânea de cor `#FFFFFF -> #FFDE00` (`\kf` no ASS ou classe `.active` com `scale(1.06)` no `editonny`).

---

## 3. Catálogo de Elementos Gráficos e Overlays (`editonny` + `effectcraft`)

| Elemento Gráfico | Ferramenta / Cena | Posição Padrão `(X, Y)` | Duração | Quando Usar Automaticamente |
| :--- | :--- | :---: | :---: | :--- |
| **Caixa / Pílula de Hook** | `editonny` (`headline`/`badge`) ou `ec_grafico.py titulo` | `(540, 230)` | `3,0 s – 8,0 s` | Sempre nos primeiros `3,0 s` para ancorar o tema do vídeo. |
| **Contador Monetário (`counter`)** | `editonny` (`type: "counter"`) ou `ec_grafico.py contador` | `(330, 1170)` ou `(540, 230)` | `0,6 s` roll-up + hold | Em desafios de orçamento, somas de carrinho, comparativos de economia ou métricas de estoque. |
| **Selo de Conclusão (`stamp`)** | `editonny` (`type: "stamp"`, `color: "green"`) | `(230, 1150)` | `3,5 s – 6,5 s` | No fechamento de listas ou desafios (ex.: `"R$ 150 · 11 ITENS"`). |
| **Círculo / Seta Indicadora (`pointer`)** | `editonny` (`apply.py --pointer down-arrow` / `circle`) ou `ec_grafico.py circulo` | Coordenada do objeto (`x, y` medido no quadro) | `1,2 s – 2,2 s` | Quando o apresentador aponta para um item na prateleira, detalhe radiográfico ou preço pequeno. |
| **Flash de Transição (`flash` / `glow`)** | `editonny` (`transition-glow` / `transition-zoom`) ou `ec_grafico.py flash` | Tela inteira (`1080×1920`, opacidade máx. `35%`) | `0,40 s – 0,50 s` | **OBRIGATÓRIO** na entrada (`transition-zoom-0X.html`, `start - 0.25s` a `start + 0.25s`) e na saída (`transition-glow-0X.html`, `end - 0.20s` a `end + 0.20s`) de toda imagem inserida (`scene: "evidence"`). |
| **Card de Imagem / Evidência (`evidence`, `fit: "contain"`)** | `editonny` (`build.py` `.media.contained`) | Card `x=50, y=520, w=980, h=654, border-radius=36px` sobre fundo desfocado | `3,5 s – 4,5 s` (máx. **2 momentos** no vídeo) | Exibe 100% da imagem sem cortes laterais, acima da legenda (`y=1290`) e abaixo da pílula (`y=250`), com entrada elástica (`scale 0.85 -> 1.0`, `back.out(1.6)`), zoom contínuo (`1.00× → 1.10×`) e som sincronizado (`whoosh` + `photo` + `pop`). **Proibido reutilizar imagens de edições anteriores.** |
| **Painel Superior (`Frame Panel`)** | `editonny` (`frame.box: [36, 912, 1008, 990]`) | Painel em `y=230–850` + Speaker em `y=912–1902` | `3,3 s – 7,3 s` | Em vídeos educativos/clínicos/jurídicos que exigem gráfico, checklist ou comparação acima do especialista. |
| **Cortina Antes/Depois (`before-after`)** | `editonny` (`compositions/scenes/2d/before-after.html`) | Tela inteira (`1080×1920`) | `3,0 s – 5,0 s` | Comparações visuais sincronizadas (clínica estética/odontológica, reforma, limpeza industrial). |
