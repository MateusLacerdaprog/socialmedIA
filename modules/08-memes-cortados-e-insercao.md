# Módulo 08 — Regras de Uso de Memes (Clipes de Terceiros) em Reels

> **Catálogo local:** os clipes ficam em `memes_cortados/` e o catálogo com nome, recorte, `crop` e LUFS medidos de cada
> um fica em `terceiros/memes.json` + `terceiros/memes-catalogo.md`, **só na máquina** (são de terceiros e o repositório é
> público). O comando `socialmedia_engine.py meme` lê esse catálogo; sem ele, devolve só a receita encenada.

---

## 0. Regra de direitos — vale antes de tudo

Clipes de meme são, quase sempre, **material de terceiros**: apresentadores e celebridades de TV, trechos de programa
com logo da emissora, personagens protegidos, propaganda eleitoral e pessoas comuns de reportagens de rua.

**Consequência para conta de empresa** (orientação geral, não parecer jurídico):
- Uso **comercial** da imagem de alguém sem autorização gera indenização no Brasil, sem precisar provar prejuízo (**Súmula 403 do STJ**).
- O trecho de programa pertence à emissora (**Lei 9.610/98**).
- O **modo só áudio não resolve**: a voz de um apresentador conhecido também é imagem dele, e o áudio é trecho do programa.
- O **Rights Manager** da Meta encontra trechos de TV e pode silenciar ou bloquear o Reel. Conteúdo não original também perde recomendação.

| Tipo de conta | O que a skill faz |
| :--- | :--- |
| **`empresa`** (qualquer cliente) | **Não usa o clipe.** Devolve a receita de **remix do formato**: a equipe encena a reação (uau / errou / mãos na testa) em `0,8–2,0 s`; o som vem de **efeito sonoro licenciado**; figurinhas animadas próprias sobre o produto; ou, com Gemini Pro/Enterprise, reação gerada no **Argon** com a mascote da marca (nunca imitando pessoa real). |
| **`pessoal_sem_receita`** | Pode usar o clipe com as regras técnicas abaixo: punchline de `0,8–2,0 s`, `-16 LUFS`, crop da tarja, no máximo 1 a cada `15–20 s`. Ainda é material de terceiros, então pode ser silenciado pelo Rights Manager. |
| **Qualquer conta** | Termo pejorativo e propaganda eleitoral ficam **sempre bloqueados**. Palavrão: bloqueado em empresa; em canal pessoal só com bipe. |

Os níveis (§3) são **classificação de tom** (quanto o meme combina com cada nicho), **não** autorização de uso comercial.

---

## 1. Problemas técnicos dos clipes brutos `[OBSERVADO na medição do catálogo local]`

1. **Tarjas pretas embutidas:** os clipes vêm em `1920×1080`, mas parte deles é `4:3` com barras laterais gravadas no
   quadro (ex.: `crop=1440:1080:240:0`). **Regra:** aplicar o `crop` medido de cada clipe antes de redimensionar ou montar o layout.
2. **Volume muito desigual (`-36,4` a `-11,8 LUFS`):** a voz do Reel sai a `-14 LUFS`; um clipe a `-36` some no celular e
   um a `-12` assusta. **Regra:** compensar o ganho até **`-16 LUFS`** (`2 dB` abaixo da voz) ou `loudnorm=I=-16:TP=-1.5`.
3. **Duração bruta longa (até `11,2 s`):** **Regra:** nunca usar o arquivo inteiro acima de `2,2 s`; só a punchline,
   entre **`0,8 s e 2,0 s`**.

---

## 2. Os 4 modos de inserção (`1080×1920`), do mais profissional ao mais informal

### Modo 1 — `SFX_ONLY` (só o áudio normalizado + zoom no apresentador) 🏆
O vídeo da empresa **não é interrompido**: entra só o áudio curto (`0,8–1,5 s`) de uma reação (surpresa, erro, suspense,
aplauso) sincronizado com zoom `impacto` (`1.45×` em `0,15 s`) ou `reacao` (`1.30×`) no próprio apresentador.
Mantém a identidade visual limpa (`amber`, `paper` ou `night`).

