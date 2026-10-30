# Setup do Codex: S0.1

> Estado revalidado em S0.2: [relatório de validação](codex-validation-report.md). O relato S0.1 abaixo permanece histórico. A skill segue íntegra e descoberta; o campo `version` é uma incompatibilidade estrita não bloqueante no Codex testado. Licença de redistribuição continua inconclusiva. Pacote WSL 2.6.3.0 foi identificado, mas sua operação não foi validada. A S0.2 também registrou regeneração automática de skills globais pelo diagnóstico do CLI; não presume preservação integral desse cache.

Data: 29/10/2026. Responsável: Codex. Escopo: auditoria, fundação documental, regras de colaboração e instalação local da skill Remotion. Nenhuma funcionalidade foi implementada e nenhuma stack foi escolhida.

## Resultado

Fundação criada na pasta existente `ai lives`, preservando o cache inicial do Graft. Git inicializado em `main`, sem commits, staging, remote ou worktrees adicionais. Foram criados nove arquivos próprios e instalado um pacote de skill com 144 arquivos oficiais. Não foram instaladas dependências globais, ferramentas de produto, servidores MCP ou aplicações.

Durante a execução surgiram `CLAUDE.md` e `Claude outputs/`, ausentes na inspeção inicial. São alterações externas ao trabalho do Codex; não foram criadas, editadas ou removidas por esta tarefa. O estado final pode incluir trabalho simultâneo de outro agente. Essa ocorrência não autoriza alterá-los.

## Ambiente e ferramentas

Windows nativo NT `10.0.26200.0`, PowerShell `7.6.5`, Git `2.55.0.windows.4`, Python `3.12.10`, Node `v24.19.0`, npm `11.17.0`, FFmpeg/FFprobe `9.0.1-full_build-www.gyan.dev` e Codex CLI `0.153.4` foram identificados. `npx` e `rg` estão no PATH. PyYAML já estava disponível.

Claude Code não foi encontrado no PATH desta sessão, mas isso não descarta outro método de execução; os arquivos externos observados reforçam que não se deve inferir ausência do agente a partir desse teste. WSL está no PATH, mas seu comando de status falhou por acesso ao arquivo. Não foram testados GPU, pipelines, compatibilidade de dependências futuras ou a execução do produto.

Consulte a [auditoria](environment-audit.md) para evidências e diferenças Windows/Linux/WSL, incluindo caminhos com espaços, fins de linha e OneDrive.

## Arquivos e configurações criados

| Arquivo/diretório | Propósito |
| --- | --- |
| `AGENTS.md` | Regras duráveis de escopo, segurança e colaboração; proprietário Codex |
| `README.md` | Estado do projeto e navegação |
| `.gitignore` | Segredos, ambientes, dependências, mídia, transcrições e saídas privadas |
| `docs/setup/environment-audit.md` | Ambiente observado antes das modificações e limitações |
| `docs/setup/codex-setup.md` | Este registro, verificações e pendências |
| `docs/setup/skills-inventory.md` | Preexistentes, instalada, candidatas, riscos e manutenção |
| `docs/setup/remotion-files.sha256` | Manifesto completo dos arquivos instalados, com hashes SHA-256 |
| `docs/coordination/collaboration-rules.md` | Responsáveis, concorrência, entrega e worktrees futuras |
| `docs/decisions/README.md` | Local reservado a decisões futuras, sem decidir arquitetura |
| `.agents/skills/remotion-best-practices/` | Uma skill local de terceiros; 144 arquivos, sem execução de seus exemplos |
| `.git/` | Metadados do repositório recém-inicializado |

O `.gitignore` mantém configurações compartilháveis, `.agents/`, lockfiles e exemplos de ambiente visíveis. A extensão `.ts` não é ignorada como mídia, pois também é TypeScript. Arquivos privados em JSON/TXT devem ficar nos diretórios privados documentados ou ter nomes de transcrição cobertos pelas regras; não há como inferir sensibilidade apenas pela extensão de todo JSON/TXT.

Não foi criado `.codex/config.toml`: instruções em `AGENTS.md` e skills no caminho de descoberta local são suficientes. Configurações pessoais do Codex, políticas de execução, `.claude/` e `CLAUDE.md` não foram alterados pelo Codex.

## Instalação executada

