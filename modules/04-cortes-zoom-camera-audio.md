# Módulo 04 — Cortes, Ritmo, Zoom, Movimento de Câmera e Áudio (Etapas 4.4 a 4.9)

> **Regra de Retenção (corrigida em 20/10/2026, `[MEDIDO n=27]`):** o ritmo depende do **tipo de Reel** (PLAYBOOK §0).
> - **`montagem_criador`:** plano mediano `0,8–1,6 s`, nenhum plano acima de `8 s`, 1º corte até `1,2 s`.
> - **`fala_continua`:** plano mediano `2–8 s`. Planos de até `37 s` aparecem em virais, mas **acima de `8 s` exigem texto em movimento** (palavra-chave gigante, caixa fixa, legenda palavra a palavra).
> - **`produto_sem_fala`:** planos de `4–5 s`, máximo `10 s`.
>
> A regra antiga ("nada parado acima de `4,00 s`, mediana `1,65–2,20 s`") só é cumprida por **3 dos 27** Reels virais medidos. Continua valendo como alvo do tipo `montagem_criador` de varejo, onde nasceu (auditoria de cliente).

---

## 1. Engenharia de Cortes (`Waveform Cutting` & `J-Cuts`)

### 1.1. Parâmetros Técnicos de Corte (`[OBSERVADO — edl.json & editonny_fala.py]`)
1. **Corte Guiado pela Forma de Onda (`Waveform-First`)**:
   - Os limites de cada intervalo (`start`, `end`) são extraídos da forma de onda real do áudio (`48 kHz`), nunca apenas do timestamp aproximado do Whisper, protegendo consoantes surdas finais (`/s/`, `/t/`, `/k/`, `/p/`).
   - **Margem de ataque (`pre-roll`)**: `40 ms a 60 ms` antes do início da fonação.
   - **Margem de queda (`post-roll`)**: `50 ms a 80 ms` após o fim da fonação (`ends_in_valley: true`).
2. **Remoção Seletiva por Tipo de Reel (Regra Anti-Picotamento em `fala_continua`)**:
   - **Em `montagem_criador` (varejo, oferta, desafio)**: remover respirações audíveis entre frases (`>= 350 ms`), falsos começos, repetições de preço e comandos de bastidor (*"Vem cá"*, *"Grava aí"*, *"Espera"*).
   - **Em `fala_continua` (saúde, clínica, serviços, educação, especialista)**: **PROIBIDO usar `"dry": true` ou cortar respiros internos de `300 ms – 550 ms`**. Agrupar frases completas em **5 a 8 blocos contínuos de raciocínio** (`"dry": false`, `4,0 s a 12,0 s` por bloco), cortando apenas erros de gravação ou pausas longas entre parágrafos (`>= 650 ms`). Cobrir 1 a 2 emendas de bloco com as **2 imagens enviadas pelo usuário** (sempre com transição `transition-zoom` / `transition-glow`), deixando apenas **3 a 4 cortes secos de câmera** visíveis no vídeo todo.
3. **J-Cut Obrigatório em Transições de Fala**:
   - Em `edl.json`, configurar `"jcut": {"lead_frames": 4, "tail_trim_frames": 2}` (a `30 fps`, o áudio do corte seguinte antecipa `133 ms` enquanto o vídeo anterior encerra `67 ms` mais cedo), eliminando a sensação robótica de corte seco.
4. **Nivelamento de Ganho por Segmento (`gain_db`)**:
   - Quando o apresentador se afasta do microfone ou vira o rosto para a prateleira, compensar individualmente no intervalo da EDL (ex.: `gain_db: +5.3` em `r002` ou `gain_db: -4.3` em `r012` quando fala muito perto da cápsula).

---

## 2. Zoom Automático Subpixel e Movimento de Câmera

### 2.1. Matemática dos 4 Presets de Zoom (FFmpeg `perspective` & `editonny`)

| Preset | Fator de Escala | Tempo de Rampa | Fórmula de Interpolação $s(t)$ | Aplicação no Fluxo |
| :--- | :---: | :---: | :--- | :--- |
| **`destaque` (Punch-in)** | `1,00× → 1,25×` | `0,70 s` | $u = \text{clamp}(t/0.7, 0, 1)$, $s = 1 + 0.25(3u^2 - 2u^3)$ | Enfatizar argumento chave ou novo tópico sem choque visual. |
| **`impacto` (Snap Zoom)** | `1,00× → 1,45×` | `0,15 s` | $u = \text{clamp}(t/0.15, 0, 1)$, $s = 1 + 0.45(1 - (1-u)^3)$ | Cravar preço (`"R$ 22"`), tonelagem (`"32 toneladas"`) ou revelação. |
| **`reacao` (In-Hold-Out)** | `1,00× → 1,30× → 1,00×` | `0,35 s` in / `0,35 s` out | Smoothstep simétrico na entrada e nos últimos `0,35 s` | Quebra de humor, alerta de erro ou reação facial. |
| **`lento` (Push-in)** | `1,00× → 1,12×` | Duração da cena (`2–4 s`) | $s = 1 + 0.12(t / T_{\text{cena}})$ | Storytelling, autoridade clínica, explicação contínua. |

