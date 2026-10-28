# Instagram Viral Editing Playbook (Etapas 4 e 6)

> **Especificação Técnica Determinística para Edição Automática de Reels Empresariais (`1080×1920` @ `30 fps` / `60 fps`)**
> Este documento converte os padrões extraídos na auditoria empírica (`[OBSERVADO]` e `[CÁLCULO]`) e nos benchmarks do algoritmo do Instagram em regras matemáticas executáveis pelos motores locais **`editonny`**, **`effectcraft`**, **`hyperframes`** e **`ffmpeg`**.

> **Correção de 20/10/2026 — medição de 27 Reels virais de 14 empresas** (detalhe por conta só na máquina, em `terceiros/medicao-2026-10/`).
> - Os valores marcados `[MEDIDO n=27]` vêm de arquivos medidos com FFmpeg + Whisper. Reels com 2,6× a 204× a mediana de views da própria conta.
> - Os valores `[OBSERVADO — cliente]` vêm de **um único vídeo** de uma auditoria de cliente (os dados do cliente ficam fora do repositório). Valem como ponto de partida, não como padrão viral.
> - **Onde os dois discordam, vale o medido.** Seção nova: **§0 Tipo de Reel** (decide ritmo, legenda e fim antes de tudo).

---

## 0. Tipo de Reel — escolha antes de editar `[MEDIDO n=27]`

| Tipo | n | Duração (mediana) | Plano (mediana) | Plano mais longo aceito | 1º corte | Fala | Exemplos |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`montagem_criador`** (vlog, receita, compra, obra) | 11 | `65,9 s` | **`0,8 – 1,6 s`** | `≤ 8 s` | `≤ 1,2 s` | `~197 pal/min` | série de reforma, receita, compra em loja, evento |
| **`fala_continua`** (talking head, 1 tomada ou poucas) | 10 | `53,7 s` | **`2,0 – 8,0 s`** | `≤ 37 s` **com texto em movimento** | livre | `~181 pal/min` | especialista explicando, tomada única ou poucas |
| **`produto_sem_fala`** (ad curto, prato/produto parado) | 4 | `23,9 s` | `4 – 5 s` | `≤ 10 s` | livre | — | prato ou produto parado, escassez real |
| **`personagem_ia`** (personagem 3D/IA da marca) | 2 | `31,9 s` | `1,7 s` | `≤ 8 s` | `~2 s` | — | mascote 3D da marca — **só com Argon/Gemini Pro ou Enterprise** |

- **Não há ritmo único.** Só **3 de 27** virais respeitam "nenhum plano parado acima de 4 s". Um Reel de educação com 15,7× a mediana da conta é uma tomada única de 37 s; um de escritório contábil com 85× tem plano mediano de 16,7 s.
- Quando não há corte, o que segura a atenção é **texto em movimento**: palavra-chave gigante, caixa fixa com o gancho, legenda palavra a palavra.
- **Fala no quadro 0:** em 17 de 22 Reels com fala, a 1ª palavra está em `0,0 s`.
- **Duração:** só 6 de 27 têm ≤ 35 s; 15 têm 35–90 s. A amostra é de marcas grandes, então vale o tempo que a ideia pede.
- **Fator que não é edição:** pelo menos 15 de 27 são de **criador, celebridade ou parceria** (post colaborativo `#publi`, série com episódio numerado, patrocínio de evento). Para empresa local, o maior multiplicador observado é **colab com criador local + série numerada**.

---

## 1. Arquitetura do Quadro Vertical e Zonas Seguras (`1080×1920 px`)

Todo cálculo espacial deste Playbook assume um canvas vertical **`1080 px` (largura) × `1920 px` (altura)** (`9:16`).

### 1.1. Mapa de Coordenadas e Zonas de Risco (`[OBSERVADO]` + `[CÁLCULO]`)

