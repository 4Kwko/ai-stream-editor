# Frontend: status

Escrito por Claude Code; o GPT lê. Última atualização: 2026-10-30, lote "galeria de cortes automáticos".

## Lote de 2026-10-30: design system e acabamento (só frontend)

- **Direção visual "sala de corte":** tokens em `frontend/src/styles/tokens.css`, ícones próprios, filtros com padrão radio, card refeito, faixa de estado, atalhos de triagem (setas, G e N). Detalhes, referências e validação em `docs/implementation/design-system.md`.
- **Contrato e rotas:** nenhuma mudança.
- **Dependências novas:** `@fontsource/ibm-plex-sans` e `@fontsource/ibm-plex-mono` (OFL 1.1, fontes locais).
- **Correção:** com o backend fora do ar, o proxy do Vite responde 502/504. O cliente agora trata isso como "backend indisponível", e não como erro da API.
- **Verificação:**
  - typecheck, lint e build ok;
  - 40 testes;
  - navegador em modo demonstração: desktop, 400 px, estados de carregamento, vazio, processando, atenção, erro de avaliação e configuração aberta;
  - backend real fora do ar: aviso correto.
- **Não verificado:**
  - movimento reduzido por emulação (só por inspeção do CSS);
  - percurso com o backend real: os servidores estavam parados e não os iniciei.
- **Para o GPT (opcional):** uma `thumbnail_url` ou pôster por corte permitiria miniaturas e scrub no hover na galeria.

### Formato 16:9/9:16 e percurso real (2026-10-30, ~10:30)

**Extensão de formato consumida:**
- **Quadro do card:** segue o `output_format` de cada corte, com 9:16 quando o campo falta (cortes antigos).
- **Informação no card:** marca do formato no quadro, "Câmera em cima" quando `layout = camera_top_content_bottom`, e `layout_warning` como aviso.
- **Configuração:** seletor "Formato dos próximos cortes" (16:9 horizontal / 9:16 vertical) em "Configurar canal", que envia só `output_format`. Aparece só se o backend informa o campo, e o texto deixa claro que os cortes prontos não mudam.
- **Cortes novos:** detectados por `gallery_updated_at`, com `counts.completed` como reserva para backend antigo.

Testes: 44, todos passando.

**Percurso real, sem mock.** O backend 8765 já estava no ar (iniciado pelo GPT). Subi o Vite pelo inicializador oficial `python -m ai_stream_editor.local`, que reutilizou o backend, e o encerrei no fim; o backend continuou no ar.

| # | Passo | Resultado |
| --- | --- | --- |
| 1–2 | Abrir e ver o estado | `waiting`, "Aguardando uma gravação disponível neste canal.", canal joaomontagner, 0 VODs, última e próxima verificação |
| 3 | Cortes | Os 5 cortes reais, todos 9:16 (antigos, sem campo de formato). Mídia sintética, não Twitch |
| 4 | Reproduzir | Player só no clique, 1080×1920, 23,5 s, borda "no ar", um único `<video>` |
| 5 | Avaliar pelo teclado | No `4acfe103` (do meu projeto de teste): N gravou `rejected` na API e mostrou a marca vermelha; G voltou a `approved`. Revision 3 inalterada, nenhum job novo |
| 6 | Filtros | Gostei: 5. Não gostei e Para avaliar: estados vazios com texto próprio |
| — | Configuração | O painel abriu mostrando 16:9 marcado (o valor real). **Não salvei**, para não mudar a sua configuração real |
| 7 | Recarregar | Filtro "Gostei" restaurado, 5 marcas vindas do backend, nenhum vídeo carregado sozinho |
| 8 | MP4 | `download_url`: 206, `video/mp4`, `attachment; filename="corte_4acfe103.mp4"` (curl, sem gravar arquivo) |
| — | Console e tela estreita | Console sem erros numa aba nova; 400 px com 2 colunas e sem rolagem horizontal |

**Não comprovado no real:**
- um corte 16:9 ou com câmera em cima: ainda não existe nenhum na galeria real; foi coberto com mock e testes;
- a chegada de cortes por `gallery_updated_at`: não houve render novo durante o percurso;
- um VOD da Twitch: o canal não tinha gravação.

## Lote anterior: galeria de cortes automáticos

**Estado: interface integrada à API real em 8765** depois da confirmação do GPT no backend-status das 01:11. Percurso real abaixo.

- **Coberto:** a galeria, a avaliação e o download, com os cortes reais existentes (mídia sintética de projetos locais).
- **Não comprovado:** a chegada automática de cortes vindos da Twitch. O canal `joaomontagner` não tinha VODs, segundo a descoberta real do GPT, e a interface mostra esse estado.

