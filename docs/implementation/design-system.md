# Design system: "sala de corte"

2026-10-30. Responsável: Claude Code. Código em `frontend/src/styles/tokens.css` (tokens) e `frontend/src/index.css` (componentes).

## 1. Auditoria (antes)

A interface da galeria funcionava. Visualmente, porém, era um tema escuro genérico.

| Problema | Impacto |
| --- | --- |
| Emojis 👍 👎 como ícones, sem sistema de ícones | Peso e estilo diferentes por sistema operacional; aspecto improvisado |
| Selo "Gostei"/"Para avaliar" no card **e** botão pressionado com a mesma informação | Redundância e excesso de pílulas |
| Filtros como pílulas soltas, sem semântica de grupo | A seleção mudava sem continuidade visual; o teclado só tinha Tab |
| Fonte do sistema e números sem fonte tabular | Sem identidade; durações e datas mal alinhadas |
| Tokens nomeados por valor (`--bg`, `--ok`), tema claro e escuro misturados | Trocar a paleta exigia mexer em componentes; durações literais (`0.3s`, `1.4s`) espalhadas |
| Quadros 9:16 vazios e altos, cards largos | Pouca densidade: 3 a 4 cortes por linha em 1440 px |
| Painel de automação em texto corrido | O estado só se lia lendo a frase inteira |
| Avaliar exigia o mouse, card a card | Triagem lenta, justamente na tarefa principal |
| Backend fora do ar aparecia como "erro 502" | O proxy do Vite responde 502, e a interface mostrava um erro técnico em vez de "backend indisponível" |

**Preservado:** o contrato da API, a avaliação sem atualização otimista, o player único montado no clique, os filtros lembrados, os estados de automação honestos, a paginação e os textos em PT-BR.

## 2. Pesquisa e curadoria

Fontes consultadas em 2026-10-30. A coluna "Uso" diz o que foi aproveitado.

