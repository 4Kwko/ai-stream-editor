# Inventário de skills e plugins do Claude Code

Atualizado em 2026-10-29 (S0.2). Fonte do marketplace: `anthropics/claude-plugins-official`, commit `f8c5e7a` (2026-10-27), inspecionado por clone. "Declarado" significa incluído em `enabledPlugins` do `.claude/settings.json` proposto. Esse arquivo ainda precisa ser criado manualmente (a escrita remota em `.claude/` foi recusada), e a ativação não foi confirmada no CLI local (ver `claude-setup.md`, seções 3.2 e 6).

## Recursos avaliados

| Recurso | Tipo | Mantenedor | Finalidade | Versão | Caminho/escopo | Estado | Justificativa | Referência |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frontend-design | plugin (1 skill) | Anthropic | Direção visual e qualidade de interface | 1.1.1 (manifesto) | projeto, `.claude/settings.json` | declarado, ativação pendente | Prioridade A. Só `SKILL.md` e licença; sem hooks, MCP ou scripts. Útil para o editor futuro | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/frontend-design) |
| skill-creator | plugin (skill + agentes de avaliação + scripts Python) | Anthropic | Criar e avaliar skills do projeto | sem versão no manifesto (calculada pelo commit) | projeto, `.claude/settings.json` | declarado, ativação pendente | Prioridade B. Sem hooks nem MCP; scripts só rodam ao avaliar uma skill e chamam `claude -p`. Nenhuma skill foi criada | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator) |
| remotion-best-practices | skill | Remotion (instalada pelo Codex) | Orientação para tarefas Remotion | 4.0.539 | `.agents/skills/` (Codex) | existente, invisível ao Claude Code | O Claude Code descobre skills em `.claude/skills/`, não em `.agents/skills/`. Não duplicada; decisão adiada até tarefa Remotion autorizada | `AGENTS.md`, [docs de skills](https://code.claude.com/docs/en/skills) |
| code-review | plugin (comando) | Anthropic | Revisão de PR com agentes | 1.0.1 | — | adiado | Depende de `gh` e de PRs; o repositório não tem commits nem remote | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-review) |
| pr-review-toolkit | plugin (agentes + comando) | Anthropic | Revisão de PR por especialidade (testes, tipos, erros) | não informada | — | adiado | Útil com código e PRs; nada a revisar agora | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/pr-review-toolkit) |
| security-guidance | plugin (hooks) | Anthropic | Avisos de segurança ao editar e revisão no Stop | 2.0.17 | — | adiado | Registra hooks em SessionStart, UserPromptSubmit, PostToolUse e Stop. A tarefa proíbe hooks automáticos. Reavaliar na implementação web | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/security-guidance) |
| claude-security | plugin (skill, agentes, hooks, scripts) | Anthropic | Varredura profunda de vulnerabilidades | não informada | — | adiado | Tem hooks; sem código para varrer | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-security) |
| typescript-lsp | plugin (LSP) | Anthropic | Inteligência de código TS/JS | 1.0.0 | — | adiado | Depende da escolha da stack e de um language server instalado | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/typescript-lsp) |
| playwright | plugin externo (MCP) | Microsoft | Automação de navegador e testes E2E/visuais | não informada | — | adiado | É MCP server, proibido nesta tarefa. Candidato forte para testes de interface depois | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/external_plugins/playwright) |
| webapp-testing | skill | Anthropic | Testar apps web locais com Playwright | não informada | — | adiado | Exige app rodando e Playwright; reavaliar com o frontend | [skill](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) |
| context7 | plugin externo (MCP remoto) | Upstash | Documentação versionada de bibliotecas | não informada | — | adiado | MCP de terceiro, exige autorização. WebSearch/WebFetch cobrem o uso atual | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/external_plugins/context7) |
| feature-dev | plugin (agentes) | Anthropic | Fluxo de feature com exploração, arquitetura e revisão | não informada | — | adiado | Sobrepõe o modo de planejamento nativo; reavaliar na implementação | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/feature-dev) |
| code-simplifier | plugin (agente) | Anthropic | Simplificar código recém-alterado | não informada | — | adiado | Sem código ainda | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-simplifier) |
| hookify | plugin | Anthropic | Criar hooks a partir de regras | não informada | — | rejeitado (agora) | Objetivo é criar hooks, proibido nesta fase | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/hookify) |
| claude-code-setup | plugin | Anthropic | Recomendar automações (hooks, MCP, subagentes) | não informada | — | rejeitado | Setup feito manualmente; recomenda justamente o que a tarefa adia | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-code-setup) |
| claude-md-management | plugin | Anthropic | Auditar e manter `CLAUDE.md` | não informada | — | rejeitado | `CLAUDE.md` tem 32 linhas; `/memory` e `/doctor` bastam | [plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-md-management) |
| frontend-design (repo `anthropics/skills`) | skill | Anthropic | Mesma finalidade do plugin | — | — | rejeitado | Duplicaria o plugin de mesmo nome | [skill](https://github.com/anthropics/skills/tree/main/skills/frontend-design) |
| skill-creator (repo `anthropics/skills`) | skill | Anthropic | Mesma finalidade do plugin | — | — | rejeitado | Duplicaria o plugin de mesmo nome | [skill](https://github.com/anthropics/skills/tree/main/skills/skill-creator) |

## Fechamento S0.4 (2026-10-29)

- Agente único: a skill `remotion-best-practices` em `.agents/skills/` passa a ser mantida pelo Claude Code, mas continua **não descoberta** por ele nesse caminho. Torná-la disponível (cópia ou link em `.claude/skills/`) fica para uma tarefa Remotion autorizada; a licença de redistribuição não esclarecida pesa contra versionar uma segunda cópia.
- Ressalvas mantidas: diverge da validação estrita pela chave `version`; funciona no Codex testado; licença de redistribuição não esclarecida.
- Plugins e skills locais: não verificados. Ver `claude-validation-report.md`, seção 10.

## Verificação S0.4 (2026-10-29)

- `.claude/settings.json` agora existe com `enabledPlugins` para os dois plugins. Se eles carregam numa sessão local continua **não verificado** (sem shell local; janela do app não visível ao controle do computador).

## Verificação S0.3 (2026-10-29)

- Os dois plugins de projeto continuam inativos: `.claude/settings.json` não existe (o arquivo foi salvo em `Claude outputs/`).
- As mesmas skills estão habilitadas na conta claude.ai e carregaram na sessão em nuvem: `frontend-design` com `SKILL.md` idêntico ao plugin 1.1.1; `skill-creator` (cópia sincronizada) com `SKILL.md` **diferente** do plugin do marketplace.
- Consequência esperada numa sessão local: duas fontes para cada skill. A documentação dá precedência ao plugin instalado sobre a cópia sincronizada; confirmar na aba Errors de `/plugin`. Se a divergência do `skill-creator` atrapalhar, desativar uma das cópias (decisão do usuário).
- Detalhes em [claude-validation-report.md](claude-validation-report.md).

## Funcionalidades nativas relevantes

| Recurso | Tipo | Finalidade | Estado | Referência |
| --- | --- | --- | --- | --- |
| Import `@arquivo` em `CLAUDE.md` | nativo | Compartilhar `AGENTS.md` | em uso | [memory](https://code.claude.com/docs/en/memory) |
| `/context`, `/memory`, `/doctor`, `/permissions`, `/plugin` | nativo | Diagnóstico de instruções, permissões e plugins | documentado; uso local pendente | [memory](https://code.claude.com/docs/en/memory), [plugins](https://code.claude.com/docs/en/plugins/install) |
| Modo de planejamento (`plan`) | nativo | Planejar sem editar | documentado; exigido no `CLAUDE.md` para mudanças complexas | [permissões](https://code.claude.com/docs/en/permissions) |
| Regras `allow/ask/deny` | nativo | Limitar edições e comandos | proposto (`ask`/`deny`, sem `allow`); depende da criação de `.claude/settings.json` | [permissões](https://code.claude.com/docs/en/permissions) |
| Comandos de revisão nativos | nativo | Revisão de código e segurança | não confirmados nesta sessão | verificar com `/` no CLI |

## Áreas sem recurso oficial identificado (adiadas)

React, Tailwind CSS, arquitetura de frontend, players de vídeo, interfaces de timeline, FFmpeg e documentação técnica: nenhum plugin específico no marketplace oficial (commit `f8c5e7a`). A skill Remotion existe do lado do Codex. Pesquisar quando a stack for decidida em tarefa própria.
