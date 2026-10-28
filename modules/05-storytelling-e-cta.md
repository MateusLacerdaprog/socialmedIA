# Módulo 05 — Storytelling Empresarial, Retenção e Engenharia de CTA

> **Objetivo Algorítmico:** Maximizar **Watch Time** (via *Open Loops* e *Seamless Loops*), **Sends per Reach** (compartilhamentos via DM) e **Conversão Direta** (comentários com palavra-código e cliques no WhatsApp).

---

## 1. As 4 Estruturas de Storytelling Empresarial para Vídeos Curtos

### 1.1. Arco de Desafio Matemático (*Open-Loop Budget Arc* — `45 s a 65 s`)
- **0,0 s – 3,5 s (Hook + Regra do Jogo)**: Define o limite financeiro ou físico (*"O que dá pra comprar com R$ 150?"*).
- **3,5 s – 25,0 s (Aceleração de Itens 1 a 6)**: Cortes rápidos (`1,2 s – 2,2 s`), mostrando produto + preço + soma parcial no `counter`.
- **25,0 s – 45,0 s (Tensão do Limite — Itens 7 a 11)**: Apresentador mostra quanto falta (*"Tá em R$ 127, ainda cabe mais!"* → *"R$ 137,50, falta R$ 12,50"*). Essa micro-tensão segura a retenção no terço final.
- **45,0 s – 55,0 s (Clímax + Selo)**: Meta exata batida (`"R$ 150 · 11 ITENS"`) + convite direto.

### 1.2. Arco do Custo Invisível (*Myth vs. Math Arc* — `35 s a 55 s`)
- **0,0 s – 3,0 s (Quebra de Crença)**: *"Comprar o insumo mais barato por quilo é o que está comendo o seu lucro."*
- **3,0 s – 15,0 s (O Erro Comum)**: Mostra o produto padrão que perde peso/volume no preparo (água evaporando, quebra técnica, retrabalho).
- **15,0 s – 35,0 s (A Prova Técnica)**: Mostra o produto superior (ex.: 80% lipídios, alta concentração, equipamento digital) e faz a conta de rendimento na tela (`-15% de uso = +22% de margem`).
- **35,0 s – 45,0 s (Fechamento de Autoridade)**: CTA para solicitar teste ou tabela comparativa.

### 1.3. Arco de Diagnóstico e Paz de Espírito (*Clinical / Advisory Arc* — `30 s a 50 s`)
- **0,0 s – 3,0 s (Pergunta de Sintoma/Medo)**: *"Medo de perder o dente?"* / *"Recebeu notificação fiscal?"*.
- **3,0 s – 12,0 s (Desmistificação +Momento de Imagem 1)**: Tira a culpa do cliente e explica por que o problema acontece em fala contínua (`"dry": false`), inserindo a **Imagem 1** do usuário (`~4,5s–8,5s`, `fit: "contain"`, com transição de entrada `transition-zoom-01.html` e saída `transition-glow-01.html`).
- **12,0 s – 32,0 s (Explicação Técnica + Momento de Imagem 2)**: Fala contínua por blocos de parágrafo (sem picotar frases), inserindo a **Imagem 2** do usuário (`~20,0s–25,0s`, `fit: "contain"`, com transição `transition-zoom-02.html` e `transition-glow-02.html` cobrindo a emenda de bloco). **Proibido usar mais de 2 momentos de imagem ou reutilizar imagens de outros projetos.**
- **32,0 s – 42,0 s (Próximo Passo Seguro)**: Convite de baixo atrito para avaliação/diagnóstico.

### 1.4. Arco de Escala e Abastecimento (*Supply Power Arc* — `20 s a 30 s`)
- **0,0 s – 3,0 s (Choque de Volume)**: Paredão de carga + número em toneladas/caixas.
- **3,0 s – 14,0 s (Especificação + Aplicação)**: Qual marca chegou, qual a gramatura e para quem serve (padaria, obra, restaurante).
- **14,0 s – 24,0 s (Urgência Operacional)**: Lote disponível para retirada imediata ou entrega na rota do dia.

---

## 2. Mecânica de Retenção e Seamless Loop

1. **Re-Hooks de Meio de Vídeo (A cada `12 s – 15 s`)**:
   - Em vídeos acima de `30 s`, inserir uma frase de transição que reabre o loop:
     - *"Mas o principal não é nem isso..."*
     - *"E olha quanto ainda sobrou na calculadora..."*
     - *"Agora vem o detalhe que quase ninguém olha no rótulo..."*
2. **Encerramento sem "Cheiro de Fim"**:
   - **Proibido** dizer *"Então é isso pessoal"*, *"Por hoje é só"*, *"Espero que tenham gostado"*. No instante em que o cérebro detecta despedida, o usuário desliza o dedo.
   - O CTA deve ser a conclusão lógica imediata da última prova mostrada.

---

## 3. Matriz de CTAs de Alta Conversão (Otimizados para o Algoritmo)

| Objetivo | Tipo de CTA | Frase Falada no Vídeo (`Últimos 4 s`) | Frase na Legenda + Automação |
| :--- | :--- | :--- | :--- |
| **Alcance Viral (`Sends`)** | **Compartilhamento Direcionado** | *"Manda esse vídeo agora pro seu sócio antes de fechar o pedido da semana."* | `📲 Envie no WhatsApp ou Direct de quem decide as compras com você.` |
| **Comentários + Leads (`DMs`)** | **Palavra-Código (ManyChat / Direct)** | *"Comenta **TABELA** aqui embaixo que eu te mando a lista completa no Direct."* | `💬 Comente "TABELA" para receber o catálogo atualizado no seu Direct.` |
| **Retenção + Autoridade (`Saves`)** | **Salvamento Utilitário** | *"Salva esse vídeo pra você conferir essa proporção na hora de produzir."* | `🔖 Salve este post para consultar sempre que for calcular sua receita.` |
| **Venda Imediata (Local)** | **Rota / Pronta-Entrega** | *"Tira print dessa tela e traz aqui no balcão da [EMPRESA] hoje."* | `📍 Estamos na [ENDEREÇO] — estacionamento próprio e carregamento na hora.` |
