# Regras de trabalho

Atualização de 2026-10-29: a tarefa de execução autônoma do MVP autorizou implementação local e restabeleceu GPT para backend/processamento/integração e Claude para frontend. Esta autorização sucede o arranjo de agente único da S0.4, preservado nos registros históricos.

Na implementação atual, GPT escreve `backend/`, seus testes, `scripts/`, `docs/coordination/integration-contract.md`, `docs/coordination/backend-status.md`, documentação de backend e inicialização compartilhada. Claude escreve `frontend/`, seus testes e `docs/coordination/frontend-status.md`. Cada agente lê o status do outro; não edita seus arquivos. Dependências ficam em ambientes separados por diretório. Não há comunicação direta com Claude confirmada: os arquivos são o canal de coordenação.

As seções abaixo registram o acordo da S0.4; a divisão acima prevalece para a implementação atual. `.claude/`, `CLAUDE.md` e relatórios históricos continuam preservados. Nenhum Git de escrita, publicação, serviço pago ou upload de mídia está autorizado.

## Responsáveis

| Área/arquivo | Responsável | Regra de edição |
| --- | --- | --- |
| `AGENTS.md`, `CLAUDE.md`, `.claude/`, `docs/` | Claude Code, dentro do escopo de cada tarefa | Só os arquivos declarados na tarefa |
| `README.md`, `.gitignore`, `.ignore` | Claude Code, quando a tarefa autorizar | Mudanças pequenas e registradas no relatório |
| `.agents/skills/` (Remotion) | Claude Code, só em tarefa de manutenção de skills | Seguir o procedimento de `docs/setup/skills-inventory.md` e o manifesto de hashes |
| `Claude outputs/settings.json` | Usuário decide | Preservado até a validação local e autorização explícita para remover |
| `graft/` | Ferramenta Graft (índice regenerável) | Não editar à mão; não colocar código de produto ali |
| Commits, branches, worktrees, remotes | Usuário | Só com instrução explícita para a operação |

## Antes e durante a tarefa

1. Leia `AGENTS.md`, este documento e o pedido.
2. Declare escopo e arquivos de escrita. Rode `git status --short --branch` quando houver shell e preserve arquivos não rastreados.
3. Antes de salvar um arquivo, confira se ele mudou desde a leitura. Mudança inesperada bloqueia a edição daquele arquivo até perguntar ao usuário.
4. Não use comandos Git de restauração, limpeza ou troca de branch para resolver diferenças.
5. Não faça staging amplo. Só o usuário prepara commits, ou uma tarefa que o autorize.

## Processos e dependências

- Não rode instalações simultâneas no mesmo ambiente ou lockfile, inclusive entre duas sessões do Claude abertas ao mesmo tempo.
- Servidores e testes de longa duração usam portas definidas no planejamento. Não encerre processos que a tarefa não iniciou.
- Ferramentas de outros agentes ainda instaladas no computador (por exemplo, o app Codex) não devem ter sessões ativas nesta pasta. Em 2026-10-29, depois da mudança para agente único, havia objetos Git novos e refs `refs/codex/turn-diffs/checkpoints` gravados pelo app Codex; não remover, decisão do usuário.

## Worktrees (reavaliação S0.4)

Com um agente, não há mais motivo para worktrees por divisão de trabalho. Continuam úteis em dois casos:

- duas sessões do Claude implementando ao mesmo tempo, com dependências ou testes próprios;
- um experimento descartável que não deve sujar o checkout principal.

Pré-requisitos, quando forem usadas: commit inicial autorizado, política de fins de linha (`.gitattributes`) decidida e diretório preferencialmente fora do OneDrive. Nenhum desses itens bloqueia tarefas só de documentação. Procedimento:

```powershell
git status --short --branch
git worktree list
git worktree add -b claude/nome-da-tarefa ../ai-stream-editor-tarefa main
```

Cada operação (criar, integrar, remover) precisa de autorização. Não use remoção forçada. A sintaxe segue a [documentação oficial](https://git-scm.com/docs/git-worktree).

## Entrega e bloqueios

Cada relatório inclui: status, escopo, arquivos criados/alterados, verificações e resultados, decisões reversíveis, pendências. Diferencie execução real de procedimento recomendado.

Um bloqueio indica a ação impedida, a causa observada, o impacto, o trabalho ainda possível e o que permite continuar. Não declare pendência resolvida por suposição.

## Histórico: modelo com dois agentes (S0.1–S0.4)

Registro do arranjo anterior, mantido como referência. Não está mais em vigor.

- Codex respondia por `AGENTS.md`, `docs/setup/codex-setup.md`, `README.md`, `.gitignore`, auditoria, inventário de skills, regras de colaboração e `.agents/skills/`. Indicativamente, também pelo backend e processamento futuros.
- Claude Code respondia por `.claude/`, `CLAUDE.md`, `docs/setup/claude-setup.md`, `claude-skills-inventory.md`, `claude-validation-report.md` e `Claude outputs/`. Indicativamente, também pelo frontend futuro.
- Um terceiro participante (ChatGPT) coordenava e aprovava tarefas.
- Regras específicas daquele modelo: um editor por arquivo compartilhado, propostas de mudança entregues como diff ao dono do arquivo, reserva de arquivos nos relatórios, worktrees recomendadas antes de implementação paralela entre os dois agentes.
- Registros completos: `docs/setup/codex-setup.md`, `docs/setup/codex-validation-report.md`, `docs/setup/environment-audit.md`, `docs/setup/skills-inventory.md` e os três `docs/setup/claude-*.md`.