| Zona / Elemento | Eixo X (`px`) | Eixo Y (`px`) | Status | Regra Técnica |
| :--- | :---: | :---: | :---: | :--- |
| **Danger Zone Superior (UI do IG)** | `0 – 1080` | `0 – 220` | 🚫 Bloqueado | Reservado para barra de status, câmera e cabeçalho do Reels. |
| **Zona de Hook / Título Fixo Superior** | `100 – 980` | **`230 – 380`** | ✅ Primário | Posição padrão de `ec_grafico.py` (`y=230`), `p0.png` (`y=230`) e `q0.png` (`y=260`). |
| **Zona de Olhos do Apresentador (Talking Head)** | `300 – 780` | **`540 – 760`** | 🎯 Âncora | Medido em `face_layout.json` (`eyes_y = 0.28 – 0.38` → `537 px – 730 px`). Nunca cobrir com texto. |
| **Zona de Elementos Gráficos / Cards / Contadores** | `140 – 940` | **`950 – 1220`** | ✅ Dinâmico | Posição validada do `counter` (`x=330, y=1170`) e `stamp` (`x=230, y=1150`) no vídeo do cliente auditado. |
| **Zona de Legendas Sincronizadas (Karaokê / Padrão)** | `80 – 920` | **`1100 – 1400`** | ✅ Leitura | `y=1100` (tela cheia ASS), `y=1280` (empilhado ASS), `y=1350–1400` (`editonny` standard). |
| **Danger Zone Direita (Ícones de Engajamento)** | `920 – 1080` | `980 – 1720` | 🚫 Bloqueado | Botões de Like, Comentário, DM Send, Save e Áudio. Centro X da legenda deslocado para **`POS_X = 500`** (em vez de `540`) quando em `y >= 1100`. |
| **Danger Zone Inferior (Handle, Legenda e Áudio)** | `0 – 1080` | `1530 – 1920` | 🚫 Bloqueado | Reservado para `@perfil`, prévia da legenda do post, botão "Seguir" e faixa de áudio. |
| **Margens Laterais de Segurança** | `< 60` e `> 1020` | `0 – 1920` | 🚫 Bloqueado | Evita corte em telas curvas ou proporções `9:19.5` de smartphones modernos. |

---

## 2. Tipografia On-Screen (Padrões Reproduzíveis em Pixels)

### 2.1. Tabela Mestra de Hierarquia Tipográfica (`1080×1920`) `[OBSERVADO]`

| Elemento | Tamanho (`px`) | Fonte Recomendada | Peso | Caixa | Cor Principal | Contorno (`Stroke`) | Sombra (`Shadow`) | Opacidade / Fundo | Tempo em Tela |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gancho Impacto (1–3 palavras)** | **`90 – 108 px`** | `Montserrat Black` / `Impact` / `Arial-Black` | `900` | `UPPERCASE` | `#FFDE00` ou `#FFFFFF` | `9 – 10 px` `#000000` | `4 px` (25–40%) | `100%` (sem fundo) | `1,2 s – 2,5 s` |
| **Gancho Pergunta / Pílula Topo (`y=230–260`)** | **`52 – 64 px`** | `Montserrat ExtraBold` / `Inter Bold` | `800` | `Sentence case` | `#FFFFFF` (fundo escuro) ou `#1A1A1A` (pílula `#FFFFFF`) | `0 px` (em pílula) ou `8 px` `#000000` |Drop shadow `18 px` blur (`65%` `#000000`) | Pílula `95%` `#FFFFFF` + borda `4 px` | `3,0 s – 8,0 s` (ancora o início) |
| **Legenda de fala de empresa (padrão)** `[MEDIDO n=14]` | **`40 – 48 px`** | `Arial` / `Inter` / `Montserrat` | `600 – 700` | **Caixa normal** | `#FFFFFF`; destaque de **1 palavra** na **cor da marca** | `0 – 2 px` | suave (`2 px`) | `100%` | frase curta, 1–2 linhas, centro **`y = 1330 – 1400`**, nunca abaixo de `y = 1530` |
| **Legenda palavra por palavra (talking head)** `[MEDIDO n=3]` | **`55 – 65 px`** | `Inter Bold` / `Arial Black` | `800` | caixa alta ou pílula preta | `#FFFFFF`, palavra-chave na cor da marca | `0 px` (pílula) | — | pílula `#000000` | `y = 1115 – 1540` |
| **Palavra-chave gigante (cinética)** `[MEDIDO n=3]` | **`150 – 260 px`** | `Montserrat Black` | `900` | livre | cor da marca | — | — | sem fundo | 1–2 palavras, centro `y = 860 – 1000` |
| **Legenda Karaokê (3–5 palavras)** — estilo **entretenimento/gameplay**; **não apareceu em nenhum dos 27 Reels de empresa** | **`76 – 88 px`** | `Arial Black` / `Montserrat Black` | `900` | `UPPERCASE` | Base `#FFFFFF` + Ativa **`#FFDE00`** | `7 px` `#000000` | `2 px` `#000000` (`50%`) | `100%` | `0,6 s – 1,8 s` por bloco |
| **Legenda Clean / Clínica (`maxWords: 3`)** | **`64 – 72 px`** | `Montserrat Black` / `Poppins ExtraBold` | `900` | `UPPERCASE` | `#FFFFFF` | `6 px` `#141824` | `3 px` (`35%`) | `100%` | `0,5 s – 1,4 s` por bloco |
| **Subtítulo / Caixa Editorial** | **`54 – 58 px`** | `Inter Bold` / `Arial Bold` | `700` | `Sentence case` | `#FFFFFF` | Caixa `14 px` padding | `0 px` | Caixa `#000000` a `75%` (`#BF000000`) | `1,5 s – 3,0 s` |
| **Contador de Preço / Valor (`counter`)** | **`84 – 96 px`** (número) + `44 px` (`R$`) | `Montserrat Black` / `JetBrains Mono Bold` | `900` | `UPPERCASE` | Número `#FFFFFF` + Prefixo `#FF6B00` | Borda do card `2 px` `#FF8800` (`40%`) | Sombra card `24 px` (`50%`) | Card `#121318` a `92%` | Acumulativo (`0,6 s` de roll-up por soma) |
| **Selo de Fechamento (`stamp`)** | **`60 – 68 px`** | `Montserrat Black` | `900` | `UPPERCASE` | `#FFFFFF` ou `#0A2E1A` | Borda `4 px` `#22C55E` | `12 px` (`40%`) | Fundo `#16A34A` (`95%`) | `3,0 s – 6,5 s` |