### Percurso real (2026-10-30, ~01:15–01:20, Vite 5173 e API 8765 já em execução)

| # | Passo | Resultado observado |
| --- | --- | --- |
| 1 | Abrir | Página carregou sem mock |
| 2 | Estado da automação | `waiting`: "Aguardando uma gravação disponível neste canal.", canal `joaomontagner`, 0 VODs processados, última e próxima verificação (intervalo de 300 s) |
| 3 | Cortes gerados | "Todos" listou os 5 itens de `GET /gallery`, todos `source.type: local`, sem `next_cursor`. Não são cortes automáticos da Twitch |
| 4 | Reproduzir | Um `<video>` montado só no clique: 1080×1920, 23,5 s, busca ok, sem erro |
| 5 | Avaliar | Só no corte do meu projeto de teste (`4acfe103`): Não gostei e depois Gostei. "Salvo: …" a cada clique; a API passou para `rejected` e voltou a `approved` com **revision 3 inalterada**. Nenhum job novo no projeto |
| 6 | Filtrar | Gostei: 5. Não gostei e Para avaliar: vazios, com as mensagens próprias |
| 7 | Recarregar | Filtro "Gostei" restaurado, avaliações vindas do backend, nenhum vídeo carregado sozinho |
| 8 | MP4 existente | `download_url` com `Range` (curl, sem gravar arquivo): 206, `video/mp4`, `attachment; filename="corte_4acfe103.mp4"`, `no-store` |
| — | Tela estreita e console | 400 px sem rolagem horizontal. Numa aba nova, console sem erros (só os avisos do Vite e do React) |

**Observação para o GPT:** o corte `53749628` estava `rejected` na primeira leitura do percurso e apareceu `approved` alguns minutos depois. O log de rede do navegador mostra que esta página não enviou nenhuma requisição para esse id: os únicos PATCHes foram os dois de `4acfe103`. Talvez tenha sido o smoke automático de vocês, que grava avaliação. Não reverti, porque não é um dado meu.

**Ajuste feito durante o percurso:** em `waiting`, o `message` do backend repetia o rótulo e aparecia em destaque de aviso. Agora o destaque fica só para `attention`, `configuration_required`, `stopped` e `disabled`; durante o processamento a mensagem aparece como texto simples.

### Para o GPT

1. **Rotas consumidas:**
   - `GET /automation` e `PATCH /automation`, só com `channel_login` e `enabled`;
   - `GET /gallery?review_status=&limit=20&cursor=`, repassando o `next_cursor`;
   - `PATCH /clips/{id}` com **somente** `{review_status}`, sem `expected_revision`, porque avaliar não depende de revisão;
   - `preview_url` para assistir e `download_url` para baixar.

   A minha proposta anterior (`/automation/status`, `PUT /rating`) foi descartada em favor do contrato.
2. **Pedido (média): totais por `review_status`.** O contrato não traz totais, então os filtros aparecem sem contagem e não há "quantidade pronta" de cortes, só VODs processados via `counts`. Sugestão: `counts: {pending, approved, rejected, all}` na resposta de `/gallery`, ou em `/automation`.
3. **Detecção de cortes novos.** A interface usa o aumento de `automation.counts.completed`. Se houver um sinal melhor (por exemplo um contador de cortes prontos ou `gallery_updated_at`), a troca é simples.
4. **Percurso real feito** (tabela acima). Falta a chegada automática de um VOD real, que depende de haver gravação no canal.
5. **Lançador.** Continua chamando `python -m ai_stream_editor.local`, sem mudança.

### Implementado

- **Tela principal = galeria.** Cards com "Assistir" (o player monta só no clique, um por vez, sem autoplay ao abrir), duração, origem, data, selo do estado, botões Gostei e Não gostei, e "Baixar MP4" quando há `download_url`.
- **Filtros:** Para avaliar (padrão), Gostei, Não gostei e Todos. O filtro escolhido é lembrado. Há "Carregar mais" com o cursor do backend.
- **Avaliação persistente:**
  - "Salvando…" e depois "Salvo: Gostei"; botões travados durante a gravação, para não duplicar;
  - dá para trocar a escolha;
  - em falha, a interface diz que não salvou e qual escolha continua registrada;
  - Não gostei não esconde nem apaga o corte.
- **Painel de automação:**
  - canal com link;
  - estado em PT-BR, incluindo "Aguardando uma gravação disponível neste canal." para canal vazio, que não é falha;
  - etapa do VOD ativo com "% desta etapa" ou "sem estimativa";
  - `message` do backend;
  - VODs processados, em processamento, na fila e com falha;
  - última e próxima verificação;
  - aviso de que a busca depende do app em execução no PC ligado.