### 2.2. Regras de Estabilização e Conflito com Overlays (`camera_motion.py`)
- Se um intervalo possui um ponteiro ou círculo ancorado a um objeto físico (`overPerson: true` no `editonny`), **desativar zoom/pan digital** nesse intervalo para que a seta não saia do alvo.
- Nos intervalos apenas de fala (`talking head`), alternar entre escala `1.08×` e `1.18×` nos jump cuts para disfarçar o corte seco (regra de mudança mínima de `8% a 12%` na escala entre takes consecutivos do mesmo ângulo).

---

## 3. Enquadramento e Ritmo de Edição por Formato

| Formato de Reel | Segundos por Corte (Mediana) | Mudanças Visuais / Minuto | Enquadramento Dominante | Intensidade Visual |
| :--- | :---: | :---: | :--- | :---: |
| **Desafio de Orçamento / Lista de Preços** | **`1,65 s`** (`0,65s – 3,5s`) | `32 – 38 / min` | Corredor dinâmico (`Medium Shot`) + Mão no produto + Calculadora | **Alta** (Contador + Legenda + Cortes rápidos) |
| **Estoque / Volume / Atacado (`20–30s`)** | **`2,10 s`** (`1,2s – 3,8s`) | `25 – 30 / min` | Plano Aberto Vertical (0–4s) → Plano Médio ao lado do palete | **Média-Alta** (Escala física real domina o quadro) |
| **Educativo / Rendimento / Indústria (`45–60s`)** | **`6,50 s`** (`4,0s – 11,0s`, `"dry": false`) | `6 – 10 / min` | Talking Head (`Medium Close-Up`) + **apenas 2 momentos de imagem** com transição | **Média** (Foco na clareza didática e fluidez de fala) |
| **Clínica / Saúde / Escritório (`30–50s`)** | **`7,50 s`** (`4,5s – 12,0s`, `"dry": false`) | `5 – 8 / min` | Especialista em `y_eyes=0.35` + **apenas 2 momentos de imagem** (`fit: "contain"`) com transição `transition-zoom`/`glow` | **Sóbria e Elegante** (Estilo `paper`, fala contínua sem picotar) |

**Medido nos virais `[MEDIDO n=27]`** (corte = `scene > 0,3` no FFmpeg):

| Tipo | Reels | Plano mediano | Plano mais longo (mediana) | Trocas nos 10 s iniciais | Câmera observada |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `montagem_criador` | 11 | `1,07 s` | `7,0 s` | `7 – 16` | na mão, selfie ou acompanhando o criador; macro de produto |
| `fala_continua` | 10 | `5,5 s` | `18,9 s` | `0 – 4` | tripé, plano médio ou close; um Reel de educação = 1 tomada de `37 s` |
| `produto_sem_fala` | 4 | `4,4 s` | `10,0 s` | `0 – 1` | produto parado + animação sobre ele (letreiro de LED, figurinhas) |
| `personagem_ia` | 2 | `1,7 s` | `7,3 s` | `4 – 6` | câmera virtual, close de reação |

- **Fala:** mediana de `182 pal/min`; montagem de criador ~`197`; série de material de construção `279–287` `[MEDIDO n=22]`.
- **Zoom/punch-in:** **não medido** (a folha de quadros não mede zoom com segurança). Os presets abaixo continuam como `[HIPÓTESE]`.

---

## 4. Engenharia de Áudio, Ducking e Efeitos Sonoros (`SFX`)

### 4.1. Cadeia de Processamento Obrigatória (Voz + Música + SFX)
1. **Voz Principal**:
   - Filtro passa-alta em `80 Hz` + presença `+2 dB` em `3 kHz` + compressor `3:1` + normalização final integrada em **`-14,0 LUFS`** e pico verdadeiro **`<= -1,5 dBTP`**.
2. **Música de Fundo (`Music Bed`)**:
   - Escolha compatível com o posicionamento: batida percussiva limpa para varejo/estoque; instrumental minimalista acústico/lo-fi corporativo para clínicas e escritórios.
   - Volume sob a fala: **`-26 dB a -28 dB`** (nunca competir com as consoantes da voz).
   - Ducking automático via sidechain (`attack=15ms`, `release=250ms`).
3. **Mapa de Efeitos Sonoros (`SFX`) com `anchorSeconds`**:
   - **Abertura (`0,15 s`)**: `title-swoosh` (apoia a entrada do gancho textual no topo).
   - **Novo Item / Soma no Contador**: `cash-register` ou `pop-ui` (pico alinhado ao início do roll-up numérico).
   - **Destaque / Seta / Círculo**: `swish` ou `pencil`.
   - **Selo Final (`stamp`)**: `ding` (reforça recompensa dopaminérgica de conclusão).
   - **Limite máximo**: `1 SFX` a cada `3,0 s – 5,0 s` (nunca colocar efeito sonoro em cada corte de fala).
