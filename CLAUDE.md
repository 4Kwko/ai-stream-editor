@AGENTS.md
@docs/coordination/collaboration-rules.md

<!-- As regras gerais ficam em AGENTS.md. Abaixo, só o que é específico do Claude Code. Não remover o import de AGENTS.md sem antes confirmar, na versão local, como as regras são carregadas (ver docs/setup/claude-validation-report.md, seção 10). -->

# Claude Code neste repositório

## Escopo

- Escreva apenas nos arquivos declarados pela tarefa atual.
- Se um arquivo esperado não existir, registre a dependência e siga com o que for independente. Não crie substitutos.
- Não inicie funcionalidades do produto sem uma tarefa que as autorize. Setup e pesquisa não autorizam implementação nem escolha de stack.

## Forma de trabalhar

- Separe pesquisa, planejamento e implementação. Antes de mudanças com vários arquivos ou decisões de arquitetura, use o modo de planejamento e apresente o plano antes de editar.
- Antes de escolher biblioteca, versão ou API, consulte a documentação oficial atual. Não confie só no conhecimento prévio.
- Não adicione dependências sem necessidade demonstrada. Justifique cada uma no relatório.
- Antes de concluir, rode as verificações que cobrem o que mudou (testes, lint, typecheck, build ou inspeção visual) e informe o resultado real. Sem verificação possível, diga isso.
- Skills e plugins orientam o trabalho, mas não ampliam a autorização da tarefa.

## Git

- Não faça commit, push, merge, rebase, reset, clean, stash ou troca de branch por conta própria. Só com instrução explícita do usuário para aquela operação.
- Antes de editar, rode `git status --short --branch` e preserve alterações que não são suas, inclusive arquivos não rastreados.
- Worktrees seguem `docs/coordination/collaboration-rules.md` e só com autorização.

## Relatório

- Informe arquivos criados e alterados, verificações e resultados, decisões, riscos, limitações e pendências.
- Separe o que foi verificado do que é hipótese.