- **Estados distintos:** `configuration_required` (sem campo de segredo), `attention` (falha parcial, sem bloquear os cortes prontos), `stopped`, `disabled` e rota ausente (404).
- **"Configurar canal"** com login público e liga/desliga, validação local e as mensagens 409/422 do backend.
- **Removido do fluxo e do código:** importação por caminho, projetos recentes, análise e render manuais, tempos, legendas, preview com aprovação, exportação com histórico. Não ficou seção avançada.

### Verificações

| Tipo | Resultado |
| --- | --- |
| `npm run typecheck`, `npm run lint` | Sem erros nem avisos |
| `npm test` (mock e fetch simulado) | 37 testes em 3 arquivos (ver lista abaixo) |
| `npm run build` | OK, JS 241 kB (76 kB gzip) |
| Navegador, modo demonstração | Galeria, avaliação com "Salvo: Gostei" e console sem erros depois de recarregar; 1440 px e 400 px sem rolagem horizontal |
| Navegador, backend real antes das rotas | Degradação correta com as rotas em 404: "O backend em execução ainda não oferece…" |
| Navegador, backend real com rotas | Percurso de 8 passos ok (tabela acima), com mídia sintética de projetos locais |
| VOD real / Twitch | **Não testado:** o canal não tinha VODs. A interface mostrou o estado `waiting` real |

Os 37 testes cobrem:
- canal sem VOD, configuração necessária, serviço parado, processamento com cortes chegando, falha parcial, API indisponível e rota 404;
- configuração do canal, inclusive o 409;
- ausência de controles de edição, player único e download;
- Gostei, troca de escolha e cliques repetidos;
- falha ao salvar, filtros e filtro vazio;
- recarga, paginação, aviso de cortes novos e teclado;
- cliente HTTP: rotas, corpo, erros, cancelamento e URLs.

### Arquivos deste lote

- **Reescritos:** `frontend/src/App.tsx`, `App.test.tsx`, `index.css`, `main.tsx`, `api/types.ts`, `api/client.ts`, `api/client.test.ts`, `api/mock.ts`.
- **Novos:** `components/AutomationPanel.tsx`, `components/GalleryCard.tsx`, `hooks/useAutomationStatus.ts`.
- **Removidos (componentes do editor):** `ClipEditor`, `ClipList`, `ClipPlayer`, `ExportHistory`, `ExportPanel`, `ImportPanel`, `JobProgress`, `JobWatcher`, `RecentProjects`, `useJob`, `clipDraft` e `validation`, com seus testes.
- **Docs:** `frontend/README.md`, `docs/implementation/frontend.md`, este arquivo, `README.md` (nova direção no topo, MVP anterior como histórico) e `docs/planning/product-brief.md` (D9, sucede D5 e D6, sem apagar).
- **Lançador:** sem mudança.

### Pendências

| Pendência | Prioridade | Responsável |
| --- | --- | --- |
| Primeiro VOD real do canal processado automaticamente; conferir a chegada na galeria | Alta | Usuário (gravação), GPT e Claude conferem |
| Origem da mudança em `53749628` | Baixa | GPT |
| Totais por `review_status` | Média | GPT (opcional) |
| VOD disponível no canal `joaomontagner` | Externa | Usuário, Twitch |

---

## Histórico: lote "fechar a interface do MVP" (2026-10-29), superado pela galeria

## Estado

**Pronto para o teste integrado do GPT:** projetos recentes, histórico de exportações, cancelamento de render/exportação, warnings e correção do sucesso vazio. Todos verificados no backend real (abaixo).

## Concluído neste lote

1. **Sucesso vazio (bug de prioridade alta).** O estado da análise agora é derivado de `analysis_status` e do job:
   - em andamento;
   - falha ("Analisar de novo");
   - cancelada ("Analisar de novo");
   - sucesso com cortes;
   - sucesso sem cortes;
   - não iniciada ("Analisar vídeo").

   No sucesso sem cortes aparece "Nenhum corte sugerido", com explicação e o botão "Escolher outro vídeo". Não há retry nem erro técnico.

   Um 409 ao iniciar a análise oferece "Recarregar projeto" e "Escolher outro vídeo", não a mesma ação. Há regressões automatizadas para o percurso novo e para reabrir o projeto.
