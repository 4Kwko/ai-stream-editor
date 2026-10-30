# Frontend: decisões de implementação

2026-10-29, atualizado em 2026-10-30. Responsável: Claude Code. Execução e verificação em `frontend/README.md`; estado atual em `docs/coordination/frontend-status.md`.

## Galeria de cortes automáticos (2026-10-30, decisão D9 do brief)

A galeria substitui o editor manual como experiência principal. Foram removidos da interface e do código:
- importar por caminho;
- projetos recentes;
- análise e render manuais;
- ajuste de tempos;
- edição de legendas;
- preview com aprovação;
- exportação com histórico.

Os arquivos removidos foram `ClipEditor`, `ClipList`, `ClipPlayer`, `ExportHistory`, `ExportPanel`, `ImportPanel`, `JobProgress`, `JobWatcher`, `RecentProjects`, `useJob`, `clipDraft` e `validation`, com seus testes. Não ficou seção avançada.

| Tema | Escolha | Motivo |
| --- | --- | --- |
| Fonte dos dados | `GET /automation`, `GET /gallery`, `PATCH /clips/{id}` (`review_status`), `download_url` (`GET /clips/{id}/file`) | Contrato publicado pelo GPT. A proposta anterior do frontend (`/automation/status`, `PUT /rating`) foi descartada |
| Gostei / Não gostei | `approved` / `rejected`; "Para avaliar" = `pending` | O contrato reaproveita `review_status`. Avaliar não muda revisão nem mídia |
| Gravação da avaliação | Sem atualização otimista: botões travados e "Salvando…" até a resposta; erro mostra o que continua registrado | Não fingir que salvou; evitar duplicatas |
| Players | Um por vez, montado no clique; sem autoplay ao abrir a galeria | Evita dezenas de `<video>` e som inesperado |
| Paginação | 20 por página, "Carregar mais" repassando o `next_cursor` opaco; troca de filtro reinicia | Contrato (1–50) |
| Totais por filtro | Não exibidos | O contrato não os oferece; a tela mostra só quantos estão carregados |
| Atualização | Status a cada 10 s com a aba visível, backoff até 60 s em erro, uma consulta por vez, cancelada ao desmontar | Limitar consultas. Quem processa é o backend |
| Cortes novos | `counts.completed` maior que no último carregamento: carrega sozinho se a lista está vazia; senão aviso "Mostrar" | Não reordenar o que o usuário está vendo |
| Estados da automação | Texto por `status`; `waiting` sem VODs processados = "Aguardando uma gravação disponível neste canal." | Canal vazio não é falha; `configuration_required` e `attention` aparecem à parte |
| Configuração | Login público do canal + liga/desliga, validados (`[a-z0-9_]{3,25}`, aceita colar a URL do canal) | Sem credenciais; o 409 com VOD ativo aparece como mensagem |
| Rota ausente (404) | "O backend em execução ainda não oferece…" | Backend anterior à extensão; sem inventar estado |
| Filtro | Lembrado no `localStorage` | Conveniência local; as avaliações ficam no backend |

## Histórico: editor manual (2026-10-29), superado por D9

## Base

- React 19.3, TypeScript 7.0, Vite 8.3 (template oficial `create-vite@9.3.3 react-ts`). Versões consultadas no registro npm em 2026-10-29.
- Sem biblioteca de estado, componentes, roteamento ou player: `useState` no `App`, `<video>` nativo, CSS próprio com variáveis e tema claro/escuro pelo sistema.
- Dependências de desenvolvimento adicionadas: `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`. Justificativa: testes de componentes e do cliente sem navegador real. Nenhuma dependência de produção além de `react` e `react-dom`.

## Decisões reversíveis

| Tema | Escolha | Motivo |
| --- | --- | --- |
| Acesso ao backend | Proxy do Vite em `/api` (`changeOrigin: true`) | Evita CORS. O Host enviado (`127.0.0.1:8765`) passa no TrustedHost do backend e o Origin (`127.0.0.1:5173`) está na lista dele |
| Entrada do vídeo | Campo de caminho absoluto, aspas removidas | O navegador não fornece caminho real de arquivo |
| Pasta de exportação | Campo de caminho, lembrado no navegador; rejeita pasta de rede | Sem seletor nativo honesto; o contrato proíbe rede |
| Limites do corte | 3 s a 3 min; fim não passa de `duration_seconds` | Escolha de UX da interface, não requisito confirmado do produto. O backend aceita qualquer intervalo positivo dentro do vídeo. O Shorts aceita até 3 min. A decisão final é do usuário |
| `vite preview` (4173) | Configurado, mas não validado | A porta 4173 não está na lista de origens do backend; usar `npm run dev` (5173) |
| Formato de tempo | `m:ss.d` / `h:mm:ss.d`, aceita vírgula | Precisão de décimos basta para ajuste manual |
| Salvar texto e tempos | Dois PATCHes: legendas primeiro, tempos depois | Contrato v1: legendas enviadas precisam de tempos relativos aos novos limites, que o frontend não sabe calcular |
| Concorrência | `expected_revision` em todo PATCH | Detecta edição sobre versão antiga (409) |
| Aprovação | Só com preview atual e sem ajustes não salvos | O usuário aprova o que viu, que é o que será exportado |
| Estado do preview | `preview_status` do backend; assinatura local como reforço | Ver `previewState` em `src/lib/clipDraft.ts` |
| Progresso | "N% desta etapa"; barra indeterminada quando `progress` é null | `progress_scope: stage`: o percentual recomeça a cada etapa. Sem total nem tempo restante inventados |
| Retomada | Último projeto no `localStorage`; o job de análise vem de `Project.analysis_job_id` | O `localStorage` do job só vale para backends sem esse campo |
| Estado da análise | Derivado do job e de `analysis_status`: em andamento, falha, cancelada, sucesso com/sem cortes, não iniciada, desconhecido | Sucesso com zero cortes é resultado válido. O backend recusa reanálise (409), então a interface oferece outro vídeo |
| Projetos recentes | Lista na tela inicial; abrir não processa nada | Sem roteamento: a tela inicial e o projeto alternam por estado |
| Rascunho ao trocar de projeto | `window.confirm` | Nativo, acessível por teclado, sem biblioteca de modal |
| Cancelamento | Estado por job: enviando → solicitado → resultado do backend | O cancelamento é cooperativo; `succeeded` depois do pedido é respeitado |
| Exportação | Resultado da sessão separado do histórico do backend; nova tentativa não apaga o anterior | O registro não garante que o arquivo exista |
| Warning | Aviso visual em qualquer status | Não transforma sucesso em erro |
| 409 ao salvar | Recarregar cortes mantendo o rascunho | O usuário confere e salva de novo com a revisão nova |
| `result.message` no sucesso vazio | Não exibido | No backend atual é genérico ("revise o contexto"); foi pedido um campo próprio |

## Acessibilidade

Rótulos em todos os campos, `aria-invalid` e `aria-describedby` nos erros, `role="status"`/`alert` nos estados, foco visível, setas ↑/↓ na lista de cortes, `aria-current` no corte selecionado, texto explicando por que cada botão está desabilitado, `prefers-reduced-motion`.