A [documentação Remotion](https://www.remotion.dev/docs/ai/skills) confirmou o repositório e o método `npx skills add remotion-dev/skills`. Em vez de executar um pacote npm adicional, foi usado o instalador OpenAI já disponível, após ler seu código e o helper de rede. Seu parâmetro `--dest` permite instalação no projeto, sem duplicar skills de sistema nem escrever no diretório pessoal de skills.

Revisão Remotion fixada: `30d4553ecd46fbc5212fd0ff006ae43af522158b`, versão declarada `4.0.539`.

Comando executado, após inspecionar a cópia temporária da mesma revisão:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python 'C:\Users\jvmon\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py' --repo remotion-dev/skills --path skills/remotion-best-practices --ref 30d4553ecd46fbc5212fd0ff006ae43af522158b --dest 'C:\Users\jvmon\OneDrive\Documents\ChatGPT\ai lives\.agents\skills' --method download
```

Os caminhos acima são o registro desta máquina, não uma exigência para outros ambientes. O comando não é de atualização: o helper aborta quando o destino existe. Para manutenção, siga o [inventário](skills-inventory.md).

O download/revisão foi feito em temporário permitido, na pasta `ai-stream-editor-s01-3aa17d7558e84af69ec27ba10e67434b` sob `%TEMP%`. Também ficaram ali hashes de comparação do estado inicial. Nenhum script Remotion, `npm install`, `npx`, renderizador ou modelo de transcrição foi executado. Não se executou o `package.json` upstream, que nem foi copiado para o projeto.

A skill já apareceu no catálogo atualizado desta sessão. Em outra sessão, abra o projeto na raiz e confirme o seletor de skills; descoberta de arquivos não equivale a validar todos os exemplos de execução no Windows.

## Procedimento de verificação

Executar na raiz do projeto, em PowerShell. As verificações abaixo são somente leitura. O teste de manifesto verifica bytes; alterações de fins de linha também serão detectadas.

```powershell
git status --short --branch
git remote -v
git worktree list --porcelain
git diff --check
```

Em S0.1: `main` sem commits, nenhum remote, apenas a worktree principal. Os arquivos novos são não rastreados; por isso `git diff --check` sozinho não inspeciona seu conteúdo.

Para conferir a skill e as regras de exclusão, sem criar arquivos de teste:

```powershell
@'
from pathlib import Path
import hashlib
import subprocess

root = Path.cwd()
expected = {}
for line in (root / 'docs/setup/remotion-files.sha256').read_text(encoding='utf-8').splitlines():
    digest, rel = line.split('  ', 1)
    path = (root / rel).resolve()
    assert path.is_relative_to(root.resolve())
    expected[rel] = digest
skill_dir = root / '.agents/skills/remotion-best-practices'
actual = {p.relative_to(root).as_posix() for p in skill_dir.rglob('*') if p.is_file()}
assert actual == set(expected), 'Manifesto e arquivos divergem'
assert all(hashlib.sha256((root / rel).read_bytes()).hexdigest() == digest
           for rel, digest in expected.items()), 'Hash divergente'
assert len(list((root / '.agents/skills').rglob('SKILL.md'))) == 1

ignored = ['.env', '.env.production', 'secrets/key.json', 'credentials.json',
           '.venv/test', 'node_modules/test', 'video.mp4', 'VIDEO.MP4',
           'audio.WAV', 'private.srt', 'private.VTT', 'session.transcript.json',
           'transcripts/private.json', 'data/private/transcript.txt',
           'outputs/result.json', 'graft/.cache/session/test.json']
visible = ['.env.example', '.env.production.example', '.env.template',
           'AGENTS.md', 'README.md', '.gitignore', 'pyproject.toml', 'package.json',
           'uv.lock', 'package-lock.json', 'config/settings.toml',
           '.codex/config.toml', '.claude/settings.json', 'src/example.ts',
           *sorted(actual)]
result = subprocess.run(['git', 'check-ignore', '--no-index', '--stdin', '-z'],
    input=('\0'.join(ignored + visible) + '\0').encode(), capture_output=True)
assert result.returncode in (0, 1), result.stderr
found = set(filter(None, result.stdout.decode().split('\0')))
assert found == set(ignored), found.symmetric_difference(ignored)
print(f'OK: {len(actual)} arquivos e hashes; regras de exclusao verificadas')
'@ | python -
```

Esse teste de skill única vale para o estado S0.1; atualize a expectativa se outra instalação local for autorizada no futuro. O protocolo NUL (`-z`) evita interpretar CRLF como parte de um nome no Git para Windows.

O validador estrito local também foi executado, com UTF-8 e sem bytecode:

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
python 'C:\Users\jvmon\.codex\skills\.system\skill-creator\scripts\quick_validate.py' '.\.agents\skills\remotion-best-practices'
```

**Resultado real: saída 1**, por `Unexpected key(s) in SKILL.md frontmatter: version`. A presença dos campos obrigatórios e a sintaxe YAML foram verificadas separadamente com PyYAML já instalado. Não se declara conformidade estrita com esse validador. A descoberta pelo Codex foi observada, e os arquivos oficiais foram mantidos sem modificações. Isso é uma ressalva upstream documentada, não um erro escondido como teste aprovado.

## Evidências da validação

| Verificação | Resultado |
| --- | --- |
| Origem Remotion e documentação atual | Confirmadas; revisão fixa, download oficial |
| Comparação com arquivo baixado para inspeção | 144/144 arquivos com SHA-256 igual; 1.183.282 bytes |
| Manifestos locais | Um `SKILL.md`; nenhuma skill adicional de topo instalada |
| Scripts MJS | Quatro arquivos, dois conteúdos distintos; inspecionados, não executados |
| Campos obrigatórios/YAML | Nome corresponde à pasta, nome/descrição válidos e YAML legível |
| Validador estrito OpenAI local | Ressalva: rejeita campo extra `version`, código 1 |
| Descoberta no Codex | `remotion-best-practices` apareceu no catálogo atualizado da sessão |
| Regras do `.gitignore` | 16 caminhos privados/gerados ignorados; 158 caminhos de configuração/código/skill permanecem visíveis |
| Preservação do estado inicial selecionado | 62/62 hashes iguais: configurações selecionadas, skills pessoais/de sistema e cache Graft inicial |
| Produto | Nenhum manifesto de dependências, aplicação ou ambiente de produto criado pelo Codex |
| Claude | Arquivos externos observados e preservados; nenhum arquivo reservado ao Claude alterado pelo Codex |
| Links/documentos próprios | Nove arquivos em UTF-8, sem espaços no fim das linhas; cercas Markdown equilibradas e dez links locais existentes |
| Procedimento publicado acima | O trecho Python foi extraído deste documento e executado: passou para os 144 arquivos/hashes e regras de exclusão |
| Estado Git final | `main` sem commits; nenhum remote, staging ou worktree adicional; `git diff --check` sem mensagens, com a limitação dos arquivos não rastreados indicada acima |

Saída de `git status --short --branch` na revisão final:

```text
## No commits yet on main
?? .agents/
?? .gitignore
?? AGENTS.md
?? CLAUDE.md
?? "Claude outputs/"
?? README.md
?? docs/
```

`CLAUDE.md` e `Claude outputs/` são trabalho externo observado. O cache inicial do Graft permaneceu presente e ignorado. Não houve staging para produzir esse relatório, portanto os arquivos próprios também aparecem como não rastreados.

Não há suíte de testes de produto a executar. Não foram instalados linters ou testes de mídia para simular uma aplicação inexistente.

## Limitações, decisões e pendências

1. Usar a pasta atual evita renomear/mover trabalho. `main` foi selecionada apenas para o repositório novo; o padrão global de branch permaneceu inalterado.
2. A permissão de rede foi necessária para API/raw/codeload do GitHub. Não houve bloqueio de instalação após a revisão automática.
3. WSL não pôde ser validado; CLI Codex apresentou avisos de acesso a aliases/temporários. Resolver isso só se necessário em tarefa própria, sem alterar permissões ou configuração global por iniciativa desta etapa.
4. A skill Remotion é ampla e inclui exemplos com escrita de arquivos, instalação de pacotes e serviços externos. Só deve ser usada em tarefas Remotion explicitamente autorizadas; não adota tecnologia, não autoriza custos ou transferência de mídia.
5. Há ressalva do validador pelo campo `version` e ausência de licença identificada na raiz/API upstream. Antes de redistribuir o pacote publicamente ou incorporar exemplos ao produto, esclarecer condições de uso. Não houve publicação ou incorporação de exemplos ao produto aqui.
6. A instalação é de referências, não de runtime Remotion. Exemplos de mapas, WebGPU, transcrição ou renderização não foram testados; não se afirma compatibilidade funcional deles com Windows, WSL ou hardware local.
7. Antes do primeiro commit autorizado, decidir política de fins de linha e revisar todos os arquivos, inclusive os produzidos pelo outro agente. A política global `core.autocrlf=true` não foi modificada. Um checkout futuro pode alterar bytes sem uma política adequada.
8. Não foi instalado planejador genérico, nova coleção de skills, plugin ou MCP. O catálogo e as candidatas estão no inventário, com fontes e recomendações.
9. Propriedade de arquivos é um acordo operacional, sem mecanismo de lock. Mudanças simultâneas de arquivo compartilhado exigem coordenação real; worktrees futuras separam diretórios mas não dispensam a revisão de integração.

## Autoavaliação obrigatória

| Pergunta | Resposta e evidência |
| --- | --- |
| 1. Estrutura suficiente sem antecipar produto? | Sim: documentos, regras, Git e skill; nenhum app. |
| 2. AGENTS claro e coerente? | Sim: regras curtas, propriedade explícita e skills subordinadas ao escopo. |
| 3. Claude pode trabalhar sem sobrescrever nossos arquivos? | As responsabilidades permitem divisão segura se ambos seguirem o acordo; não existe garantia técnica de exclusão mútua no checkout. Arquivos externos observados foram preservados. |
| 4. Origem das skills instaladas verificável? | Sim: somente Remotion, organização oficial, SHA fixo e manifesto de hashes. |
| 5. Instruções perigosas ou amplas? | Há instruções amplas de criação, upgrade e serviços externos; identificadas e limitadas por AGENTS. Nada disso foi executado. Não é certificação irrestrita de segurança. |
| 6. Duplicações/complexidade desnecessária? | Nenhuma instalação duplicada de skill de sistema ou outro pacote. Há exemplos internos repetidos no bundle oficial; preservados para manter a distribuição íntegra. |
| 7. Instalação funciona no SO? | Cópia, hashes, YAML e descoberta funcionaram no Windows; execução dos exemplos não avaliada. Validador estrito tem a ressalva documentada. |
| 8. Dependência global desnecessária? | Não: nenhuma instalada. |
| 9. Documentação corresponde à execução? | Sim: falhas, permissões de rede, conteúdo upstream e concorrência registrados sem prometer testes de produto. |
| 10. Procedimentos de verificação testados? | Sim: manifesto, exclusões e inspeções Git. Atualização, remoção e criação de worktrees são procedimentos futuros, não executados. |
| 11. Arquivo fora do escopo alterado? | Nenhum editado deliberadamente pelo Codex; 62 arquivos preexistentes selecionados mantiveram hashes. Downloads/auditoria ficaram em temporário permitido. |
| 12. Preparados para pesquisa/planejamento separados? | Sim, com as ressalvas técnicas acima. A fase seguinte exige nova tarefa; não foi iniciada. |

## Próximas necessidades, sem execução

- Concluir o setup próprio do Claude Code e alinhar leitura explícita de AGENTS/regras e propriedade dos documentos.
- Em tarefa separada, pesquisar requisitos e alternativas, registrar decisões e contratos de integração antes de implementação.
- Esclarecer licença upstream e fins de linha antes de publicação/primeiro commit; revisar e autorizar esse commit separadamente.
- Definir versões suportadas e ambiente de execução na etapa apropriada; reavaliar WSL/OneDrive somente se necessário.
- Reavaliar skills adicionais quando houver necessidade concreta, sem instalação em lote.

## Resumo para o coordenador

S0.1 criou a fundação documental local do AI Stream Editor na pasta existente `ai lives`. Git em `main`, sem commit, staging, remote ou worktree adicional. AGENTS e regras de colaboração separam proprietários e proíbem antecipar implementação. Remotion `remotion-best-practices` 4.0.539 foi instalada em `.agents/skills/`, revisão `30d4553ecd46fbc5212fd0ff006ae43af522158b`: 144 arquivos verificados por SHA-256 e descoberta confirmada no Codex. Nenhuma dependência global, stack ou funcionalidade foi introduzida. Ressalvas: validador estrito rejeita metadado `version`; licença upstream não identificada; WSL não validado; exemplos Remotion não executados. `CLAUDE.md` e `Claude outputs/` surgiram externamente durante o trabalho e foram preservados. Próxima etapa: setup próprio do Claude e nova tarefa de pesquisa/planejamento, com coordenação de arquivos compartilhados.