### 2.2. Regras de Quebra e Sincronismo de Legendas On-Screen (`[OBSERVADO — legendas.py & editonny]`)
1. **Velocidade e Densidade**:
   - **Modo Dinâmico (`editonny` / Clínica / Varejo Rápido)**: Máximo de **`3 palavras`** por bloco (`maxWords: 3`), máximo de **`18 caracteres`** por linha, 1 linha única em `y=1350–1400`.
   - **Modo Karaokê (ASS próprio)**: frase curta em 1–2 linhas, fonte `44 px`, caixa normal, centro em `y = 1360` (medido nos Reels de empresa).
2. **Proibição de Palavras Órfãs (`LIGACAO`)**:
   - Artigos, preposições e conjunções (`a`, `o`, `de`, `do`, `da`, `em`, `no`, `na`, `por`, `para`, `com`, `sem`, `que`, `se`, `mas`, `ou`) **nunca** podem ficar isolados no final de um bloco; o algoritmo deve empurrá-los para o bloco seguinte.
3. **Antecipação Visual**:
   - Títulos e cards gráficos podem antecipar a palavra falada em até **`150 ms` (`0,15 s`)**, mas nunca atrasar mais que `50 ms`.

---

## 3. Cortes de Vídeo, Enquadramento, Câmera e Ritmo de Edição

### 3.1. Parâmetros Técnicos de Corte (`[OBSERVADO]` + `[CÁLCULO]`)

