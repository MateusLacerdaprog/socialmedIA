# Módulo 01 — Engenharia de Hooks para Reels Empresariais (`0,0 s – 3,0 s`)

> **Métrica de Sucesso:** Hook Rate (retenção aos 3 segundos) **`>= 65%`**.
> **Regra de Ouro:** O gancho de um Reel empresarial nunca depende apenas da fala. Ele exige a sincronização exata de **3 canais** nos primeiros `1.500 ms` (`1,5 s`).

> **Medido em 27 Reels virais de empresa (20/10/2026)** `[MEDIDO]`:
> - **Fala no quadro 0** em **17 de 22** Reels com fala.
> - **Quadro 0:** pessoa em 12, produto/mãos em close em 6, ambiente em 6, tela preta/desfocada em 3.
> - **Fala dos 3 primeiros segundos** (14 de 21 se encaixam):
>   - **pergunta direta** ao público (6) — "Você confiaria seu futuro nos dados?", "Quantas vezes por semana o seu time…";
>   - **conflito em andamento** (4) — "nossa casa tá caindo aos pedaços", "a regra é clara: se os dois trabalham, os dois limpam";
>   - **promessa de resultado** (2) — "Hoje você vai aprender a fazer…";
>   - **novidade com o nome do produto** (2).
> - O título fixo no topo aparece em 1 de 27 (série de reforma de uma loja de material de construção, `y ≈ 380–440`, com número do episódio). O `y = 230` abaixo é o padrão do `effectcraft`, não um dado medido.
> - Os percentuais de "+201 %" etc. deste módulo vêm de **uma conta** (conta de cliente, anonimizada). Valem para aquele perfil, não como média do Instagram.

---

## 1. A Equação dos 3 Canais Simultâneos (`0,00 s – 1,50 s`)

| Canal | Tempo de Disparo | Especificação Técnica Exata (`1080×1920`) | Implementação Local |
| :--- | :---: | :--- | :--- |
| **1. Canal Visual (Quadro 1)** | `0,00 s` (Frame 0) | Movimento físico imediato (passo à frente, mão erguendo produto, B-roll macro) + Zoom inicial `1.08×` ou punch-in `1.25×` em `0,7s`. Proibido quadro estático ou fade-in preto. | `editonny` (`zoom: 1.08`) ou FFmpeg `perspective` (`destaque`). |
| **2. Canal Textual (Hook Topo)** | `0,00 s – 0,15 s` | Título fixo em **`y = 230 px a 260 px`**, centrado em `x = 540 px`, largura máx. `880 px`, `4 a 8 palavras`, fonte `56–64 px` (pílula) ou `88–96 px` (impacto), duração `3,0 s – 8,0 s`. | `effectcraft` (`ec_grafico.py titulo`) ou `editonny` (`headline`/`badge`). |
| **3. Canal Auditivo (Voz + SFX)** | `<= 0,38 s` | Corte no vale exato da forma de onda (`waveform_cut`) antes da primeira consoante. Zero respiração inicial, zero *"Olá pessoal, tudo bem?"*. SFX sutil (`title-swoosh` ou `pop-ui`) ancorado em `0,15 s`. | `editonny` (`transcribe_batch` + `edl.json`) + `apply.py --sounds`. |

---

## 2. Os 7 Arquétipos de Hook de Maior Desempenho Empresarial

### 2.1. Desafio de Orçamento Fechado (*Budget Challenge*)
- **Desempenho Empírico `[OBSERVADO — cliente]`**: `+201%` acima da mediana da conta.
- **Fórmula Verbal**: *"O que dá pra comprar com R$ [VALOR] aqui na [EMPRESA]?"*
- **Texto On-Screen (`y=250`)**: `O que dá pra comprar com R$[VALOR]?` (2 linhas, branco com drop-shadow preto denso).
- **Gatilho Visual**: Apresentador segurando calculadora física ou cestinha/carrinho já em movimento no corredor.