2. **Projetos recentes** (`GET /projects`). Mostram nome, data, duração, estado da análise, nº de cortes e caminho; "Abrir" ou "Voltar".
   - Abrir usa `GET /projects/{id}` e `analysis_job_id`. Não inicia processamento: só acompanha o job se ainda estiver ativo e carrega os cortes se a análise terminou.
   - Correções, aprovação e preview vêm do backend.
   - Projeto ausente (404), ao abrir ou ao retomar após recarregar, mostra uma orientação.
   - Trocar de projeto com ajustes não salvos pede confirmação (`window.confirm`). Voltar sem trocar preserva o rascunho.
3. **Histórico de exportações** (`GET /clips/{id}/exports`) do corte selecionado.
   - Cada item mostra data, revisão, "versão atual"/"versão anterior" e caminho.
   - Carregamento, vazio e erro (com "Tentar de novo") têm estados próprios.
   - Um aviso diz que o registro não garante que o arquivo continue no lugar. Não há botão de abrir ou baixar.
   - O resultado da operação atual fica em outro bloco: "Exportação concluída nesta sessão".
4. **Cancelamento** de análise, render e exportação (`POST /jobs/{id}/cancel`).
   - O botão só aparece com job ativo e trava enquanto o pedido está em curso: "Enviando cancelamento…" e depois "Cancelamento solicitado", com aviso de que a operação pode terminar normalmente.
   - "Operação cancelada" só aparece quando o job chega a `canceled`.
   - Se o job terminar `succeeded`, o sucesso é mantido, com a nota "terminou antes de o cancelamento ter efeito".
   - Cancelar uma nova exportação não apaga o resultado anterior.
5. **Warnings.**
   - `job.warning` aparece como aviso em qualquer estado, sem virar erro.
   - Numa exportação com sucesso, o caminho continua visível com a frase "não é preciso exportar de novo por causa deste aviso".
   - Um warning de análise aparece acima da lista de cortes.
6. **Progresso por etapa.** O texto diz "N% desta etapa" ou "Sem estimativa para esta etapa". Não há porcentagem total nem tempo restante.
7. **409 ao salvar.** Aparece o botão "Recarregar versão do backend": recarrega os cortes e mantém o que foi digitado no formulário para conferir e salvar de novo. Um 409 na revisão oferece "Recarregar cortes".
8. **Tipos e cliente** atualizados para o contrato atual:
   - `Project`: `analysis_status`, `analyzed_at`, `clip_count`, dimensões de exibição;
   - `Job`: `warning`, `progress_scope`, tempos, `result.message`;
   - `ExportEntry`.

   Campos ausentes têm fallback: estado "não informado" e, sem `analysis_job_id`, o job guardado no `localStorage`.

## Lançador .exe (pedido do usuário, 2026-10-29)

`frontend/launcher/dist/AI Stream Editor.exe` é um atalho só para este PC. Fonte em `frontend/launcher/Launcher.cs`, compilado com o `csc.exe` do .NET Framework 4.8 que já vem no Windows (`npm run launcher`).

- **Serviços já no ar:** ele só abre o navegador.
- **Serviços parados:** executa `backend\.venv\Scripts\python.exe -m ai_stream_editor.local`, com `PYTHONUTF8=1` e cwd `backend`, como faz `scripts/start-local.ps1`. Espera `/api/health` e a interface em 5173, depois abre o navegador.
- **Por que não chama o `.ps1`:** para não precisar de `-ExecutionPolicy Bypass`.

Não altera o backend nem os scripts.

- **Verificado:** compilação; com os serviços já no ar, saída 0 e navegador aberto; fora da pasta do projeto, mensagem de erro clara e saída 1.
- **Não verificado:** a partida a frio (backend e Vite parados). Os servidores em execução não foram iniciados por mim, então não os encerrei para testar.
- **Para o GPT:** se mudar o módulo `ai_stream_editor.local` ou a forma de iniciar, avise aqui. O lançador depende desse comando.

## Percurso real (2026-10-29, sem mock, backend 8765 e Vite 5173 já em execução)

Fixtures sintéticas do `backend/.test-data`. Saídas em pasta de teste fora do projeto.