| Parâmetro | Valor Técnico Obrigatório | Ferramenta / Implementação |
| :--- | :--- | :--- |
| **Início da Primeira Palavra (Hook Cut)** | **`<= 0,40 s`** (ideal `0,15 s – 0,38 s`) | `waveform_cut` / `editonny` (no vídeo do cliente auditado a 1ª palavra entra em `0,38 s`). |
| **Limiar Mínimo de Fala Contínua (`FALA_MIN`)** | **`0,30 s` (`300 ms`)** | Segmentos menores que `300 ms` são ruído/respiro e são descartados. |
| **Limiar de Pausa Entre Frases (`PAUSA_FRASE`)** | **`>= 0,35 s`** (`montagem_criador`) / **`>= 0,65 s` com `"dry": false`** (`fala_continua`) | Em `fala_continua`, é **proibido** usar `"dry": true` ou cortar respiros internos (`0,25s–0,55s`). Corta-se apenas entre parágrafos completos (`4,0s–12,0s` por bloco, máx. 5–8 blocos em 50s). |
| **Duração Mínima de um Corte (`MIN_CUT`)** | **`0,65 s`** (`montagem_criador`) / **`3,00 s`** (`fala_continua`) | Evita piscadas e picotamento artificial na fala de especialistas. |
| **Duração Mediana Alvo por Corte** | **por tipo (§0)**: `montagem_criador 0,8–1,6 s` · `fala_continua 4,0–12,0 s` (`"dry": false`) · `produto_sem_fala 4–5 s` · `personagem_ia ~1,7 s` `[MEDIDO n=27]` | Em `fala_continua`, 1 a 2 emendas de bloco são cobertas pelas imagens de apoio, restando apenas 3 a 4 cortes secos de câmera no vídeo inteiro. |
| **Duração Máxima Sem Mudança Visual (`MAX_CUT`)** | **por tipo (§0)**: `≤ 8 s` (montagem), `≤ 37 s` (fala contínua **com texto em movimento** a partir de `8 s`), `≤ 10 s` (produto) | Antes: `3,80–4,00 s` fixo. Só 3 de 27 virais respeitam esse limite `[MEDIDO n=27]`. |
| **J-Cut Padrão em Cortes de Fala** | **`lead_frames = 4` (`133 ms`)** / **`tail_trim = 2` (`67 ms`)** | Áudio da frase seguinte antecipa 4 quadros a 30 fps para fluidez orgânica. |
| **Pausa Dramática Intencional** | **`0,40 s – 0,65 s`** (máx. 1 por vídeo) | Permitida **apenas** imediatamente antes da revelação do número/preço principal. |

### 3.2. Movimento de Câmera e Zoom Automático (`[OBSERVADO — zoom.py & editonny]`)

> **REGRA TÉCNICA CRÍTICA (`FFmpeg 9`)**: **Proibido** usar o filtro `zoompan` do FFmpeg (bug documentado que descarta os primeiros quadros e dessincroniza o áudio). Todo zoom via FFmpeg deve usar transformação subpixel **`perspective`** ou escala CSS/Canvas via **`editonny`/`hyperframes`**.

| Preset de Zoom | Escala (`Scale`) | Duração da Rampa | Curva (`Easing`) | Quando Disparar Automaticamente |
| :--- | :---: | :---: | :--- | :--- |
| **`base_editonny` (Reenquadramento)** | **`1.08×` (`108%`)** | Contínuo no bloco | Estático / Tracking | Padrão de base em `project.json` para dar margem de corte e presença. |
| **`destaque` (Punch-in Suave)** | **`1.25×` (`125%`)** | `0,70 s` | `smoothstep` ($3t^2 - 2t^3$) | Em argumentos técnicos, mudança de tópico ou início de explicação. |
| **`impacto` (Snap Zoom / Preço)** | **`1.45×` (`145%`)** | `0,15 s` (`150 ms`) | `ease-out` cúbico ($1 - (1-t)^3$) | No exato frame em que o preço, desconto ou número de choque é falado. |
| **`reacao` (Vai-e-Volta)** | **`1.30×` (`130%`)** | `0,35 s` entrada / `0,35 s` saída | `smoothstep` | Em quebras de humor de balcão, ironias ou alertas ("Cuidado!"). |
| **`lento` (Push-in Contínuo)** | **`1.00× → 1.12×`** | Duração do take (`2,5s–4,0s`) | Linear | Durante storytelling, depoimento de cliente ou prova social emocionante. |

### 3.3. Padrões de Enquadramento (`Framing`) `[OBSERVADO]`
1. **Talking Head de Autoridade (Clínica / Serviços / Educação)**:
   - Plano médio-curto (`Medium Close-Up`), olhos entre `y=540 px` e `y=680 px`, ombros alinhados até `y=1250 px`, fundo limpo com profundidade (consultório/escritório real).
2. **Corredor / Operação Viva (Varejo / Atacado / Material de Construção)**:
   - Câmera na altura do peito/olhos (`1,50 m – 1,65 m`), leve ângulo alto (`10°–15°`) mostrando simultaneamente o apresentador, o produto na mão e o corredor de estoque profundo ao fundo (`q0.png`–`q5.png`).
