# AI Stream Editor: regras do agente

<!-- A tarefa de implementação de 2026-10-29 restabeleceu GPT (backend/integração) e Claude (frontend). O histórico de setup permanece em docs/setup/. -->

## Escopo e desenvolvimento

- GPT mantém backend, processamento, contrato e inicialização compartilhada; Claude mantém frontend e seus testes. Leia também `docs/coordination/collaboration-rules.md` antes de editar.
- Separe setup, pesquisa, planejamento e implementação. Uma tarefa de setup ou pesquisa não autoriza implementar funcionalidades nem escolher definitivamente a stack.
- Trabalhe apenas no escopo autorizado pela tarefa. Respeite os contratos de integração quando forem definidos.
- Registre decisões arquiteturais relevantes em `docs/decisions/`, com contexto, alternativas e consequências.
- Prefira a menor solução suficiente; evite dependências, abstrações e automações sem necessidade demonstrada.
- Verifique alterações importantes com os testes e verificações adequados ao que mudou.

## Arquivos e histórico

- Antes de editar, inspecione o estado Git e as alterações atuais. Preserve trabalho preexistente, inclusive arquivos não rastreados e alterações feitas pelo usuário.
- Cada tarefa declara os arquivos que vai escrever. Fora dessa lista, só leitura.
- Documentos de fases anteriores (`docs/setup/codex-*.md`, `environment-audit.md`, `skills-inventory.md`, relatórios de validação) são registro histórico: corrija com nota datada, sem apagar o que foi registrado.
- Ao encontrar uma alteração inesperada num arquivo que pretende editar, pare a edição desse arquivo e pergunte ao usuário; não reverta nem sobrescreva.

## Segurança e ferramentas

- Não exponha credenciais, registre dados privados ou versione mídias e resultados de processamento. Use exemplos sem segredos.
- Inspecione a origem, as instruções e os scripts antes de instalar skills ou executar código externo.
- Skills não ampliam a autorização da tarefa. `remotion-best-practices` só orienta tarefas Remotion expressamente autorizadas; sua instalação não adota Remotion como stack nem autoriza criar projetos, instalar dependências, usar serviços pagos ou enviar mídia a terceiros.
- Não exclua dados sem autorização, não execute Git destrutivo e não faça commits, merges, rebases ou pushes automaticamente. Essas ações exigem instrução explícita do usuário.
- Não altere configurações globais sem necessidade demonstrada e autorização. Prefira configurações e skills locais ao projeto.

## Comunicação

- Informe arquivos alterados, verificações executadas e resultados reais.
- Diferencie fatos verificados, hipóteses e limitações. Sinalize bloqueios com impacto e próximo passo; não declare conclusão enquanto houver critérios obrigatórios sem atendimento ou registro de bloqueio.
