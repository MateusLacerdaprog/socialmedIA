# Módulo 06 — Posicionamento Empresarial e Adaptação por Tipo de Negócio (Etapa 7)

> **Princípio Diretor:** Viralizar sem posicionamento atrai curiosos; posicionar sem engenharia de retenção gera vídeos ignorados. A skill `socialmedia` adapta automaticamente **ritmo de corte, paleta de cores, tipografia, vocabulário e gatilhos psicológicos éticos** ao arquétipo exato da empresa.

---

## 1. Os 7 Pilares do Posicionamento Empresarial em Vídeo

1. **Construção de Autoridade Técnica**: Mostrar o *porquê* por trás do produto (ex.: percentual de lipídios, resistência estrutural do material, precisão da fresadora a laser) em vez de usar adjetivos vazios (*"o melhor"*, *"incrível"*).
2. **Confiança e Transparência**: Exibir o produto aberto, o rótulo real, a calculadora somando na frente da câmera ou o equipamento funcionando ao vivo.
3. **Prova Social Operacional**: Filas reais no balcão, caminhões descarregando, pedidos sendo separados com nome da cidade do cliente (ex.: cliente vindo de outra cidade buscar mercadoria) ou central de WhatsApp ativa.
4. **Identidade Visual Consistente**: Manter a mesma família tipográfica, coordenada de título (`y=230`) e estilo cromático (`amber`, `paper` ou `night`) em toda a grade do perfil.
5. **Storytelling Empresarial Real**: Transformar a operação diária (chegada de carreta, teste de bancada, dúvida de balcão) em narrativa útil para o comprador.
6. **Gatilhos Psicológicos Éticos**:
   - *Ancoragem numérica*: Mostrar o rendimento total por caixa/fardo antes do preço unitário.
   - *Aversão à perda*: Mostrar o desperdício causado pela escolha errada de insumo/serviço.
   - *Especificidade*: Números quebrados e reais (`R$ 137,50`, `32 toneladas`, `15% menos`) geram mais credibilidade imediata do que números genéricos.
7. **Diferenciação Competitiva**: Nunca atacar concorrentes pelo nome; diferenciar-se pelo domínio técnico, pronta-entrega e clareza de informação.

---

## 2. Regras Automáticas de Edição por Tipo de Empresa (7 Arquétipos Obrigatórios)

### 2.1. Loja de Material de Construção / Home Center
- **Estilo Visual (`editonny`)**: `amber` (alto contraste industrial: preto `#121318`, amarelo obra `#FFDE00`, laranja `#FF6B00`).
- **Ritmo de Corte**: Rápido (`mediana 1,70 s`), cortes secos com `impacto` (`1.45×`) em testes de resistência ou preços de lote.
- **Enquadramento Dominante**: Pátio de cargas / paletes de cimento, pisos e ferragens + demonstração prática nas mãos (comparando bitola de fio, resistência de argamassa ou cobertura de tinta).
- **Elementos Gráficos Obrigatórios**: `counter` de custo por metro quadrado ($\text{R\$}/\text{m}^2$), seta/círculo (`pointer`) indicando especificação ABNT e selo `"PRONTA ENTREGA NA OBRA"`.
- **CTA Padrão**: *"Manda pro seu mestre de obras ou comenta **ORÇAMENTO** com a metragem."*

### 2.2. Supermercado / Atacadista / Distribuidora de Alimentos
- **Estilo Visual (`editonny`)**: `amber` + selo verde `#16A34A` no fechamento (`[OBSERVADO — cliente]`).
- **Ritmo de Corte**: Dinâmico (`mediana 1,65 s – 1,95 s`), J-cut de `4 frames`, zero pausas de caminhada entre corredores.
- **Enquadramento Dominante**: Corredor abastecido até o teto (`Volume Shock`) + apresentador com calculadora/produto na mão.
- **Elementos Gráficos Obrigatórios**: Título de desafio fixo em `y=230–260`, `counter` acumulativo em `x=330, y=1170` (`prefix: "R$"`) e `stamp` final com quantidade de itens.
- **CTA Padrão**: *"Salva a lista antes de passar no caixa e manda no grupo da família / pro seu comprador."*