3. **Paredão de Escala (Indústria / Distribuidora / Atacado)**:
   - Plano aberto vertical (0,0s–3,0s) onde a carga/palete ocupa `> 75%` da área da tela, seguido de corte para plano médio do especialista aos `3,0s`.
4. **Imagens de Apoio / Evidência (`scene: "evidence"`) — Regra dos 2 Momentos + Transição Obrigatória**:
   - **Proibição Absoluta de Reutilização**: É terminantemente proibido reutilizar imagens (`assets/*.jpg`, `*.png`) de edições ou projetos anteriores. O validador compara hashes `SHA-256` entre todos os projetos.
   - **Apenas 2 Momentos Cirúrgicos**: Inserir imagens em no máximo **2 momentos** do vídeo (ou a quantidade exata enviada pelo usuário): Momento 1 na dor/sintoma inicial (`~4,5s–8,5s`) e Momento 2 no mecanismo técnico/solução (`~20,0s–25,0s`, cobrindo emenda de bloco da fala).
   - **Card Enquadrado (`fit: "contain"`) + Transição Obrigatória (PRIORIDADE)**:
     - Imagens `3:2` ou `16:9` entram com `"fit": "contain"` no card arredondado (`x=50, y=520, w=980, h=654, border-radius=36px`) sobre fundo desfocado, livre da pílula superior (`y=250`) e da legenda (`y=1290`).
     - Toda imagem exige: (a) transição gráfica de entrada (`transition-zoom-0X.html`, `start - 0.25s` a `start + 0.25s`), (b) transição gráfica de saída (`transition-glow-0X.html`, `end - 0.20s` a `end + 0.20s`), (c) animação elástica do card (`scale: 0.85 -> 1.0`, `back.out(1.6)`) + zoom contínuo (`1.00× → 1.10×`), e (d) efeitos sonoros sincronizados (`whoosh` + `photo` + `pop`).

---

## 4. Elementos Gráficos, Cores e Áudio Profissional

### 4.1. Paletas de Cores Recomendadas por Posicionamento (`[OBSERVADO]`)

| Estilo (`editonny`) | Fundo do Card | Texto Principal | Cor de Destaque (`Accent`) | Borda / Contorno | Uso Recomendado por Nicho |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`amber` (Comercial / Oferta / Varejo)** | `#121318` (`92%`) | `#FFFFFF` | **`#FF6B00` / `#FFDE00`** | `#FF8800` (`2 px`) | Varejo, Atacado, Supermercado, Material de Construção, Gastronomia. |
| **`paper` (Clínico / Clean / Autoridade)** | `#FFFFFF` (`95%`) | `#1A1A2E` | **`#6B4C9A` / `#2563EB`** | `#D8B4FE` (`4 px`) | Saúde, Clínicas, Odontologia, Educação, Escritórios (Advocacia/Contabilidade). |
| **`night` (Industrial / Tech / Premium)** | `#0B0F19` (`94%`) | `#F8FAFC` | **`#38BDF8` / `#22C55E`** | `#1E293B` (`2 px`) | Indústria, Tecnologia, E-commerce Premium, Engenharia. |
| **`selo_fechamento` (Confirmação)** | `#16A34A` (`95%`) | `#FFFFFF` | **`#DCFCE7`** | `#22C55E` (`4 px`) | Checklists concluídos, meta batida (`"R$ 150 · 11 ITENS"`), aprovação. |

### 4.2. Engenharia de Áudio e Mixagem (`[OBSERVADO — CLAUDE.md & WORKFLOW.md]`)

