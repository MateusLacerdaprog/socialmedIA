# Módulo 07 — Playbooks Específicos: Reels Educativos vs. Reels de Vendas

> **Regra de Calibragem:** Um Reel Educativo otimiza **Saves (`> 2%`) + Sends (`DMs`) + Autoridade**. Um Reel de Vendas otimiza **Watch Time até o preço + Comentários de Código + Cliques no WhatsApp**. Eles nunca devem usar a mesma cadência de edição.

---

## 1. Playbook: Reels Educativos de Alto Desempenho (`35 s – 60 s`)

### 1.1. Parâmetros Técnicos Exclusivos
- **Fórmula de Sucesso Validada (`[OBSERVADO — cliente]`)**:
  - **Proibido dar aula teórica abstrata**. Todo Reel educativo empresarial deve responder a uma pergunta de **bolso, rendimento, segurança ou tempo** (*"Por que o trigo aumentou?"*, *"Margarina 80% lipídios: use 15% menos"*, *"100g parece barato até fazer a conta"*).
- **Estrutura Cronometrada**:
  1. `0,0 s – 3,0 s` (**Hook Contraintuitivo**): Afirmação que desafia o senso comum do comprador + título fixo em `y=230`.
  2. `3,0 s – 12,0 s` (**O Mecanismo Técnico em 1 Frase**): Explicação física/química/financeira simples com zoom `destaque` (`1.25×`).
  3. `12,0 s – 35,0 s` (**A Conta Prática na Tela**): Comparação entre o jeito amador e o jeito profissional usando `counter` ou painel superior (`Frame Panel`).
  4. `35,0 s – 48,0 s` (**Aplicação + CTA de Salvamento/Envio**): Como aplicar hoje + *"Salva esse vídeo pra consultar na bancada"*.
- **Configuração `editonny`**:
  - `maxWords`: `3` a `4` palavras.
  - `zoom`: `base 1.08×` + `destaque 1.25×` nos pontos de virada lógica.
  - `SFX`: `pencil`, `swish`, `pop-ui` (sóbrios).

---

## 2. Playbook: Reels de Vendas, Oferta e Estoque (`20 s – 60 s`)

### 2.1. Subformato A: Explosão de Estoque / Lote Novo (`20 s – 28 s`)
- **Referência Validada (`[OBSERVADO — cliente]`)**:
  1. `0,0 s – 3,5 s`: Plano aberto do paredão de mercadoria + tonelagem/volume no topo (`y=230`).
  2. `3,5 s – 16,0 s`: 3 cortes rápidos (`~2,0 s` cada) mostrando: (a) marca/especificação, (b) para qual negócio serve, (c) vantagem de rendimento ou preço de fardo.
  3. `16,0 s – 25,0 s`: Chamada de urgência operacional (*"Já liberado no pátio — comenta TABELA ou chama no WhatsApp"*).
- **Configuração Técnica**:
  - `style`: `"amber"`
  - `zoom`: `impacto` (`1.45×` em `0,15 s`) na palavra do volume/preço.

### 2.2. Subformato B: Desafio de Orçamento / Cesta Completa (`45 s – 62 s`)
- **Referência Validada (`[OBSERVADO — cliente]`)**:
  1. `0,0 s – 5,0 s`: Pergunta do orçamento (`R$ 150`, `R$ 200`, `R$ 500`) + primeiro item imediato.
  2. `5,0 s – 46,0 s`: Sequência rítmica de `8 a 12 itens` (`mediana de corte = 1,67 s`). A cada preço falado, disparo de animação `counter` (`duration: 0.6s`, `where: [330, 1170]`).
  3. `46,0 s – 56,0 s`: Selo verde `stamp` (`"R$ [TOTAL] · [N] ITENS"`, `where: [230, 1150]`) + convite para visitar a loja.
  4. `56,0 s – 61,0 s`: Cartão de endereço/localização (máx. `4,5 s`).