### 2.3. Clínica (Odontologia, Medicina, Estética, Saúde)
- **Estilo Visual (`editonny`)**: `paper` (fundo claro `#FFFFFF`, texto escuro `#1A1A2E`, destaque clínico sóbrio `#6B4C9A` ou `#2563EB`).
- **Ritmo de Corte (Fala Contínua Sem Picotar)**: Fluido e natural (`"dry": false` no `edl.json`, blocos contínuos de parágrafo de **`4,0 s a 12,0 s`** (PLAYBOOK §0), máx. 5 a 8 blocos em 50s, cortando apenas pausas longas entre parágrafos `>= 0,65 s`). Sem zooms bruscos de `1.45×` (usar apenas `base 1.08×` e `destaque 1.25×` suave em `0,7s`).
- **Imagens / B-rolls (Regra dos 2 Momentos + Transição Obrigatória)**:
  - **PROIBIDO** reutilizar imagens de projetos anteriores (cada vídeo usa exclusivamente os arquivos enviados pelo usuário para aquele vídeo).
  - Inserir imagens em **apenas 2 momentos cirúrgicos** do vídeo (Momento 1 na dor/sintoma inicial `~4,5s–8,5s`; Momento 2 na explicação técnica `~20,0s–25,0s`, cobrindo emenda de bloco da fala).
  - **Transição Obrigatória (PRIORIDADE)**: Toda imagem entra com `transition-zoom-0X.html` + card arredondado `fit: "contain"` (`x=50, y=520, w=980, h=654, border-radius=36px`) em animação elástica (`back.out(1.6)`) + zoom suave (`1.00× → 1.10×`) + SFX (`whoosh` + `photo` + `pop`), e sai com `transition-glow-0X.html`.
- **Elementos Gráficos Obrigatórios**: Pílula de pergunta acolhedora em `y=230–250`, legendas limpas de no máximo `3 palavras` (`maxWords: 3`), zero efeitos sonoros de caixa registradora. Respeito absoluto às normas do CFM/CFO.
- **CTA Padrão**: *"Salve este vídeo para tirar suas dúvidas na consulta ou envie para alguém da família que precisa saber disso."*

### 2.4. Indústria e Transformação B2B
- **Estilo Visual (`editonny`)**: `night` (azul escuro profundo `#0B0F19`, ciano técnico `#38BDF8`, verde eficiência `#22C55E`).
- **Ritmo de Corte**: Preciso (`mediana 2,00 s – 2,40 s`), sincronizado com o ciclo das máquinas (prensas, envase, corte a laser, paletização).
- **Enquadramento Dominante**: Planos abertos de linha de produção + close técnico em controle de qualidade/laboratório + especialista com EPI.
- **Elementos Gráficos Obrigatórios**: Indicadores de capacidade produtiva (`toneladas/hora`, `% de pureza`, `tolerância em mm`), gráficos de rendimento (`gauge` / `chart`).
- **CTA Padrão**: *"Comente **FICHA** para receber a especificação técnica e cotação para CNPJ no Direct."*

### 2.5. Restaurante / Gastronomia / Padaria / Confeitaria
- **Estilo Visual (`editonny`)**: `amber` quente (sem cobrir o centro do quadro `y=500–1050`, onde está o *food porn*).
- **Ritmo de Corte**: Muito rápido no preparo (`0,8 s – 1,5 s` nos cortes de faca, chapa chiando, queijo esticando) + `2,2 s` na finalização/mordida.
- **Enquadramento Dominante**: Close-up macro (`45°` e `90° top-down`) com iluminação lateral destacando vapor, brilho e textura.
- **Áudio Especial**: Preservar ASMR real da cozinha (crocância, chapa, forno) a `-18 dB` junto com a locução a `-14 LUFS`.
- **CTA Padrão**: *"Marca nos comentários quem vai dividir esse [PRATO] com você hoje à noite!"*

