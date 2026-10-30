# Auditoria do ambiente: S0.1

> Atualização S0.2: o registro inicial abaixo é histórico. A revalidação independente está no fim deste arquivo e em [codex-validation-report.md](codex-validation-report.md); prevalece para o estado atual.

Data: 29/10/2026, referência de data do usuário em America/Sao_Paulo. Auditoria feita antes da criação dos arquivos do projeto. Resultados específicos desta sessão; disponibilidade no PATH não equivale a validação de uma futura stack.

## Estado inicial

- Diretório: `C:\Users\jvmon\OneDrive\Documents\ChatGPT\ai lives`.
- Conteúdo inicial: apenas `graft/.cache/`, com `telemetry-repo-id.json` e `session/01a18667-2cfd-7841-a352-a580a9aae3ee.json`, além dos diretórios intermediários. São dados preexistentes da ferramenta, não código do produto. Foram preservados.
- Não havia `AGENTS.md`, `README.md`, `.gitignore`, `.agents/`, `docs/`, `.claude/` ou `CLAUDE.md` na raiz.
- `git rev-parse --show-toplevel` e `git status --short --branch` retornaram inicialmente que esta pasta não era um repositório Git. Não foi encontrado repositório pai.
- A busca nos diretórios ancestrais e no diretório de configuração do Codex não encontrou um `AGENTS.md` adicional aplicável.
- O pedido anexado foi lido fora do projeto, sem copiar seu arquivo para o repositório.

## Sistema, shell e permissões

| Item | Resultado verificado |
| --- | --- |
| Sistema | Windows nativo, Win32NT, versão NT `10.0.26200.0` |
| PowerShell | Core `7.6.5` |
| Política de scripts | `RemoteSigned` em LocalMachine; demais escopos consultados: Undefined. Nenhuma política alterada. |
| Escrita autorizada | Workspace do projeto, pasta de visualizações indicada pela sessão e temporários permitidos. Configurações globais fora do escopo de escrita da tarefa. |
| Rede | Consulta direta da API GitHub falhou com host desconhecido na execução restrita. Consultas públicas e download funcionaram com a permissão de rede revisada automaticamente. |
| WSL | `wsl.exe` existe; `wsl --status` falhou com mensagem de impossibilidade de acesso ao arquivo pelo sistema. Distribuições e funcionamento de WSL não foram confirmados. |
| Pasta sincronizada | O caminho está sob OneDrive. Isso não comprova que a sincronização esteja ativa nem que todos os arquivos estejam disponíveis offline. |

## Ferramentas

| Ferramenta | Versão/estado | Evidência |
| --- | --- | --- |
| Git | `2.55.0.windows.4` | `git --version` |
| Python | `3.12.10` | `python --version` |
| Node.js | `v24.19.0` | `node --version` |
| npm | `11.17.0` | `npm --version` |
| npx | Disponível, fornecido pelo npm | `Get-Command npx`; nenhum pacote executado por npx |
| FFmpeg | `9.0.1-full_build-www.gyan.dev` | `ffmpeg -version`, build Windows Gyan/WinGet |
| FFprobe | `9.0.1-full_build-www.gyan.dev` | `ffprobe -version` |
| Codex CLI | `codex-cli 0.153.4` | Invocação explícita de `codex.cmd --version`, código de saída 0; `package.json` local concorda |
| Codex desktop | Campo de versão da integração: `26.1023.51421` | Valor já existente na configuração; não é uma verificação independente do binário do app |
| ripgrep | Executável disponível no pacote do Codex | `Get-Command rg`; versão não consultada |
| Claude Code | Não encontrado no PATH desta sessão | `Get-Command claude`; não prova ausência de instalação por outro método |
| PyYAML | Módulo já disponível no Python | `importlib.util.find_spec('yaml')`; nada instalado |

