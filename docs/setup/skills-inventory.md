# Inventário de skills: S0.1

> Revisão S0.2: as seções S0.1 são o registro histórico. A seção de revalidação ao fim deste arquivo registra operacionalidade, dependências e mudanças observadas, incluindo o efeito automático do CLI no cache de sistema. Nenhuma skill local foi atualizada ou reinstalada.

Inspeção em 29/10/2026. Apenas `remotion-best-practices` foi instalada nesta tarefa, no projeto. As demais já existiam ou foram apenas avaliadas. Auditoria das preexistentes: presença dos manifestos, metadados e escopo exposto; não é certificação integral de todos os scripts dos plugins.

## Caminhos

- **S** = `C:\Users\jvmon\.codex\skills\.system`
- **U** = `C:\Users\jvmon\.agents\skills`
- **P** = `C:\Users\jvmon\.codex\plugins\cache`
- **R** = `C:\Users\jvmon\OneDrive\Documents\ChatGPT\ai lives\.agents\skills`

Cada caminho abaixo é relativo à raiz indicada e contém `SKILL.md`. Prefixos como `sites:` e `ponytail:` no seletor identificam o plugin; o nome da pasta pode não ter esse prefixo.

## Preexistentes

| Nome | Origem/mantenedor observado | Finalidade | Caminho | Verificação/ação |
| --- | --- | --- | --- | --- |
| imagegen | Sistema OpenAI | Imagens | S/imagegen | Disponível; preservada |
| openai-docs | Sistema OpenAI | Documentação OpenAI/Codex | S/openai-docs | Lida para esta tarefa; preservada |
| skill-creator | Sistema OpenAI; referência oficial `openai/skills` | Criar/atualizar skills | S/skill-creator | Presença e instruções iniciais verificadas; não duplicada |
| skill-installer | Sistema OpenAI; referência oficial `openai/skills` | Instalar skills | S/skill-installer | Manifesto, instalador Python e helper GitHub inspecionados; usado com destino local |
| review-agent | Diretório de sistema local | Revisão, conforme nome; não avaliada para uso | S/review-agent | Somente presença em disco; não exposta no catálogo da sessão |
| antislop | Instalação pessoal; upstream não confirmado | Regras de interface/texto | U/antislop | Core lido; nenhum wizard/complemento instalado |
| antislop-code | Instalação pessoal; upstream não confirmado | Comentários de código | U/antislop-code | Metadados/presença; preservada |
| antislop-copywriting | Instalação pessoal; upstream não confirmado | Texto de produto | U/antislop-copywriting | Metadados/presença; preservada |
| antislop-human | Instalação pessoal; upstream não confirmado | Acessibilidade | U/antislop-human | Metadados/presença; preservada |
| antislop-layoutmobile | Instalação pessoal; upstream não confirmado | Layout responsivo | U/antislop-layoutmobile | Metadados/presença; preservada |
| antislop-ui | Instalação pessoal; upstream não confirmado | Interface visual | U/antislop-ui | Metadados/presença; preservada |
| find-skills | Instalação pessoal | Descoberta de skills | U/find-skills | Manifesto lido; pesquisa feita nas fontes, sem instalar CLI |
| computer-use | Plugin openai-bundled | Controle do Windows | P/openai-bundled/computer-use/26.1023.51421/skills/computer-use | Catálogo e arquivo presentes |
| visualize | Plugin openai-bundled | Visualizações na conversa | P/openai-bundled/visualize/1.0.57/skills/visualize | Catálogo e arquivo presentes |
| plugin-management | Plugin openai-curated-remote | Gerenciar plugins | P/openai-curated-remote/plugin-management/0.1.0/skills/plugin-management | Catálogo e arquivo presentes |
| sites | Plugin Sites | Criar/editar sites | P/openai-curated-remote/sites/1.1.2/skills/sites | Catálogo e arquivo presentes |
| sites-remix | Plugin Sites | Remixar sites | P/openai-curated-remote/sites/1.1.2/skills/sites-remix | Catálogo e arquivo presentes |
| create-pet | Plugin work-pets | Criar pets do ChatGPT | P/openai-curated-remote/work-pets/0.1.6/skills/create-pet | Catálogo e arquivo presentes |
| pets | Plugin work-pets | Gerenciar pets | P/openai-curated-remote/work-pets/0.1.6/skills/pets | Catálogo e arquivo presentes |
| update-pet | Plugin work-pets | Atualizar pets | P/openai-curated-remote/work-pets/0.1.6/skills/update-pet | Catálogo e arquivo presentes |
| documents | Plugin openai-primary-runtime | Documentos | P/openai-primary-runtime/documents/26.1025.11240/skills/documents | Catálogo e arquivo presentes |
| pdf | Plugin openai-primary-runtime | PDFs | P/openai-primary-runtime/pdf/26.1025.11240/skills/pdf | Catálogo e arquivo presentes |
| presentations | Plugin openai-primary-runtime | Apresentações | P/openai-primary-runtime/presentations/26.1025.11240/skills/presentations | Catálogo e arquivo presentes |
| spreadsheets | Plugin openai-primary-runtime | Planilhas | P/openai-primary-runtime/spreadsheets/26.1025.11240/skills/spreadsheets | Catálogo e arquivo presentes |
| excel-live-control | Plugin openai-primary-runtime | Sessão ativa do Excel | P/openai-primary-runtime/spreadsheets/26.1025.11240/skills/excel-live-control | Catálogo e arquivo presentes |
| template-creator | Plugin openai-primary-runtime | Templates reutilizáveis | P/openai-primary-runtime/template-creator/26.1025.11240/skills/template-creator | Catálogo e arquivo presentes |
| ponytail | Plugin Ponytail | Mudanças pequenas de código | P/ponytail/ponytail/5.3.3/skills/ponytail | Catálogo e arquivo presentes |
| ponytail-audit | Plugin Ponytail | Auditoria de repositório | P/ponytail/ponytail/5.3.3/skills/ponytail-audit | Catálogo e arquivo presentes |
| ponytail-debt | Plugin Ponytail | Inventário de atalhos | P/ponytail/ponytail/5.3.3/skills/ponytail-debt | Catálogo e arquivo presentes |
| ponytail-gain | Plugin Ponytail | Medições do plugin | P/ponytail/ponytail/5.3.3/skills/ponytail-gain | Catálogo e arquivo presentes |
| ponytail-help | Plugin Ponytail | Referência do plugin | P/ponytail/ponytail/5.3.3/skills/ponytail-help | Catálogo e arquivo presentes |
| ponytail-review | Plugin Ponytail | Revisão de mudanças | P/ponytail/ponytail/5.3.3/skills/ponytail-review | Catálogo e arquivo presentes |