| Parâmetro de Áudio | Especificação Técnica Exata | Regra de Execução |
| :--- | :--- | :--- |
| **Loudness Integrado Final** | **`-14,0 LUFS`** (`± 0,5 LUFS`) | Normalização obrigatória EBU R128 em dois passes (`loudnorm=I=-14:TP=-1.5:LRA=11`). Confirmado: os 27 Reels virais saem do Instagram entre `-14,5` e `-14,1 LUFS` `[MEDIDO n=27]`, então mixar mais alto não adianta. |
| **Silêncio** | **`≤ 10 %`** do tempo abaixo de `-40 dB` | Mediana `0 %`, máximo `9,9 %` `[MEDIDO n=27]`: sempre há fala, música ou ambiente. |
| **True Peak Máximo (`dBTP`)** | **`<= -1,5 dBTP`** (medido `-1,74 dBTP` no vídeo do cliente auditado) | Rechecar após codificação AAC para evitar clipping em alto-falantes de celular. |
| **Relação Sinal-Ruído (SNR Voz/Fundo)** | **`>= 25 dB`** (medido `32 dB` no vídeo do cliente auditado) | Se SNR `< 20 dB`, aplicar `afftdn=nf=-25`; se `>= 25 dB`, preservar voz natural sem filtro destrutivo. |
| **Cadeia DSP da Voz (FFmpeg)** | `highpass=f=80`, `equalizer=f=3000:t=q:w=1:g=2`, `acompressor=threshold=-18dB:ratio=3:attack=5:release=50` | Remove grave de manuseio (`< 80 Hz`), dá clareza de dicção em `3 kHz` e controla dinâmica. |
| **Música de Fundo + Sidechain Ducking** | Base **`-24 dB a -28 dB`** sob a voz; sobe para **`-14 dB`** em intervalos sem fala `> 0,8s` | `sidechaincompressor=threshold=0.015:ratio=6:attack=15:release=250` (a voz esmaga a música automaticamente). |
| **Efeitos Sonoros (`SFX`)** | Calibrados por janela RMS de `100 ms` + `anchorSeconds` | `title-swoosh` em títulos, `pop-ui`/`bubble-pop` em itens de lista, `cash-register` em preços, `ding` no selo final. **Proibido** SFX em toda palavra. |

---

## 5. Legendas do Post (Copywriting, Estrutura e SEO Instagram)

### 5.1. Parâmetros Estruturais da Legenda Textual (`[OBSERVADO — publicacao.py & legenda-frameworks.md]`)

1. **Limite da Prévia (Zona Crítica do "...mais")**:
   - Máximo absoluto de **`125 caracteres`** na primeira linha antes da quebra.
   - A primeira linha **nunca** pode repetir literalmente a primeira frase falada no vídeo; deve complementar a curiosidade (ex.: se o vídeo abre com *"O que dá pra comprar com R$150?"*, a linha 1 da legenda abre com *"Fizemos a conta na calculadora: 11 itens de giro rápido por R$ 150 👇"*).
2. **Extensão Total por Objetivo**:
   - **Reels de Estoque / Humor / Oferta Rápida**: **`180 a 350 caracteres`** (leitura em 4 segundos, foco 100% no CTA de envio/WhatsApp).
   - **Reels Educativos / Rendimento / Saúde / Indústria**: **`450 a 900 caracteres`** (lista escaneável que gera **Save Rate > 2%**).
   - **Limite Técnico da Plataforma**: `2.200 caracteres` (nunca ultrapassar `1.200` para não diluir o CTA).
3. **Espaçamento, Emojis e Quebra de Linhas**:
   - Parágrafos de no máximo **2 linhas** separados por **1 linha em branco** (`\n\n`).
   - Máximo de **3 a 4 emojis** em toda a legenda, usados apenas como marcadores visuais de lista (`📦`, `💰`, `📍`, `👇`). Proibido blocos de emojis no final da frase.
4. **Regra de Hashtags e Triple-Mention SEO (Atualização IG)**:
   - Máximo de **`5 hashtags`** altamente específicas no rodapé (ex.: `#atacadoalimentos #panificacao #confeitariapro #recife #insumos`).
   - **Triple-Mention SEO**: A palavra-chave principal do negócio deve aparecer (1) falada no áudio, (2) escrita no hook on-screen e (3) no primeiro parágrafo da legenda.
5. **Engenharia de CTA (Foco em Sends e DMs)**:
   - Todo Reel deve terminar com um **CTA de Código Comentado** (ex.: *"Comenta **TABELA** que te envio a lista no Direct"*) ou um **CTA de Compartilhamento Direcionado** (ex.: *"Manda esse vídeo pro seu sócio ou comprador antes do pedido da semana"*). **Um só, nunca os dois.**
   - **Observado nos virais** `[OBSERVADO n=19]`: a última frase pede comentário com uma pergunta ("Qual das duas você usaria primeiro? Conta aqui nos comentários.", "Quem vai também?"). Posts de criador começam com `#publi`/`Publicidade`. No varejo, o preço vem em lista ("Prato… R$ 29,99"). Prazo e escassez aparecem só quando são reais ("até 30 de outubro", "Última semana").

