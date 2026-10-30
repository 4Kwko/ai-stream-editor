# S1: proposta de pesquisa e planejamento

Status: **proposta, não autorizada**. Data: 2026-10-29. Autor: Claude Code.

A S1 produz documentos para decidir o que construir primeiro e com quais tecnologias. Ela não cria projeto, não instala dependências e não escolhe a stack em definitivo sem aprovação do usuário em cada decisão.

## 1. O que bloqueia e o que não bloqueia

### Bloqueia o planejamento

| Item | Por quê | Como destravar |
| --- | --- | --- |
| Respostas do usuário às perguntas de produto (seção 2.1) | Sem saber para quem é e qual o primeiro resultado útil, qualquer arquitetura é chute | Uma conversa curta ou respostas por escrito na S1.1 |

Nada mais bloqueia escrever documentos.

### Não bloqueia o planejamento (necessário antes da implementação)

| Item | Quando passa a importar |
| --- | --- |
| Validação local do Claude Code (instruções, permissões, plugins, versão) | Antes da primeira tarefa que escreve código ou roda comandos no computador. Para documentos, as regras já estão no texto que o agente lê |
| GPU desconhecida | Ao decidir transcrição e encode locais (S1.4 trata como pergunta em aberto, com alternativas para os dois casos) |
| Repositório no OneDrive | Antes de baixar VODs, criar `node_modules`/`.venv` ou rodar testes com mídia |
| Fins de linha (`.gitattributes`) | Antes do primeiro commit |
| Commit inicial | Antes de worktrees ou de qualquer integração de branches |
| Licença da skill Remotion | Só se Remotion for escolhido e a skill for redistribuída ou copiada para o repositório |
| WSL | Só se uma dependência exigir Linux; opcional |
| `Claude outputs/settings.json` | Remoção após a validação local, com autorização |

## 2. Perguntas a resolver

### 2.1 Produto (bloqueiam; respostas do usuário)

1. Para quem é a primeira versão: só para as suas lives, para outros streamers, ou um serviço aberto?
2. Qual o primeiro resultado útil? Exemplo: "colo o link de um VOD e recebo 5 cortes verticais com legenda para revisar".
3. Quanto controle manual: aprovar cortes sugeridos, ajustar início/fim, editar legenda, ou edição completa numa timeline?
4. Publicação automática nas plataformas está no escopo inicial, ou basta exportar o MP4?
5. Onde roda: só no seu computador, num servidor, ou os dois?
6. Orçamento mensal aceitável para APIs pagas (transcrição, LLM), incluindo zero.
7. Idioma das lives e das legendas (só português, ou também inglês).
8. Existe código ou aprendizado do projeto Clipper (cortes verticais) para reaproveitar, ou o AI Stream Editor começa do zero?

### 2.2 Pesquisa (respondidas pelo agente na S1, com fontes)

- **Entrada de mídia:** formas de obter VODs da Twitch (download do próprio canal, API oficial, ferramentas como yt-dlp), limites e termos de uso; tamanho e duração típicos de um VOD; armazenamento necessário.
- **Direitos e privacidade:** termos da Twitch sobre reuso de VODs, música com direitos autorais nas lives, falas de terceiros no chat ou em call, dados pessoais (LGPD) em transcrições.
- **Detecção de momentos:** sinais disponíveis (transcrição, picos de áudio, mensagens do chat, clips criados pela audiência, marcadores do streamer) e abordagens (regras, LLM sobre transcrição, combinação). Como medir se um corte é bom.
- **Transcrição:** opções locais e em nuvem, custo por hora de áudio, qualidade em português, timestamps por palavra, necessidade de GPU.
- **Edição e render:** FFmpeg direto, Remotion ou outra; reenquadramento 16:9 → 9:16 (rosto, câmera, gameplay), legendas animadas, tempo de render por minuto de vídeo.
- **Interface do editor:** player com timeline, revisão de cortes, edição de legenda; bibliotecas existentes e o que elas exigem.
- **Publicação:** APIs do YouTube Shorts, TikTok e Instagram Reels, requisitos de aprovação de app, limites; ou exportação manual.
- **Ambiente:** o que roda bem no Windows nativo com Python 3.12, Node 24 e FFmpeg 9 já instalados; o que exigiria Linux/WSL ou GPU.

## 3. Entregáveis

Todos em Markdown, no repositório.