Total inicial: 31 skills expostas na sessão, mais `review-agent` encontrado apenas em disco. Não se inferiu que todo pacote no cache esteja ativo. Nenhuma preexistente foi copiada para o projeto. Eventuais sobreposições entre famílias existentes foram registradas, sem remover preferências pessoais.

## Instalada: remotion-best-practices

| Campo | Resultado |
| --- | --- |
| Origem | [remotion-dev/skills](https://github.com/remotion-dev/skills), ligado pela [documentação oficial Remotion](https://www.remotion.dev/docs/ai/skills) |
| Mantenedor | Organização Remotion (`remotion-dev`) |
| Revisão imutável | `30d4553ecd46fbc5212fd0ff006ae43af522158b` |
| Versão declarada | `4.0.539` |
| Origem na árvore | `skills/remotion-best-practices/` |
| Destino | R/remotion-best-practices |
| Finalidade | Roteamento para referências de composição, legendas, mídia, renderização e outras tarefas Remotion |
| Instalador executado | Helper de sistema OpenAI `install-skill-from-github.py`, com `--method download`, `--ref` fixo e `--dest` local |
| Conteúdo exato | 144 arquivos, 1.183.282 bytes; lista e SHA-256 em [remotion-files.sha256](remotion-files.sha256) |
| Descoberta | Um único `SKILL.md`; já apareceu no catálogo atualizado desta sessão após a instalação |
| Exclusões | Nenhum `package.json` da raiz upstream, nenhuma das outras 11 skills de topo, sem `.claude/`, links simbólicos, hooks ou dependências npm |

### Inspeção e limites

O pacote atual é mais amplo que um guia curto: inclui 88 Markdown, 13 YAML, 13 SVG, 4 MJS, 6 TS, 10 TSX, 8 JSON e 2 GeoJSON. As pastas `remotion-*` internas são referências do pacote, não instalações separadas. Há cópias de exemplos de mapas no conteúdo upstream; foram mantidas para preservar a distribuição e seus links.

Foram lidos o roteador, os guias de entrada, instruções de criação/upgrade, transcrição e voz, e os dois scripts MJS distintos. Houve inspeção estática de comandos, escrita de arquivos, variáveis de ambiente e chamadas externas no restante do conteúdo. Não se executou código de exemplo ou script do pacote.

- Os MJS de geodados leem entradas e escrevem JSON/GeoJSON; um depende de `@turf/turf`. Há duas cópias de cada script. Não são hooks de instalação e não foram executados.
- Guias sugerem criação de projetos, instalação/atualização de pacotes, abertura de Studio, modelos Whisper/WebGPU, serviços de mapas e ElevenLabs. Essas instruções excedem S0.1 se executadas; `AGENTS.md` restringe seu uso ao escopo de uma tarefa Remotion explícita. Não foram solicitadas chaves nem enviados arquivos do usuário a serviços.
- O guia de busca inclui um identificador/chave publicado pelo próprio upstream para sua busca de documentação. Não é credencial do usuário; não foi usado nesta tarefa. A configuração efetiva e os privilégios desse serviço não foram auditados.
- Não foi detectado hook de execução automática no diretório selecionado; o instalador só transfere/copia arquivos. Isso não certifica todos os exemplos como seguros para qualquer entrada ou ambiente.
- O frontmatter upstream usa `version` no nível superior, campo adicional não listado na especificação consultada. O validador estrito local `quick_validate.py` rejeita esse campo; o Codex efetivamente descobriu a skill. O conteúdo oficial foi preservado, sem remover metadados para mascarar a ressalva.
- A API do GitHub não identificou licença e não havia `LICENSE` na raiz baixada. A origem oficial foi confirmada, mas condições de redistribuição/reuso de exemplos continuam pendentes de esclarecimento antes de publicar um repositório ou incorporar exemplos ao produto.

### Por que não foi usado npx

A documentação atual mantém `npx skills add remotion-dev/skills`. O CLI do ecossistema permite seleção de skill/agente; suas fontes também descrevem telemetria. Evitamos executar um pacote npm adicional durante o setup: o helper OpenAI já instalado e inspecionado suporta `--dest`, `--path` e revisão fixa, não executa scripts do pacote e não escreve no diretório pessoal de skills quando esse destino é informado.

## Candidatas avaliadas e adiadas

Avaliação de metadados, instruções principais e adequação ao escopo; os pacotes completos das candidatas não foram instalados nem certificados. Popularidade não foi critério de instalação. Os caminhos são relativos aos repositórios das linhas.

| Candidata e repositório | Mantenedor | Finalidade/relevância futura | Sobreposição com Codex atual | Riscos e recomendação |
| --- | --- | --- | --- | --- |
| [ffmpeg](https://github.com/n0an/ffmpeg-skill/tree/aec7706a3602134bfc606cc8a85eb010dfaa22ad/ffmpeg) | n0an, comunidade; não é FFmpeg oficial | Receitas de corte, filtros, áudio e encoding; relevante a processamento | Codex já pode consultar a documentação oficial e operar FFmpeg existente | Revisar comandos, arquivos de saída e portabilidade antes de uso; não auditada integralmente. **Adiar** até tarefa de mídia. |
| [python-testing-patterns](https://github.com/wshobson/agents/tree/0874a27b17a22e2b7c2e2bcd725768e0803cad06/plugins/python-development/skills/python-testing-patterns) | wshobson/comunidade | Desenvolvimento Python e testes pytest/async | Alto: Python e testes já fazem parte da capacidade nativa | Pode induzir dependências/padrões genéricos sem necessidade. **Adiar** até existirem contratos e código Python. |
| [fastapi-templates](https://github.com/wshobson/agents/tree/0874a27b17a22e2b7c2e2bcd725768e0803cad06/plugins/api-scaffolding/skills/fastapi-templates) | wshobson/comunidade | Estruturas e testes para FastAPI, se essa opção for escolhida | Alto: scaffolding e documentação oficial acessíveis nativamente | Incentiva estrutura, banco e dependências antes de decidir a stack. **Adiar**; não autoriza escolher FastAPI. |
| [playwright](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/playwright) | OpenAI | Automação/verificação de navegador; útil quando houver interface | Parcial com as ferramentas de navegador/computer use já presentes | Skill orientada a CLI, não uma suíte automática de testes; wrapper Bash/npx e browsers exigem revisão no Windows. **Adiar**. |
| [security-best-practices](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/security-best-practices) | OpenAI | Revisão/hardening de linguagens e frameworks suportados | Parcial com revisão nativa e Ponytail já disponível | Guia não equivale a scanner/certificação; exige código e referências específicas. **Adiar** até revisão de segurança solicitada. |
| [security-threat-model](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/security-threat-model) | OpenAI | Fronteiras de confiança e ameaças fundamentadas no repo | Parcial com análise nativa | Antes de arquitetura real produziria hipóteses demais; requer validação de premissas. **Adiar**. |
| [define-goal](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/define-goal) | OpenAI | Definir metas verificáveis para trabalho persistente | Muito alto: ferramentas de meta já existem nesta sessão | Não é um planejador arquitetural genérico; requer pedido explícito de meta. **Adiar**, sem criar meta para S0.1. |
| [notion-spec-to-implementation](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/notion-spec-to-implementation) | OpenAI | Converter especificações do Notion em planos/tarefas | Planejamento nativo basta para documentos locais | Depende de Notion/MCP/OAuth e propõe setup desse serviço quando ausente. **Rejeitar para o setup atual**; reavaliar só se Notion for escolhido. |
| [architecture-decision-records](https://github.com/wshobson/agents/tree/0874a27b17a22e2b7c2e2bcd725768e0803cad06/plugins/documentation-generation/skills/architecture-decision-records) | wshobson/comunidade | Documentar decisões e alternativas | Alto: modelo curto de ADR pode ser escrito nativamente | Inclui `brew`/adr-tools e cerimônias de revisão sem necessidade aqui; **adiar**. |
| [openapi-spec-generation](https://github.com/wshobson/agents/tree/0874a27b17a22e2b7c2e2bcd725768e0803cad06/plugins/documentation-generation/skills/openapi-spec-generation) | wshobson/comunidade | Documentação técnica de APIs/contratos | Alto: documentação e geração de especificação nativas | Pressupõe API e pode antecipar geradores/SDKs; **adiar** até contrato definido. |

O [catálogo oficial OpenAI](https://github.com/openai/skills) foi inspecionado via API em árvore completa, sem truncamento, na revisão indicada acima. Não foi encontrada skill genérica `plan`/`create-plan` nessa árvore; `.experimental` retornou 404. Uma referência genérica a skills de planejamento na documentação não comprova sua presença nesta instalação. Planejamento arquitetural e documentação Markdown continuarão nativos, com as regras do projeto, até haver necessidade concreta de outra skill.

## Atualização e remoção

- **Remotion:** não use atualização global ou irrestrita. Consulte documentação e nova revisão, baixe para temporário, inspecione instruções/scripts/diff, coordene o arquivo compartilhado, compare com modificações locais e só então substitua o pacote com autorização para a manutenção. O helper aborta se o destino já existir: não apague esse destino automaticamente para contornar a proteção. Atualize versão, revisão, inventário e manifesto de hashes juntos. A consulta ao upstream pode revelar mudanças no empacotamento.
- **Remoção Remotion:** em tarefa autorizada, confira alterações locais e o caminho absoluto `R/remotion-best-practices` resolvido sob a raiz do projeto. Preserve trabalho antes de remover exclusivamente essa pasta; atualize inventário, hashes e referências. Não remova `.agents/` inteira nem skills pessoais/de sistema. Nenhuma remoção foi testada, para preservar a instalação pedida.
- **Sistema:** atualização pelo mecanismo do Codex; não duplicar `skill-creator`/`skill-installer`, não editar a instalação global nesta tarefa.
- **Plugins:** gerenciar pelo mecanismo próprio do app/plugin em tarefa autorizada; o cache não deve ser editado manualmente. Nada atualizado/removido em S0.1.
- **Skills pessoais:** origem de algumas não confirmada. Antes de atualizar/remover, identificar upstream e preservar alterações do usuário; nenhuma manutenção global autorizada aqui.

## Referências consultadas

- [Skills locais e locais de descoberta no Codex](https://learn.chatgpt.com/docs/build-skills) (o endereço antigo `developers.openai.com/codex/skills/` redirecionou para este).
- [Skill Creator oficial](https://github.com/openai/skills/tree/main/skills/.system/skill-creator) e [Skill Installer oficial](https://github.com/openai/skills/tree/main/skills/.system/skill-installer); os manifestos também foram lidos diretamente pela origem raw na revisão OpenAI fixada.
- [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra): instruções enxutas e workflows específicos motivaram evitar duplicações.
- [Especificação Agent Skills](https://agentskills.io/specification): `SKILL.md`, nome/descrição e recursos opcionais.
- [Remotion Agent Skills](https://www.remotion.dev/docs/ai/skills), [árvore Remotion fixada](https://github.com/remotion-dev/skills/tree/30d4553ecd46fbc5212fd0ff006ae43af522158b) e [CLI do ecossistema](https://github.com/vercel-labs/skills).

Todos esses endereços foram acessados. Conteúdo de arquivos foi conferido também via API/raw quando a página GitHub só entregou navegação. Não foram inventadas contagens de popularidade ou garantias de segurança.

## Revalidação S0.2

Os 32 caminhos de skills preexistentes registrados na tabela foram novamente encontrados. A skill local Remotion confere com o manifesto e com um novo download da revisão original: 144 arquivos, 1.183.282 bytes. Todos os 88 Markdown foram lidos para a inspeção de links; 139 ocorrências locais resolvem dentro da skill, sem destino ausente. Treze metadados YAML e seus ícones foram conferidos. Scripts e exemplos não foram executados.

| Grupo | Estado efetivamente verificado | Dependências/limites | Recomendação |
| --- | --- | --- | --- |
| Remotion local | Nome, caminho e descrição incluídos pelo CLI no prompt; conteúdo e referências legíveis; íntegra | Runtime Remotion, Mediabunny, Bun, GPU e `@turf/turf` não instalados/validados por esta tarefa. Ausência de runtime de produto é intencional. | Manter fixada e usar só sob tarefa Remotion autorizada. Não redistribuir como licença esclarecida. |
| skill-creator / skill-installer | Arquivos presentes; validador local executa com Python/PyYAML | Validador rejeita `version`; o instalador não foi executado novamente | Manter sistema; não duplicar. |
| openai-docs | Fontes oficiais acessíveis; documentação usada na auditoria | Arquivos internos foram atualizados automaticamente na inicialização do CLI; não se certificaram todos os helpers | Manter; considerar risco de cache compartilhado entre builds do desktop/CLI. |
| antislop e cinco complementos | Manifestos presentes; sem nova cópia local | Sobreposição de regras de UI/texto e uso condicional; não pertinentes ao setup documental | Preservar preferências pessoais; não instalar wizard ou ponteiros no projeto nesta fase. |
| find-skills | Manifesto presente | Sugestões de `npx`/instalação global não se sobrepõem ao escopo do usuário; nenhum CLI de skills executado | Manter como descoberta opcional, sem instalação em lote. |
| Ponytail e cinco auxiliares | Seis manifestos presentes | Sobreposição parcial com revisão nativa; relatórios/benchmarks não executados | Usar somente quando a tarefa pedir o fluxo correspondente; não copiar para o repo. |
| Plugins de documentos, planilhas, slides, PDF, imagens, visualização, sites, pets e computer use | Caminhos presentes; ferramentas anunciadas na sessão | A disponibilidade da ferramenta não prova cada runtime, app externo ou serviço conectado; fluxos não foram disparados | Nenhuma remoção global automática. Não são dependências do produto; usar quando necessário. |
| review-agent | Presença em disco | Não exposta no catálogo desta sessão; operacionalidade não atestada | Não duplicar nem ativar por suposição. |
| plugin-creator | Surgiu no cache de sistema durante o diagnóstico nativo; 11 arquivos novos | Materialização automática do CLI, não instalação selecionada para o projeto; não foi invocada | Registrar o desvio; não usar nem remover por iniciativa desta tarefa. |
| Dez candidatas complementares da S0.1 | Continuam apenas recomendações | Bun, uv e pytest não foram encontrados como comandos; isso não prova ausência de todos os módulos equivalentes. Bash aponta para um alias WindowsApps, sem execução validada. `gh` está disponível. | Permanecem adiadas/rejeitada para o setup, conforme a tabela histórica. |

Não foi encontrada duplicação de Remotion entre `.agents/skills/` e `.claude/skills/` (a segunda pasta nem existe). Os quatro MJS oficiais são duas cópias de cada um de dois scripts; preservados. Recursos de criação de skills em motores diferentes não constituem, por si só, duplicação dentro de um catálogo. Nenhuma instalação local da S0.1 foi considerada injustificada: Remotion havia sido solicitada expressamente, embora seja relevante só para tarefas futuras.

### Formato, licença e manutenção

O erro estrito é real: `version` no topo não integra a lista fechada do [validador de referência Agent Skills](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/src/skills_ref/validator.py). O padrão prevê extensões dentro de `metadata`. O helper local OpenAI também não aceita `compatibility`, que a especificação atual aceita; ele não é prova de equivalência completa ao padrão atual. O [parser do Codex 0.153.4](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/skills/src/parser.rs) e o teste do prompt sustentam a compatibilidade operacional observada com `version`. Nenhum conteúdo upstream foi corrigido ou reescrito.

A investigação de licença encontrou a [questão oficial #28](https://github.com/remotion-dev/skills/issues/28): foi encerrada pelo próprio autor e os comentários consultados não contêm concessão dos mantenedores. A licença do repositório principal é diferente de uma declaração explícita sobre esta distribuição. A pendência permanece; não se presume redistribuição autorizada.

No conjunto global monitorado, o diagnóstico gerou 12 arquivos novos (11 de `plugin-creator` e uma referência em `openai-docs`) e alterou nove arquivos preexistentes (marcador mais oito de `openai-docs`). Configurações e skills pessoais permaneceram iguais. Não houve instalação por npm/pip ou helper de skills, mas houve essa materialização automática fora do projeto. O relatório detalha o incidente; evitar novos diagnósticos com o home real sem considerar esse efeito. Para futuros testes, avaliar home temporário isolado e comparar o estado antes/depois, sem copiar credenciais por iniciativa própria.