### 5.2. Encerramento do Vídeo `[OBSERVADO n=27]`
- **Anúncio de marca:** cartão final de `0,8 – 1,2 s` com logo + **um** CTA ("O link tá na bio", "Agende sua avaliação"), fundo na cor da marca. Apareceu em 14 de 27.
- **Conteúdo nativo de criador/série:** **sem cartão de marca**. Termina na última fala ou na piada. Apareceu em 0 de 9 posts de criador.
- **Saúde:** responsável técnico com registro (CRO/CRM) visível na tela, como a rede de clínicas medida faz em todos os quadros.

---

## 6. Tabela de Regras Automáticas de Decisão (Prontas para Código)

```yaml
# Regras determinísticas consumidas por scripts/socialmedia_engine.py
canvas:
  width: 1080
  height: 1920
  fps: 30
  export_feed_crop: "1080x1350" # 4:5 centralizado quando solicitado

hook:
  max_first_word_delay_s: 0.40   # medido: 17/22 começam em 0.0 s; ideal <= 0.30
  on_screen_title_y: 230
  on_screen_title_duration_s: [3.0, 8.0]
  font_size_impact_px: 96
  font_size_pill_px: 58

captions:
  editonny_max_words: 3
  editonny_y: 1380
  ass_empresa_font_size_px: 44
  ass_empresa_stroke_px: 2
  ass_empresa_shadow_px: 2
  ass_empresa_pos_y: 1360
  primary_color_hex: "#FFFFFF"
  highlight_color_hex: "#FFDE00"

reel_types:   # [MEDIDO n=27] — escolha antes de cortar
  montagem_criador: {median_cut_s: [0.8, 1.6], max_shot_s: 8, first_cut_max_s: 1.2, edl_dry_mode: true, pause_cut_threshold_s: 0.35}
  fala_continua:    {median_cut_s: [4.0, 12.0], max_shot_s: 37, moving_text_required_over_s: 8, edl_dry_mode: false, pause_cut_threshold_s: 0.65, max_cuts_per_minute: 10.0}
  produto_sem_fala: {median_cut_s: [4.0, 5.0], max_shot_s: 10}
  personagem_ia:    {median_cut_s: 1.7, max_shot_s: 8, requires: "client.gemini_plan in [pro, enterprise]"}

evidence_images:
  forbid_reuse_across_projects: true
  max_moments_default: 2
  default_fit: "contain"
  card_box_px: [50, 520, 980, 654]
  card_border_radius_px: 36
  require_entry_transition_scene: "compositions/scenes/transition-zoom-0X.html"
  require_exit_transition_scene: "compositions/scenes/transition-glow-0X.html"
  require_zoom_motion: {scale: 1.10, ease: "sine.inOut"}
  require_sfx: ["whoosh", "photo", "pop"]

business_captions:   # [MEDIDO n=14] legenda de fala em Reel de empresa
  font_size_px: [40, 48]
  uppercase: false
  color_hex: "#FFFFFF"
  highlight: "brand_color"
  highlight_max_words_per_sentence: 1
  center_y: [1330, 1400]
  max_y: 1530

cuts:
  min_speech_segment_s: 0.30
  pause_cut_threshold_s: 0.35
  min_cut_duration_s: 0.65
  target_median_cut_s: 1.75   # só para montagem_criador; os outros tipos usam reel_types
  max_static_shot_s: 4.00     # antigo; substituído por reel_types.*.max_shot_s
  jcut_lead_frames_30fps: 4
  jcut_tail_trim_frames_30fps: 2

zoom:
  base_scale: 1.08
  highlight_scale: 1.25
  highlight_duration_s: 0.70
  impact_scale: 1.45
  impact_duration_s: 0.15
  reaction_scale: 1.30
  reaction_duration_s: 0.35
  slow_push_scale: 1.12

audio:
  target_lufs: -14.0
  max_true_peak_dbtp: -1.5
  music_bed_speech_db: -26.0
  music_bed_pause_db: -14.0
  highpass_hz: 80
  presence_boost_hz: 3000
  presence_boost_db: 2.0

post_caption:
  preview_cutoff_chars: 125
  short_length_chars: [180, 350]
  educational_length_chars: [450, 900]
  max_hashtags: 5
  max_emojis: 4
```