Locais encontrados: Git em `C:\Program Files\Git\cmd\git.exe`; Python em `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`; Node/npm/npx em `C:\Program Files\nodejs\`; Codex em `%APPDATA%\npm\codex.cmd`/`codex.ps1`. FFmpeg e FFprobe estão no pacote WinGet `Gyan.FFmpeg` sob `%LOCALAPPDATA%\Microsoft\WinGet\Packages\`.

O wrapper `codex.ps1` não exibiu versão na primeira chamada composta. Após inspecionar esse wrapper, a chamada explícita de `codex.cmd` confirmou a versão. O CLI avisou que não conseguiu limpar temporários antigos nem criar aliases de PATH por acesso negado. Não tentamos corrigir permissões globais; o aviso não impediu a consulta da versão.

## Git e configurações existentes

- `core.autocrlf=true` foi encontrado na configuração efetiva. `core.longpaths` não retornou valor explícito. O padrão efetivo de branch inicial consultado era `master`; nada disso foi alterado globalmente.
- O repositório desta tarefa foi inicializado depois da auditoria com `git -c init.templateDir= init -b main`. O override de template vale apenas para esse comando e evita copiar templates externos para o novo repositório.
- Nenhum commit, staging, remote ou worktree adicional foi criado. `main` ainda não tem commit; arquivos novos permanecem não rastreados para revisão.
- `~/.codex/config.toml` e `~/.codex/hooks.json` já existiam. A configuração foi inspecionada por nomes de seções/chaves, sem publicar seus valores ou conteúdo integral. Há configurações de plugins, hooks e MCPs já existentes, incluindo Graft, Headroom e Node REPL. Nenhum deles foi instalado ou reconfigurado aqui.
- Nenhum arquivo de autenticação ou armazenamento de credenciais foi lido. Não foi necessário fornecer credenciais para baixar os repositórios públicos.
- Hashes iniciais de 62 arquivos foram registrados em temporário: configurações selecionadas do Codex, cache preexistente e arquivos nas skills pessoais/de sistema inspecionadas. A comparação final está registrada em [codex-setup.md](codex-setup.md). Isso não é uma auditoria de todos os arquivos do computador.

## Skills existentes

Foram encontrados quatro manifestos de sistema expostos à sessão (`imagegen`, `openai-docs`, `skill-creator`, `skill-installer`), sete skills pessoais e vinte skills de plugins. Um diretório de sistema adicional, `review-agent`, existe no disco, mas não estava exposto como skill selecionável nesta sessão. Não foi ativado nem duplicado.

O catálogo oficial foi consultado na revisão `49f948faa9258a0c61caceaf225e179651397431`. Não havia skill genérica `plan` ou `create-plan` na árvore dessa revisão. `define-goal` e `notion-spec-to-implementation` foram avaliadas como alternativas de escopo específico, sem instalação. O caminho `.experimental` retornou HTTP 404 nessa revisão. O inventário detalha origens e limites da verificação.

## Compatibilidade futura: Windows, Linux e WSL

- Use caminhos entre aspas por causa dos espaços. Não grave caminhos absolutos deste computador no código futuro. Use APIs de caminhos portáveis.
- Windows costuma tratar nomes sem distinguir maiúsculas/minúsculas; Linux pode distinguir. Evite arquivos cujos nomes diferem apenas na capitalização e nomes reservados pelo Windows.
- `core.autocrlf=true` pode produzir diferenças de fins de linha. Os hashes do manifesto instalado conferem os bytes atuais. Uma política `.gitattributes` deverá ser decidida antes do primeiro commit para preservar arquivos de terceiros e scripts; ela não foi imposta nesta etapa.
- `NUL` no Windows e `/dev/null` em shells Unix não são intercambiáveis. Alguns exemplos da skill Remotion usam sintaxe Unix e Bun; não foram executados nem certificados como portáveis.
- Não reutilize uma `.venv` ou `node_modules` entre Windows e WSL/Linux. Executáveis, permissões, links e dependências nativas podem diferir.
- Confirme acesso offline e comportamento de sincronização do OneDrive antes de cargas de mídia ou trabalho paralelo intenso. Uma migração de local dependerá de tarefa/autorização própria; não houve movimentação de dados.
- FFmpeg foi validado somente por versão. A presença de opções CUDA/NVENC no build não confirma GPU disponível, drivers ou aceleração funcional. Não houve processamento de mídia nem benchmark.
- Node, Python e FFmpeg instalados não determinam as versões que a futura aplicação deverá suportar. Compatibilidade de pacotes será avaliada na fase apropriada.

## Revalidação independente S0.2

Data: 29/10/2026. As versões de Git, Python, Node.js, npm, FFmpeg e Codex CLI foram novamente consultadas e permanecem iguais às registradas acima. Node executou uma operação local com `platform=win32`, `arch=x64`, saída 0; Python executou os verificadores. Não houve processamento de mídia. FFprobe não foi novamente executado nesta etapa; sua versão acima é evidência da S0.1.

O repositório continua em `main`, sem commits, staging, remotes ou worktrees adicionais. `git fsck --full` terminou com saída 0 e aviso esperado de ausência de referências. A ausência de commits impede usar o histórico Git como prova de preservação; foram comparados hashes do estado inicial da S0.2.

Novidades já presentes antes de qualquer edição S0.2: `.ignore`, regra `/graft/` no `.gitignore`, índices/arquivos regeneráveis em `graft/`, `CLAUDE.md`, `Claude outputs/settings.json` e três documentos `claude-*.md`. Os hooks globais preexistentes mencionam Graft, mas não foi atribuída autoria dessas alterações sem evidência. `.gitignore` e `.ignore` não foram editados pela S0.2.

### WSL: instalado, funcionamento não confirmado

- O executável do Windows existe em `C:\Windows\System32\wsl.exe`; sua versão de arquivo é `10.0.26100.8875`, que não é a versão do runtime WSL.
- `Get-AppxPackage -Name MicrosoftCorporationII.WindowsSubsystemForLinux`, em consulta com permissão revisada, identificou pacote **2.6.3.0**, estado `Ok`. Isso confirma a presença do pacote, não um Linux funcional.
- Na execução restrita, `--version`, `--status` e `--list --quiet` retornaram saída 1 com mensagem de impossibilidade de acesso ao arquivo.
- Fora dessa restrição, `System32\wsl.exe --version` excedeu o limite de 15 segundos. No executável do próprio pacote, as três consultas excederam o limite individual de 8 segundos. Os processos de consulta que expiraram foram encerrados pelo verificador; nenhuma distribuição Linux foi iniciada deliberadamente.
- A chave `HKCU\Software\Microsoft\Windows\CurrentVersion\Lxss` não foi encontrada no contexto consultado. Isso não prova ausência de distribuições de outros usuários ou ambientes.
- Não foram instalados componentes, habilitados recursos do Windows, alterados serviços ou configurações. A versão pode ser identificada por metadados; operação, kernel e distribuições permanecem não confirmados.

WSL é **opcional** para o setup e o planejamento atuais. A [documentação OpenAI para Windows](https://learn.chatgpt.com/docs/windows/windows-sandbox) confirma o fluxo nativo. WSL2 pode atender a ferramentas Linux futuras, mas adiciona outro ambiente, diferenças de caminhos e gerenciamento separado de dependências. A [documentação WSL do Codex](https://learn.chatgpt.com/docs/windows/wsl) informa que WSL1 não é suportado desde Codex 0.115. Não há requisito atual que justifique migrar o projeto. Os comandos de diagnóstico foram conferidos na [documentação Microsoft](https://learn.microsoft.com/en-us/windows/wsl/basic-commands).

### Efeito do diagnóstico nativo do Codex

`codex debug prompt-input` falhou primeiro com acesso negado. A repetição com permissão revisada terminou com saída 0 e provou a inclusão de AGENTS e dos metadados Remotion no prompt. Entretanto, essa inicialização regenerou o cache de skills de sistema em `~/.codex/skills/.system`: 12 arquivos novos e nove hashes preexistentes alterados no conjunto monitorado. Incluiu `plugin-creator` e atualizações de `openai-docs`/marcador; não foi uma instalação solicitada pela auditoria.

O [código oficial do CLI 0.153.4](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/skills/src/lib.rs) implementa essa regeneração por fingerprint. O efeito fora do projeto é um desvio registrado, sem reversão automática. `config.toml`, `hooks.json` e as skills pessoais mantiveram seus hashes. Não se declara preservação integral de todos os arquivos globais. Detalhes e limites estão no relatório S0.2.