### 2.2. Escala Física / Tonelagem (*Volume Shock*)
- **Desempenho Empírico `[OBSERVADO — cliente]`**: `+119%` acima da mediana.
- **Fórmula Verbal**: *"[NÚMERO] toneladas de [PRODUTO] acabaram de descer no pátio."*
- **Texto On-Screen (`y=230`)**: `[NÚMERO] TONELADAS DE [PRODUTO]` (destaque em `#FFDE00`).
- **Gatilho Visual**: Plano aberto vertical de cima para baixo ou caminhando rente ao paredão de paletes do chão ao teto.

### 2.3. Matemática Contraintuitiva / Custo Invisível (*Math Proof*)
- **Desempenho Empírico `[OBSERVADO — cliente]`**: `+143%` acima da mediana.
- **Fórmula Verbal**: *"100 gramas parece barato até você fazer essa conta."* ou *"Por que essa [MATÉRIA-PRIMA] faz você usar 15% menos na receita?"*
- **Texto On-Screen (`y=230`)**: `Barato que sai CARO na receita` ou `Use 15% MENOS com essa troca`.
- **Gatilho Visual**: Dois produtos lado a lado (comparação) ou close na tabela nutricional/percentual técnico.

### 2.4. Pergunta de Dor Aguda / Diagnóstico Clínico (*Symptom Hook*)
- **Desempenho Empírico `[OBSERVADO — p0.png]`**: Padrão validado em clínicas e serviços de alto ticket.
- **Fórmula Verbal**: *"Medo de perder o dente? A odontologia moderna já resolve isso sem..."*
- **Texto On-Screen (`y=230`)**: Pílula branca `#FFFFFF` (`border-radius: 999px`) com texto escuro `#1A1A2E` e palavra-chave de dor em destaque (`#6B4C9A` ou `#DC2626`).
- **Gatilho Visual**: Especialista em consultório olhando diretamente para a lente (`eyes_y = 0.35`), cortando em `1,8 s` para B-roll macro do equipamento/exame (`p1.png`).

### 2.5. Chegada Sem Avisar / Bastidor Real (*Pattern Interrupt POV*)
- **Desempenho Empírico `[OBSERVADO — cliente]`**: Top 1 absoluto da conta auditada.
- **Fórmula Verbal**: *"Invadi a central do WhatsApp sem avisar pra ver o que tá saindo agora."*
- **Texto On-Screen (`y=240`)**: `Chegando sem avisar no [SETOR]`
- **Gatilho Visual**: Câmera em primeira pessoa (POV) abrindo a porta ou virando o corredor em direção à equipe trabalhando ao vivo.

### 2.6. Erro de Compra / Alerta Técnico (*Mistake Callout*)
- **Fórmula Verbal**: *"Se você ainda compra [PRODUTO] olhando só o preço da caixa, você está perdendo margem."* `[OBSERVADO — cliente]`.
- **Texto On-Screen (`y=230`)**: `Pare de comprar [PRODUTO] assim`
- **Gatilho Visual**: Gesto físico de "pare" com a mão aberta ou apontando para o detalhe técnico do rótulo.

### 2.7. Ancoragem de Preço Rasgado (*Price Tear*)
- **Desempenho Empírico `[OBSERVADO — cliente]`**: Reel da conta auditada acima da mediana.
- **Fórmula Verbal**: *"O preço desse lote veio tão baixo que a gente rasgou a tabela antiga."*
- **Texto On-Screen (`y=230`)**: `PREÇO DE LOTE DIRETO DA FÁBRICA`
- **Gatilho Visual**: Ação física de rasgar papel ou colar etiqueta amarela/laranja de oferta na gôndola no primeiro segundo.

---

## 3. Regras de Proibição no Hook (Eliminação Automática no Corte)
O motor `socialmedia` deve remover automaticamente da EDL inicial (`0,0 s – 3,0 s`):
1. Vinhetas ou logotipos animados no início (logotipo vai exclusivamente no cartão final ou marca d'água discreta).
2. Cumprimentos vazios: *"Bom dia"*, *"Boa tarde pessoal"*, *"Hoje estamos aqui para mostrar..."*, *"Mais um vídeo da..."*.
3. Pausas respiratórias iniciais `> 150 ms` antes da primeira palavra.
4. Planos abertos estáticos sem movimento humano ou de câmera.