| Referência | O que mostrou | Uso |
| --- | --- | --- |
| [Radix Toggle Group](https://www.radix-ui.com/primitives/docs/components/toggle-group) | Foco itinerante (roving), setas, Home/End, `data-state` | **Adaptado** no controle segmentado, sem a dependência |
| [WAI-ARIA APG: Radio Group](https://www.w3.org/WAI/ARIA/apg/patterns/radio/) | `radiogroup`/`radio`, `aria-checked`, as setas selecionam | **Adotado** como semântica dos filtros |
| [Motion Primitives: Animated Background](https://motion-primitives.com/docs/animated-background) | Um fundo que desliza até o item ativo | **Adaptado** em CSS (transform), sem Motion |
| [Motion: transitions](https://motion.dev/docs/react-transitions) | Tween de 0,3 s, springs com `bounce` | **Descartado como dependência**: as transições são curtas e de estado, e CSS resolve. Usado só para calibrar as durações |
| [shadcn/ui Button](https://ui.shadcn.com/docs/components/button) | Variantes (default, outline, ghost…), carregamento com spinner dentro do botão | **Adaptado**: três variantes (primary, secondary, quiet) e um só tamanho compacto |
| [Uiverse.io](https://github.com/uiverse-io/galaxy) | Galeria MIT de efeitos CSS (glow, gradientes, neumorphism) | **Descartado**: não pertence à linguagem; nenhum efeito copiado |
| [React Bits](https://github.com/DavidHDev/react-bits) | Textos animados, fundos com shader; licença MIT + Commons Clause | **Descartado**: efeito de vitrine, sem problema real a resolver |
| [Aceternity UI](https://ui.aceternity.com/components) | Spotlight, bordas brilhantes, cards 3D (Tailwind + Motion) | **Descartado**: exatamente o "slop" a evitar |
| [21st.dev](https://21st.dev/) | Catálogo de componentes shadcn/Tailwind; licença por item, não declarada no site | **Descartado**: exige Tailwind e não tem licença clara |
| [IBM Plex](https://github.com/IBM/plex) | Família Sans e Mono para interface, licença OFL 1.1 | **Adotado**: Plex Sans e Plex Mono via `@fontsource` (local, offline) |
| [Linear: redesign da UI](https://linear.app/now/how-we-redesigned-the-linear-ui) | Tema gerado de poucas entradas, base mais neutra, menos ruído, cuidado com contraste | **Princípio**: paleta base pequena com aliases semânticos; neutro sem tom azul |
| [Figma: UI3](https://www.figma.com/blog/behind-our-redesign-ui3/) | Conteúdo primeiro, painéis recolhíveis, ícones uniformes, ferramentas contextuais | **Princípio**: os vídeos dominam a tela; a configuração fica recolhida |
| [DaVinci Resolve: Media Pool](https://ltbits.github.io/davinci-resolve-manuals/DR18/DR18-RM04-TheCutPage.pdf) | Grade de miniaturas com metadados no quadro, scrub ao passar o mouse | **Princípio**: timecode sobre o quadro, densidade. Scrub **adiado**: exige miniaturas do backend |
| [Lightroom: triagem com P/X/U](https://laurashoe.com/2019/05/01/cull-photos-faster-in-lightroom-classic-with-auto-advance) e [atalhos](https://photofocus.com/photography/lightroom-shortcuts-for-faster-culling/) | Marcar e avançar, bandeira no canto da miniatura | **Adaptado**: G/N com avanço automático em "Para avaliar"; marca no canto do quadro |
| [Frame.io: página do player](https://help.frame.io/en/articles/7786-player-page-features) | `[`/`]` para o próximo ou anterior, estados Needs Review/Approved | **Adaptado**: setas percorrem a grade |

Não abriram: a página de ajuda da Adobe (403), a de licença do Uiverse (403) e os tokens do Material 3 (página só renderiza com JS). Usei as fontes alternativas listadas acima. Nenhum código de terceiros foi copiado: as implementações são próprias, guiadas por essas referências.

## 3. Direção visual

**Conceito: sala de corte.** É uma ferramenta de triagem de vídeo, não um painel SaaS.

- **Superfícies:** grafite neutro, sem tom azul, como em salas de cor, para não enviesar a leitura do vídeo.
- **Acento:** um único laranja-sinal, a luz de tally/REC das câmeras. Marca o que está ativo: o filtro, o foco, o corte que está tocando, o progresso, a ação primária.
- **Estados:** verde, vermelho e amarelo, sempre separados do acento.
- **Personalidade:** vem da tipografia (Plex Sans com números em Plex Mono, como timecode), da marca de tally no logotipo e da borda "no ar" do corte que toca. Não vem de efeitos.

**Paleta provisória** (`tokens.css`, bloco "Paleta base"). Contraste WCAG medido:

| Texto | Pior fundo | Contraste |
| --- | --- | --- |
| Primário `#ededee` | Superfície hover | 13,3:1 |
| Secundário `#b3b6bb` | Superfície hover | 7,6:1 |
| Terciário `#8f939a` | Superfície hover | 5,0:1 |
| Acento `#f08a3c` como texto | Superfície hover | 6,2:1 |
| Texto sobre o acento `#1c1006` | Acento | 7,5:1 |
| Sucesso, perigo, aviso | Superfície hover | 6,8 / 4,9 / 9,1 :1 |
| Desabilitado `#4c5056` | — | 2,2:1 (isento de AA por ser inativo) |

Todo texto passa em AA. Limitação: a borda dos campos tem 1,7:1. O campo de canal é identificado também pelo rótulo e pelo fundo diferente; se a WCAG 1.4.11 virar requisito, basta subir o token `--color-border-strong`.

**Tipografia:**
- Plex Sans 400/500/600 na interface;
- Plex Mono 400/500 em durações, datas, contadores e atalhos;
- escala densa: 11, 12, 13 (base), 15 e 18 px.

**Espaçamento:** base de 4 px (`--space-1` a `--space-8`). O ritmo é deliberado: mais espaço entre seções (20) do que dentro delas (8 a 12).

**Forma:**

| Elemento | Raio |
| --- | --- |
| Quadros e painéis | 6 px |
| Controles | 4 px |
| Marcas e kbd | 2 px |
| Indicador de estado (ponto) | Redondo; é o único |

A elevação vem da luminosidade da superfície (fundo → superfície → elevada → hover → ativa). Há uma única sombra, reservada a camadas flutuantes e hoje sem uso.

## 4. Movimento

| Token | Duração | Uso |
| --- | --- | --- |
| `--motion-instant` | 90 ms | Pressão (scale 0,98) |
| `--motion-fast` | 160 ms | Hover, foco, cor, interruptor |
| `--motion-normal` | 240 ms | Indicador do filtro, painel recolhível, marca de avaliação, avisos que entram |
| `--motion-loop` | 1,6 s | Só enquanto há trabalho: tally pulsando, barra sem estimativa, esqueleto |

Curvas: `--ease-standard` (entra rápido, assenta devagar) e `--ease-exit`. As animações usam `transform` e `opacity`. As exceções são `grid-template-rows` no painel recolhível e `width` no indicador do filtro, ambas em elementos pequenos.

Com `prefers-reduced-motion`, as durações vão a 0 e os loops param: a barra sem estimativa fica estática e semitransparente.

Cada animação tem uma função:
- o indicador mostra para onde a seleção foi;
- o painel recolhível mantém o contexto ao abrir;
- a marca e o "Salvo" confirmam a avaliação;
- o tally pulsando diz "processando agora".

## 5. Componentes

| Componente | Arquivo | Origem |
| --- | --- | --- |
| Tokens | `styles/tokens.css` | Novo |
| Ícones (10 desenhos próprios, grade de 16, traço 1,5; "não gostei" é o "gostei" girado) | `components/Icon.tsx` | Novo; substitui os emojis |
| Controle segmentado (radiogroup, roving, indicador deslizante) | `components/SegmentedControl.tsx` | Novo; adaptado de Radix, APG e Motion Primitives |
| Botão: `.btn` com `--primary`, `--secondary`, `--quiet` e `--sm` | `index.css` | Refeito; estados completos |
| Faixa de estado (tally, etapa com barra, metadados em mono, configuração recolhível, interruptor) | `components/AutomationPanel.tsx` | Refeito |
| Card de corte (quadro com timecode, marca de avaliação, borda "no ar", par Gostei/Não gostei, "Salvo" com ícone, download discreto) | `components/GalleryCard.tsx` | Refeito; os selos redundantes saíram |
| Esqueleto de carregamento, estado vazio com ícone, avisos | `App.tsx`, `index.css` | Novos |
| Atalhos de triagem (setas, G, N, avanço automático) | `App.tsx` | Novo |

**Contrato de consistência.** Os estados seguem a mesma convenção em todos os controles:

| Estado | Tratamento |
| --- | --- |
| Hover | A superfície sobe um degrau |
| Pressão | `scale(0.98)` |
| Foco | Anel de 2 px no acento |
| Desabilitado | Opacidade 0,45 |
| Selecionado | Acento (filtros) ou cor de estado (avaliação) |

Componentes do mesmo nível têm o mesmo raio, a mesma altura (28 ou 32 px) e a mesma família de transição.

## 6. Como trocar a paleta

1. Editar só o bloco "Paleta base" de `frontend/src/styles/tokens.css`, nos valores de `--palette-*`.
2. Conferir o contraste com a tabela acima.

Os componentes não citam hex nem durações. A varredura de 2026-10-30 não encontrou literais de cor ou de tempo em `index.css` nem nos componentes, exceto o preto translúcido do timecode sobre o vídeo.

Para um tema claro: redefinir os aliases `--color-*` num seletor, por exemplo `[data-theme='light']`.

## 7. Próximas melhorias, por impacto

1. **Miniaturas (pôster) dos cortes:** depende do backend. Permitem ver o conteúdo sem dar play e o scrub no hover, como no Media Pool do DaVinci. É o maior ganho de reconhecimento na grade.
2. **Visualização ampliada (modo foco):** um corte por vez, em tamanho grande, com G/N e avanço automático, para triagem longa.
3. **Contadores por filtro**, quando o contrato trouxer os totais.
4. **"Desfazer"** logo depois de avaliar pelo teclado, como Ctrl+Z na triagem.
5. **Tema claro** gerado pelos mesmos aliases, se houver pedido.