| Arquivo | Conteúdo |
| --- | --- |
| `docs/planning/product-brief.md` | Respostas da seção 2.1, público, primeiro resultado útil, fora de escopo |
| `docs/research/media-input-and-rights.md` | Entrada de VODs, termos de uso, direitos, privacidade |
| `docs/research/moment-detection.md` | Sinais, abordagens, como avaliar qualidade de um corte |
| `docs/research/transcription.md` | Opções, custo, qualidade, requisitos de hardware |
| `docs/research/editing-and-render.md` | Motores de edição e render, reenquadramento, legendas |
| `docs/research/editor-ui.md` | Padrões e bibliotecas para revisão e edição de cortes |
| `docs/research/publishing.md` | APIs de publicação ou exportação manual |
| `docs/planning/environment-requirements.md` | Requisitos de máquina, armazenamento, GPU, OneDrive, Windows/WSL |
| `docs/planning/architecture-options.md` | 2 ou 3 arquiteturas candidatas, com prós, contras, custo e riscos |
| `docs/decisions/ADR-0001...` | Uma ADR por decisão aprovada pelo usuário (stack, motor de render, transcrição, onde roda) |
| `docs/planning/mvp-plan.md` | Escopo do MVP, contratos entre módulos, sequência de tarefas de implementação com critérios de aceitação |
| `docs/planning/pre-implementation-checklist.md` | O que precisa estar resolvido antes da primeira linha de código (validação local, OneDrive, `.gitattributes`, commit inicial) |

Cada documento de pesquisa traz: pergunta, opções avaliadas, evidências com links, custo, riscos, recomendação e o que continua incerto.

## 4. Sequência de tarefas

| Tarefa | Entrada | Saída | Depende de |
| --- | --- | --- | --- |
| S1.1 Brief de produto | Respostas do usuário à seção 2.1 | `product-brief.md` | — |
| S1.2 Entrada de mídia e direitos | Brief | `media-input-and-rights.md` | S1.1 |
| S1.3 Detecção de momentos | Brief | `moment-detection.md` | S1.1 |
| S1.4 Transcrição | Brief; GPU como pergunta aberta | `transcription.md` | S1.1 |
| S1.5 Edição, render e interface | Brief | `editing-and-render.md`, `editor-ui.md` | S1.1 |
| S1.6 Publicação e ambiente | Brief | `publishing.md`, `environment-requirements.md` | S1.1 |
| S1.7 Opções de arquitetura | S1.2–S1.6 | `architecture-options.md` | S1.2–S1.6 |
| S1.8 Decisões | Escolhas do usuário sobre S1.7 | ADRs em `docs/decisions/` | S1.7 |
| S1.9 Plano do MVP | ADRs aprovadas | `mvp-plan.md`, `pre-implementation-checklist.md` | S1.8 |

S1.2 a S1.6 são independentes entre si e podem ser feitas em qualquer ordem, uma por vez.

## 5. Critérios de aceitação da S1

- Cada pergunta da seção 2.1 tem resposta do usuário registrada, ou está marcada como adiada com motivo.
- Cada documento de pesquisa cita fontes atuais (documentação oficial sempre que existir) e separa fato verificado de estimativa.
- Custos aparecem com unidade e data da consulta (por hora de áudio, por minuto de render, por mês).
- `architecture-options.md` compara pelo menos duas opções nos mesmos critérios: custo, complexidade, requisitos de hardware, tempo até o primeiro resultado útil, riscos.
- Toda escolha de stack tem ADR aprovada pelo usuário; nenhuma decisão aparece só dentro de um documento de pesquisa.
- `mvp-plan.md` divide a implementação em tarefas pequenas, cada uma com arquivos previstos, verificação e critério de aceitação.
- `pre-implementation-checklist.md` lista os itens da seção 1 que ainda faltam.
- Nenhum código de produto, projeto inicializado, dependência instalada ou mudança global durante a S1.

## 6. Fora de escopo da S1

Implementar qualquer parte do produto, criar projetos (React, Next.js, FastAPI, Remotion ou outros), instalar ferramentas, baixar VODs, enviar mídia a serviços externos, criar contas em APIs, operações Git de escrita.

## 7. Worktrees e paralelismo com um agente

- Na S1 não há paralelismo que justifique worktrees: um agente, documentos separados, uma tarefa por vez. O checkout único basta.
- Na implementação, worktrees passam a valer se o usuário abrir duas sessões do Claude ao mesmo tempo em tarefas que instalam dependências ou rodam servidores, ou para experimentos descartáveis (por exemplo, comparar dois motores de render).
- Pré-requisitos nessa hora: commit inicial, `.gitattributes` e, de preferência, repositório fora do OneDrive. Ficam no `pre-implementation-checklist.md`.