| # | Passo | Resultado observado |
| --- | --- | --- |
| 1 | Recarregar a página | Reabriu o último projeto: corte aprovado, revisão 3, legenda corrigida, preview carregado |
| 2 | Projetos recentes | Lista real com nome, data, duração, "Analisado", nº de cortes |
| 3 | Abrir `silence-10s.mp4` existente | "Nenhum corte sugerido" + "Escolher outro vídeo"; nenhuma chamada a `/analyze` |
| 4 | Novo projeto com `silence-10s.mp4` | Uma chamada `POST /analyze` (202), sucesso vazio, sem 409 e sem retry |
| 5 | Novo projeto com `fixture-ptbr-10min.mp4` | Etapa "Transcrevendo em PT-BR" com "Sem estimativa para esta etapa"; 1 corte |
| 6 | Cancelar render | "Cancelamento solicitado" durante o pedido. Depois "Geração do preview cancelada": job `canceled` na API, preview anterior continua `ready`, aprovar segue disponível |
| 7 | Editar a 2ª legenda, início 3:02,5 e fim 3:26,0 | Dois PATCHes; correção preservada, tempos recalculados, revisão 3, preview `stale` e aviso "Preview desatualizado" |
| 8 | Preview → aprovar → exportar | `corte_4acfe103.mp4`, 1080×1920 + áudio, 23,5 s (ffprobe); histórico com "revisão 3 · versão atual" |
| 9 | "Exportar de novo" + Cancelar | Pedido enviado, mas a exportação terminou antes: `succeeded` respeitado, nota exibida, `corte_4acfe103_2.mp4` (23,5 s), histórico com 2 itens |
| 10 | Recarregar | Estado e histórico preservados |
| 11 | Tela estreita (420 px) | Início, projetos recentes e histórico sem rolagem horizontal |

Console: sem erros depois da recarga. O único erro registrado ("message is not defined") veio de uma versão intermediária durante o hot reload, entre duas edições minhas, antes de recarregar. O código final passa no typecheck.

**Não verificado no real:** o cancelamento com efeito de uma exportação (a real terminou antes; esse caminho foi coberto com o mock) e o warning de sucesso vindo do backend real (exige falha de persistência simulada; coberto com o mock).

## Verificações automatizadas

| Verificação | Resultado |
| --- | --- |
| `npm run typecheck` | Sem erros |
| `npm run lint` (oxlint) | Sem avisos |
| `npm test` | 59 testes em 5 arquivos, todos passando |
| `npm run build` | OK, JS 270 kB (84 kB gzip) |

Testes novos:
- sucesso vazio, inclusive ao reabrir;
- 409 ao analisar;
- projetos recentes;
- confirmação ao trocar com rascunho;
- retomada após recarregar;
- projeto ausente;
- histórico;
- warning em sucesso;
- cancelar análise, render e exportação;
- sucesso antes do cancelamento;
- 409 ao salvar com recarga;
- progresso por etapa;
- rotas do cliente.

## Arquivos alterados neste lote

`frontend/src/`:
- `App.tsx` (reescrito) e `App.test.tsx`;
- `api/types.ts`, `api/client.ts`, `api/client.test.ts`, `api/mock.ts`;
- `components/JobProgress.tsx`, `components/ExportPanel.tsx`, `components/ClipEditor.tsx`;
- novos: `components/RecentProjects.tsx`, `components/ExportHistory.tsx`;
- `lib/time.ts`, `index.css`.

Também: `frontend/README.md`, `docs/implementation/frontend.md` e este arquivo. Nada fora de `frontend/` e dos meus documentos.

## Ainda com mock

Só o modo `?mock=1` (`src/api/mock.ts`), que segue as regras do contrato. Gatilhos:
- `silencio` no caminho: zero cortes;
- `falha` no caminho: análise com falha;
- `aviso` na pasta: warning;
- `falha` na pasta: exportação com falha.

O mock não comprova integração.

## Pedidos ao GPT

1. **Mensagem do sucesso vazio (baixa).** No job de análise com `clip_ids: []`, o `result.message` é o mesmo texto genérico ("revise o contexto"), por isso a interface não o mostra nesse estado. Se quiser explicar o motivo (silêncio, pouca fala), um campo próprio, por exemplo `result.empty_reason`, seria exibido.
2. **Fonte indisponível (média).** O Project não informa se o arquivo de origem ainda existe. Hoje isso só aparece como erro de job ao gerar preview ou exportar. Sugestão: `source_available` (ou equivalente) no Project, para avisar ao abrir.
3. Nenhuma outra extensão necessária. `expected_revision`, os dois PATCHes e o tratamento de 409 continuam.

## Pendências

| Pendência | Prioridade | Responsável |
| --- | --- | --- |
| Avaliar com um VOD real e representativo (vários cortes, duração longa, legibilidade e desempenho do polling) | Alta | Usuário autoriza a mídia; GPT e Claude executam |
| Decidir se o limite de 3–180 s da interface fica, muda ou sai | Média | Usuário |
| `source_available` e motivo do sucesso vazio | Média/baixa | GPT (opcional) |
| Atalhos de teclado no player | Baixa | Claude |

## Próximo passo

O GPT roda o seu teste integrado sobre esta versão (5173). Depois, com um VOD autorizado pelo usuário: revisar vários cortes em sequência, observando navegação, polling e legibilidade.
