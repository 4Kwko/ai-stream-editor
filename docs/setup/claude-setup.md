# Setup do Claude Code (S0.2)

Data: 2026-10-29. Responsável: Claude Code. Status: parcialmente concluído. `CLAUDE.md` e os documentos foram gravados. `.claude/settings.json` não pôde ser gravado (ver 3.2) e a validação no Claude Code local está pendente (seção 6).

> **Fechamento S0.4 (2026-10-29):** o projeto passou a ter um único agente (Claude Code). Verificados: presença, identidade e validade JSON de `.claude/settings.json`. Não verificados: carregamento das instruções, permissões, versão e plugins locais. Roteiro local e ressalvas em [claude-validation-report.md](claude-validation-report.md), seção 10. As menções a Codex abaixo são registro do modelo anterior.

> **Atualização S0.4 (2026-10-29):** `.claude/settings.json` agora existe e é idêntico à proposta (o arquivo foi movido para lá; a cópia de origem em `Claude outputs/` foi restaurada para preservação). Carga de instruções, permissões, versão e plugins locais continuam sem verificação: não há shell local e a janela do app Claude não é visível ao controle do computador. Detalhes e roteiro de 3 minutos em [claude-validation-report.md](claude-validation-report.md#9-s04--fechamento-de-pendências-2026-10-29-0431-0450-brt).

> **Atualização S0.3 (2026-10-29):** `.claude/settings.json` continua ausente. O arquivo foi salvo em `Claude outputs/settings.json` (conteúdo idêntico ao proposto), onde não tem efeito e entra no `git status` como não rastreado. Mova para `.claude/settings.json` e apague `Claude outputs/`. O Codex registrou que `claude` não está no PATH; a validação pode ser feita pela aba Code do app desktop numa sessão local. Resultados completos em [claude-validation-report.md](claude-validation-report.md).

## 1. Como esta tarefa foi executada

A tarefa rodou numa sessão do Claude em nuvem ligada ao computador do usuário pelo app desktop. Essa ligação permitiu listar, ler e gravar arquivos na pasta do projeto, mas não ofereceu terminal no Windows. Por isso:

- não foi possível rodar `claude --version`, `/doctor`, `/context`, `/plugin` ou `claude plugin list` no computador do usuário;
- nenhum comando Git foi executado (nem leitura de `git status`);
- nenhuma configuração global (`~/.claude/`) foi lida ou alterada.

O que não pôde ser verificado está marcado como pendente, sem suposição de resultado.

## 2. Ambiente identificado

| Item | Valor | Como foi verificado |
| --- | --- | --- |
| Sistema operacional | Windows x64 (dispositivo `jo-o`) | informação do dispositivo pelo app desktop |
| App Claude desktop | 4.29.0 (Electron 44.9.3, Node 24.22.0 embutido no app) | informação do dispositivo |
| Claude Code CLI | **não verificado** | sem terminal local nesta sessão |
| Interface usada nesta tarefa | sessão em nuvem ligada ao desktop, não o CLI local | contexto da sessão |
| Raiz do projeto | `C:\Users\jvmon\OneDrive\Documents\ChatGPT\ai lives` (pasta sincronizada pelo OneDrive) | listagem |
| Pasta `~/.claude` | não aparece na listagem da pasta pessoal. Pode indicar que o CLI nunca rodou neste usuário ou que a pasta é ocultada por proteção. Inconclusivo | listagem de nomes da pasta pessoal |
| Outras ferramentas de agente na pasta pessoal | `.codex`, `.agents`, `.copilot`, `.graft`, `.impeccable`, `.headroom` (só nomes, conteúdo não inspecionado) | listagem de nomes |
| MCP servers locais | nenhum reportado pelo app desktop | informação do dispositivo |
| Repositório Git | `.git/` presente, `HEAD` aponta para `refs/heads/main`, `refs/heads/` vazio (sem commits), sem remote em `.git/config` | leitura de arquivos |

Estado do projeto na auditoria: `AGENTS.md`, `README.md`, `.gitignore`, `docs/coordination/collaboration-rules.md`, `docs/decisions/README.md`, `docs/setup/remotion-files.sha256`, `.agents/skills/remotion-best-practices/` e `graft/.cache/`. Não existiam `CLAUDE.md` nem `.claude/`.

## 3. Configurações aplicadas

### 3.1 `CLAUDE.md`

- Importa `@AGENTS.md` e `@docs/coordination/collaboration-rules.md`. A documentação oficial (memory) diz que o Claude Code lê `CLAUDE.md`, não `AGENTS.md`, e recomenda um `CLAUDE.md` que importe `@AGENTS.md`. No Windows, a documentação desaconselha symlink (exige admin ou Developer Mode) e indica o import.
- Os imports são relativos ao próprio arquivo e ficam dentro do projeto, então não disparam o diálogo de aprovação de imports externos.
- Inclui apenas regras específicas do Claude Code: escopo, planejamento antes de mudanças complexas, separação pesquisa/planejamento/implementação, consulta à documentação atual, dependências mínimas, verificação antes de concluir, Git sem automação, relatório. Tem 32 linhas; o conteúdo de `AGENTS.md` não foi copiado.
- Uma nota para mantenedores usa comentário HTML, que a documentação diz ser removido antes de entrar no contexto.

### 3.2 `.claude/settings.json` (escopo de projeto, versionável): **presente desde S0.4, ativação não verificada**

A ferramenta de escrita remota recusou a gravação: "Writing to .claude is not permitted via remote tools." O conteúdo abaixo foi entregue ao usuário para criar o arquivo manualmente em `.claude/settings.json`. Enquanto isso não for feito, nenhuma regra de permissão nem plugin de projeto está ativo. Nenhum arquivo substituto foi criado fora de `.claude/`.

Conteúdo proposto:

```json
{
  "permissions": {
    "ask": [
      "Edit(/AGENTS.md)",
      "Edit(/.agents/**)",
      "Edit(/README.md)",
      "Edit(/.gitignore)",
      "Edit(/docs/coordination/**)",
      "Edit(/docs/decisions/**)",
      "Edit(/docs/setup/codex-setup.md)",
      "Edit(/docs/setup/environment-audit.md)",
      "Edit(/docs/setup/skills-inventory.md)",
      "Edit(/docs/setup/remotion-files.sha256)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git push *)",
      "Bash(git merge *)",
      "Bash(git rebase *)",
      "Bash(git checkout *)",
      "Bash(git switch *)",
      "Bash(git stash *)",
      "Bash(git worktree *)",
      "Bash(git branch *)",
      "PowerShell(git add *)",
      "PowerShell(git commit *)",
      "PowerShell(git push *)",
      "PowerShell(git merge *)",
      "PowerShell(git rebase *)",
      "PowerShell(git checkout *)",
      "PowerShell(git switch *)",
      "PowerShell(git stash *)",
      "PowerShell(git worktree *)",
      "PowerShell(git branch *)"
    ],
    "deny": [
      "Bash(git reset *)",
      "Bash(git clean *)",
      "Bash(git restore *)",
      "PowerShell(git reset *)",
      "PowerShell(git clean *)",
      "PowerShell(git restore *)",
      "Read(/.env)",
      "Read(/.env.local)",
      "Read(/secrets/**)"
    ]
  },
  "enabledPlugins": {
    "frontend-design@claude-plugins-official": true,
    "skill-creator@claude-plugins-official": true
  }
}
```

O que ele faz:

Nenhuma regra `allow` foi criada. Não há hooks, agentes, MCP servers, `defaultMode` nem modo de bypass.

- `ask` para edição de arquivos do Codex e compartilhados (`AGENTS.md`, `.agents/**`, `README.md`, `.gitignore`, `docs/coordination/**`, `docs/decisions/**`, documentos de setup do Codex) e para `git add/commit/push/merge/rebase/checkout/switch/stash/worktree/branch`. Isso não proíbe uma tarefa autorizada; obriga confirmação humana.
- `deny` para `git reset`, `git clean` e `git restore` (descarte de trabalho) e para leitura de `.env`, `.env.local` e `secrets/**`.
- As regras Git estão duplicadas para `Bash(...)` e `PowerShell(...)`, porque no Windows o Claude Code pode usar qualquer das duas ferramentas.
- `enabledPlugins` declara `frontend-design@claude-plugins-official` e `skill-creator@claude-plugins-official` (ver inventário).

Regras de caminho com `/` inicial ficam ancoradas no diretório de trabalho principal da sessão. **Inicie o Claude Code na raiz do projeto**; aberto numa subpasta, as regras apontam para outro lugar.

Limite conhecido (documentação de permissões): regras de Bash casam o texto do comando e não são barreira de segurança (`git -C . push` não casa `Bash(git push *)`). Regras `Read`/`Edit` não alcançam scripts que abrem arquivos sozinhos. Para bloqueio no nível do sistema seria preciso sandbox, que não foi configurado.

### 3.3 Plugins

Os dois plugins vêm do marketplace oficial `claude-plugins-official` (anthropics/claude-plugins-official, commit `f8c5e7a` de 2026-10-27) com origem de caminho relativo (`./plugins/...`). Pela documentação de carregamento de plugins, um plugin de caminho relativo não precisa de registro de instalação: carrega do próprio marketplace quando habilitado em `.claude/settings.json`. O marketplace oficial é adicionado automaticamente na primeira sessão interativa do terminal.

Isso é uma declaração de projeto que depende da criação manual de `.claude/settings.json`. **Que os plugins estão ativos ainda não foi verificado** (seção 6).

### 3.4 Estrutura preparada

```
CLAUDE.md
.claude/
  settings.json        (pendente: criação manual pelo usuário)
docs/setup/
  claude-setup.md
  claude-skills-inventory.md
```

`.claude/skills/`, `.claude/rules/`, `.claude/agents/` e `CLAUDE.local.md` não foram criados. Nenhuma skill própria foi criada. `.claude/settings.local.json` já está no `.gitignore` (feito pelo Codex); é ali que ficam aprovações pessoais do tipo "não perguntar de novo".

## 4. Integração com `AGENTS.md`

- Método: import `@AGENTS.md` no topo do `CLAUDE.md`, mais `@docs/coordination/collaboration-rules.md`, que o próprio `AGENTS.md` manda ler antes de editar.
- `AGENTS.md` existe e foi lido. Não há instrução conflitante: os dois exigem separar etapas, não automatizar Git, preferir configurações locais e respeitar a matriz de responsáveis.
- Carregamento efetivo: **pendente**. Confirmar com `/context` (seção Memory files) numa sessão local.
- Observação para o Codex: `collaboration-rules.md` ainda diz que "não foi configurado um `CLAUDE.md`". Agora existe. Atualizar fica a cargo do Codex.

## 5. Verificações realizadas

| Verificação | Resultado |
| --- | --- |
| `.claude/settings.json` é JSON válido | ok (`python -m json.tool`) |
| Destinos dos imports existem (`AGENTS.md`, `docs/coordination/collaboration-rules.md`) | ok |
| `CLAUDE.md` abaixo de 200 linhas (recomendação oficial) | ok, 32 linhas |
| Manifesto de `frontend-design` 1.1.1: só `SKILL.md` e licença, sem hooks, MCP, agentes ou scripts | ok, inspecionado |
| Manifesto de `skill-creator`: `SKILL.md`, agentes de avaliação e scripts Python (`run_eval.py` e `improve_description.py` chamam `claude -p` via subprocess só quando se roda avaliação); sem hooks nem MCP | ok, inspecionado |
| Pastas da tarefa não existiam antes da escrita | ok, listagem imediatamente antes da gravação |
| Gravação de `CLAUDE.md`, `claude-setup.md`, `claude-skills-inventory.md` | ok |
| Gravação de `.claude/settings.json` | **recusada** pela ferramenta remota (pasta protegida) |
| Arquivos fora do escopo alterados | nenhum |
| Versão do Claude Code, `/doctor`, plugins ativos, skills visíveis | **pendente**, sem terminal local |

## 6. Validação pendente (rodar no Windows, na raiz do projeto)

0. Crie `.claude/settings.json` com o conteúdo entregue (seção 3.2).
1. `claude --version`. Anote a versão aqui. O import `@` e os recursos usados exigem uma versão recente.
2. `claude` na raiz do projeto e aceite o diálogo de confiança da pasta. Plugins de projeto e regras de `.claude/settings.json` só carregam depois dele.
3. `/doctor`. Confira se não há aviso de regra inválida em `settings.json`.
4. `/context`. `CLAUDE.md` e `AGENTS.md` devem aparecer em Memory files.
5. `/permissions`. As regras `ask`/`deny` devem aparecer vindas de Project settings.
6. `/plugin`, aba Installed. `frontend-design` e `skill-creator` devem aparecer habilitados em escopo de projeto. Se aparecer "enabled in project settings but isn't installed here", rode `claude plugin install frontend-design@claude-plugins-official --scope project` (o mesmo para `skill-creator`).
7. Digite `/` e confira `/frontend-design:frontend-design` e `/skill-creator:skill-creator`. Teste sem efeito colateral: pergunte "quais skills você tem disponíveis?" e confirme as duas.
8. Se a conta claude.ai sincronizar cópias `@synced` dos mesmos plugins, mantenha só uma (desative a sincronizada com `claude plugin disable <nome>@synced`) para evitar duplicação.
9. Registre os resultados reais neste arquivo e no inventário.

## 7. Limitações conhecidas

- Projeto dentro do OneDrive. Sincronização pode gerar conflitos de arquivo com dois agentes escrevendo, e worktrees ou `node_modules` em pasta sincronizada são lentos. A regra de colaboração já recomenda worktrees fora de pastas sincronizadas.
- A skill `remotion-best-practices` está em `.agents/skills/`, caminho que a documentação do Claude Code não lista como local de descoberta (o Claude Code lê `.claude/skills/`). Para o Claude Code ela fica invisível. Não foi copiada para evitar duplicação e porque `.agents/` é do Codex.
- Comandos nativos de revisão (`/review`, `/security-review` e afins) não foram confirmados nesta sessão. Verificar com `/` no CLI local.

## 8. Pendências para as próximas fases

- Criar `.claude/settings.json` manualmente, executar a validação da seção 6 e atualizar estes documentos.
- Codex: incluir `docs/setup/claude-skills-inventory.md` e `docs/setup/claude-validation-report.md` na matriz de responsáveis e atualizar a frase sobre `CLAUDE.md` em `collaboration-rules.md`.
- ~~Codex: os documentos citados no `README.md` não existiam.~~ Resolvido: criados pelo Codex depois da S0.2 (verificado na S0.3).
- Coordenador: decidir se a skill Remotion fica disponível ao Claude Code (instalação mantida pelo Codex ou caminho compartilhado), só quando uma tarefa Remotion for autorizada.
- Quando houver código: reavaliar `typescript-lsp`, `security-guidance`, `code-review`/`pr-review-toolkit`, Playwright (MCP) e `webapp-testing`, todos adiados no inventário.
- Commit inicial: só o usuário ou uma tarefa autorizada. Worktrees dependem dele.