### Modo 2 — `CHROMA_OVERLAY` (fundo verde `#00FF00` recortado sobre o vídeo)
Só para clipes com fundo verde (campo `chroma_green` do catálogo).
```text
[1:v]chromakey=0x00FF00:0.26:0.08,despill=green,scale=620:-1[meme];
[0:v][meme]overlay=x=W-w-40:y=1180:eof_action=pass
```
Canto inferior direito (`x = 420`, `y = 1180`), `1,1–1,8 s`, sem cobrir os olhos do apresentador (`y = 540–760`) nem o
título no topo (`y = 230`).

### Modo 3 — `PIP_CARD` (card flutuante no painel superior `y = 280–820`)
O meme (já sem tarjas) entra numa janela `840×630 px` com borda arredondada (`x = 120, y = 280`) por **`1,2–1,8 s`**,
enquanto o apresentador continua visível embaixo reagindo.

### Modo 4 — `CUTAWAY_EMPILHADO` (layout empilhado via FFmpeg)
Corte seco de **`1,0–2,0 s`** em layout empilhado (bloco nítido `1080×864` em `y = 300` sobre fundo desfocado
`boxblur=4:2,eq=brightness=-0.18`). **Nunca antes de `3,0 s`** (abrir com vídeo de terceiro penaliza o alcance e
esconde a marca); só como quebra de padrão no meio (`8,0–35,0 s`).

---

## 3. Níveis de tom (o catálogo local classifica cada clipe)

- **Nível 1 — tom compatível** com varejo, atacado, construção, gastronomia e e-commerce: surpresa positiva, erro de
  mito técnico, comemoração de meta, suspense antes do preço, fome, gambiarra antes da solução. *Tom compatível ≠ uso
  liberado*: em conta de empresa vale o remix encenado (§0).
- **Nível 2 — uso restrito:** só autoironia da equipe ou canal de entretenimento. Nunca apontado para o cliente
  (o cliente nunca pode se sentir chamado de "burro" ou "chorão").
- **Nível 3 — bloqueado:** palavrão, xingamento, termo pejorativo, propaganda eleitoral. O motor nunca seleciona.

---

## 4. Dosagem por tipo de empresa
> Em conta de empresa a coluna "Reações" diz **qual reação encenar**; o clipe só entra em conta pessoal sem receita.

| Tipo de Empresa | Limite por Reel | Modo permitido | Reações (intenção do comando `meme`) |
| :--- | :---: | :--- | :--- |
| **Supermercado / Atacadista / Varejo** | máx. 1 a cada 25 s (1 ou 2) | `SFX_ONLY`, `CHROMA_OVERLAY` ou `PIP_CARD` (`<= 1,8 s`) | `surpresa`, `erro_compra`, `humor_balcao`, `economia`, `suspense`, `fome` |
| **Loja de Material de Construção** | máx. 1 a cada 25 s | `SFX_ONLY`, `CHROMA_OVERLAY` ou `CUTAWAY_EMPILHADO` (`<= 1,8 s`) | `erro_compra`, `explicacao_calculo`, `gambiarra` |
| **Restaurante / Gastronomia / Padaria** | máx. 1 | `SFX_ONLY` ou `CUTAWAY_EMPILHADO` (`<= 1,8 s`) | `fome`, `surpresa`, `economia` |
| **E-commerce / D2C** | máx. 1 a cada 20 s | `CHROMA_OVERLAY` ou `PIP_CARD` (`<= 1,5 s`) | `surpresa`, `erro_compra`, `confirmacao`, `suspense` |
| **Educação / Treinamento Técnico** | máx. 1 | `SFX_ONLY` ou `PIP_CARD` (`<= 1,6 s`) | `mito_tecnico`, `transicao_educativa` |
| **Indústria B2B / Escritório** | máx. 1 (`SFX_ONLY` sutil) ou zero | **proibido vídeo de meme** | evitar: reduz a percepção de ticket alto |
| **Clínica / Saúde / Odontologia** | **zero** | 🚫 desativado | autoridade e confiança do paciente (`style: paper`) |