### 2.6. Escritório (Advocacia, Contabilidade, Engenharia, Consultoria Financeira)
- **Estilo Visual (`editonny`)**: `paper` ou `night` (tipografia editorial limpa, sem amarelo neon agressivo).
- **Ritmo de Corte**: Firme e articulado em blocos de parágrafo (`4,5 s – 11,0 s`, `"dry": false`), com até **2 momentos** de imagem/evidência com transição obrigatória (`transition-zoom` / `transition-glow`) ou `Frame Panels` (`frame.box: [36, 912, 1008, 990]`).
- **Enquadramento Dominante**: Mesa de reunião/escritório com iluminação suave e microfone de lapela visível (sinal de produção intencional).
- **CTA Padrão**: *"Salve para revisar com seu contador/jurídico e envie no Direct do seu sócio."*

### 2.7. E-commerce / D2C (Moda, Eletrônicos, Casa, Cosméticos)
- **Estilo Visual (`editonny`)**: Adaptável (`paper` para skincare/moda; `amber`/`night` para tech/ferramentas).
- **Ritmo de Corte**: Hiper-dinâmico (`mediana 1,30 s – 1,80 s`), abertura obrigatória com *unboxing* ou teste do produto em uso no primeiro segundo (`0,0 s`).
- **Enquadramento Dominante**: POV (primeira pessoa) segurando o produto + comparativo lado a lado (`split screen` ou `before-after`) + prova da embalagem de envio.
- **Elementos Gráficos Obrigatórios**: Badge de benefício principal em `y=230`, checklist de 3 diferenciais (`completed checklist`) e chamada de código no rodapé.
- **CTA Padrão**: *"Comenta **QUERO** que te mando o link direto com cupom no seu Direct agora."*

---

## 3. O que viralizou de verdade, por tipo de empresa `[MEDIDO n=27 — 20/10/2026]`

"×" = views do Reel ÷ mediana de views da própria conta.

| Empresa | Padrão observado | Evidência |
| :--- | :--- | :--- |
| **Material de construção** | **série de reforma real** com episódio numerado, criadores, loja como cenário da solução | 43× e 29× a mediana da conta |
| **Supermercado** | criador encena **tipos de cliente** ou faz **receita** com produtos da loja; programa de fidelidade na legenda | 204× e 182× |
| **Varejo casa/eletro** | história pessoal (Dia dos Pais) com o produto de presente; celebridade testando na loja | 8× e 5× |
| **Clínica** | 1 mito por vídeo, profissional da clínica falando, cores da marca, CRO na tela | 6,9× |
| **Indústria** | **presença em evento** que o público ama + diretor com crédito na tela | 68× |
| **Restaurante** | escassez real (ex.: "último dia") com prato parado, ou criador provando o cardápio com macro de comida | 23× e 15× |
| **Escritório/serviços** | especialista explicando **mudança com prazo real** (lei/imposto), caixa fixa com o gancho | 85× |
| **E-commerce** | celebridade + data comemorativa + cartão final com promessa | 2,6× |
| **B2B (IA/automação)** | talking head com dor específica e numerável do cliente | 12,9× (conta pequena) |

**Regra 0 de posicionamento:** pelo menos **15 de 27** virais são **colaboração** (criador `#publi`, celebridade, série, patrocínio). Para empresa local, planeje **colab com criador local + série numerada** antes de discutir corte e zoom. A edição sozinha não substitui a distribuição do post colaborativo.

**Gatilhos éticos vistos:** prazo real, escassez real (fim de campanha), prova social por pessoa real com nome e cargo, identificação ("qual tipo de cliente você é?") e autoridade por profissional habilitado. A skill **nunca** cria número, depoimento ou prazo.

**Memes de terceiros (`memes_cortados/`) em conta de empresa:** não usar o clipe. Use o **formato** encenado pela equipe (ver módulo 08 §0).
