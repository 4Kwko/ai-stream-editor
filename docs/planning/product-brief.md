# Brief do produto (S1.1)

Status: **em construção**. Conversa iniciada em 2026-10-29. Este documento só registra o que o usuário confirmou; sugestões do agente e pendências aparecem separadas.

> **Nota de 2026-10-30:** a decisão D9 (abaixo) muda a experiência principal. Ela sucede o controle manual de D5 e o fluxo "aprovar e exportar" de D6. Essas decisões continuam na tabela como histórico.

## Decisões confirmadas

| # | Tema | Decisão | Data |
| --- | --- | --- | --- |
| D1 | Público da primeira versão | Uso pessoal: só o João usa. Sem cadastro de clientes, cobrança ou recursos de serviço público no MVP | 2026-10-29 |
| D2 | Primeiro resultado útil | Cortes verticais prontos para revisar: (a) identificar momentos interessantes no VOD; (b) gerar os trechos em 9:16, com áudio e legendas; (c) assistir e aprovar ou descartar cada corte. A meta da primeira versão é entregar os arquivos de vídeo; o desenvolvimento pode ser em etapas | 2026-10-29 |
| D3 | Requisitos de qualidade dos cortes | Cada corte tem contexto suficiente para ser compreensível sozinho. Legendas legíveis | 2026-10-29 |
| D4 | Layout no MVP | Um único layout simples, ainda a definir. Reenquadramento inteligente, vários estilos e efeitos elaborados ficam para depois | 2026-10-29 |
| D5 | Controle manual no MVP | Aprovar ou descartar, com ajustes leves: ajustar início e fim do trecho; corrigir o texto das legendas; visualizar o resultado atualizado antes de aprovar; gerar o vídeo final com as alterações. Fora do MVP: timeline com várias faixas, junção de trechos, edição livre dos elementos | 2026-10-29 |
| D6 | Saída do corte aprovado | Exportar o corte aprovado em MP4 para uma pasta escolhida pelo João, já com os ajustes de início e fim e as correções de legenda aprovados. Publicação manual nas plataformas. Fora do MVP (possíveis evoluções): publicação direta, agendamento, conexão com contas | 2026-10-29 |
| D8 | Idiomas | VODs em português brasileiro (PT-BR). Legendas em PT-BR, sem tradução, no MVP. Nomes próprios, jogos e expressões em inglês são preservados quando fizerem parte da fala. Erros corrigidos manualmente na revisão (D5) | 2026-10-29 |
| D7 | Ambiente de execução | Interface, vídeos, revisão, render e exportação rodam no computador do João, com Windows. Sem depender de servidor externo hospedado no MVP | 2026-10-29 |
| D9 | Galeria de cortes automáticos (sucede D5 e o fluxo de revisão de D6) | A ferramenta busca sozinha os VODs do canal https://www.twitch.tv/joaomontagner, obtém a mídia, transcreve, analisa e gera os cortes verticais com áudio e legenda, sem etapas manuais. O João abre uma galeria de vídeos **prontos** e só marca Gostei ou Não gostei. Não ajusta início e fim, não corrige legendas, não escolhe layout, não dispara etapas. A avaliação não altera a mídia; Não gostei não apaga nada. O MP4 pronto fica acessível sem nova renderização. Sem publicação nas plataformas. A busca depende dos serviços em execução no PC ligado | 2026-10-30 |

## Em aberto

| # | Tema | Situação |
| --- | --- | --- |
| A1 | Origem do conteúdo (de quem são os VODs) | Separada do público. Não presumir que serão só as lives do próprio João. A definir. *Atualização 2026-10-30: D9 define o canal joaomontagner como fonte automática; outros canais ou arquivos locais não foram descartados* |
| A2 | Qual layout simples usar no MVP | A definir (D4) |
| A4 | Transcrição e análise: locais ou por API | Em aberto. Comparar qualidade, tempo de processamento, requisitos de hardware, custos e quais dados sairiam do computador. Não presumir GPU adequada nem autorização para enviar conteúdo a terceiros. Decide-se depois da avaliação do hardware (A5) e do orçamento |
| A5 | Hardware do computador (GPU, espaço livre) | Desconhecido. Necessário para A4 |
| A6 | Orçamento mensal | Em aberto; o teto será definido depois da pesquisa de custos. Em aberto não significa ilimitado. Ver requisitos da pesquisa de custos abaixo |
| — | Pergunta 8 da proposta S1 | Em conversa |

## Requisitos definidos pelo usuário para as pesquisas

- **Custos (A6):** comparar alternativas locais e pagas, mostrando custo estimado por hora de VOD separando transcrição e análise; projeção mensal para volumes de uso claramente indicados; moeda original, conversão para reais e data da consulta; limitações e possíveis custos adicionais.
- **Transcrição e análise (A4):** comparar qualidade, tempo de processamento, requisitos de hardware, custos e quais dados precisariam sair do computador.
- **Proibido sem autorização explícita do João:** executar serviços pagos, contratar planos, enviar conteúdo a terceiros.

## Sugestões do agente (não confirmadas)

- Desenhar a primeira versão para uso pessoal sem fechar a porta para alguns usuários convidados no futuro. Sugerido na pergunta 1; o usuário confirmou apenas o uso pessoal.
- Pergunta 2: começar com recorte central ou com câmera em cima e jogo embaixo, num layout fixo. O usuário confirmou só "um layout simples, a definir" (D4, A2).
