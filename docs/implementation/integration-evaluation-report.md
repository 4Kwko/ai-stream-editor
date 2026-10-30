# Lote de integração e preparação da avaliação

2026-10-29. Responsável: GPT. Escrita restrita a runner/testes, metadados/mensagens do Service e documentos próprios. Nenhuma alteração de frontend, configurações do Claude, regras compartilhadas, skill Remotion ou heurística do produto.

## Entregas verificadas

| Frente | Resultado | Evidência / limite |
| --- | --- | --- |
| Contrato | Compatível com as novas chamadas do frontend; dois pedidos adicionais atendidos | `source_available`/`source_status` e `result.empty_reason` adicionados; nenhum endpoint novo |
| Testes afetados | 20 aprovados em6,71s | 16 da API e4 do runner; não repetiu a suíte inteira |
| Fala mais contínua | Reconhecimento real offline de630s em20,5316s | Mesmo trecho Maria repetido sem pausas adicionais; não é um VOD real |
| Avaliação editorial | Roteiro preparado; fonte real indisponível | Canal Twitch indicado pelo usuário está sem vídeos nas duas listas consultadas; falta gravação local ou VOD disponível |
| Fonte e resultado vazio | Verificados por HTTP | Missing/changed/unavailable e distinção entre transcrição vazia/sem candidatos; preview aprovado exporta mesmo sem o original |
| Projetos recentes | Lista e abertura reais | Nome/data/duração/estado/quantidade mostrados no navegador |
| Sucesso vazio | Bug de retry corrigido pelo Claude e conferido pelo GPT | Projeto silencioso abriu com resultado vazio e ação Escolher outro vídeo; sem chamada inválida de reanálise |
| Retomada | Análise real em andamento retomada após recarga | Etapa Transcrevendo em PT-BR e progresso por etapa observados |
| Cancelamento de render | Real, pela interface | Cancelamento solicitado aguardou canceled; preview ausente permaneceu ausente; nova geração funcionou |
| Edição e revisão | Dois limites e texto corrigido preservados | Corte0,1–21s, revisão3, aprovado e preview atual após salvar/recarregar |
| Exportação e histórico | Dois MP4 distintos e histórico persistente | 1080×1920, áudio,21s; hash da primeira preservado; fonte preservada desde a primeira exportação |
| Warning HTTP | Sucesso/caminho/histórico mantidos com falha controlada de commit | Transcrição simulada e FFmpeg real no teste API; sem mudar ACL/banco do produto |
| Warning na UI | Aviso junto do sucesso e caminho, sem pedir nova exportação | Verificado em modo demonstração explícito, sem arquivo real |
| Cancelamento de exportação na UI | Canceled na nova tentativa, resultado anterior preservado | Modo demonstração explícito; não é evidência de cancelamento nativo durante a cópia |

O modo padrão da interface foi usado para as verificações reais. Modo demonstração é tratado separadamente abaixo, sem alegar reconhecimento ou gravação real.

## Arquivos e reprodução

- `backend/tests/benchmark_analysis.py`: opção de densidade e recusa antecipada de dimensões incompatíveis; sparse continua padrão.
- `backend/tests/test_benchmark_analysis.py`: quatro casos de cronograma/PCM e validação, com stubs de container identificados.
- `backend/ai_stream_editor/service.py`: fonte disponível/ausente/alterada/inacessível por metadados e motivo factual de análise vazia, sem mudar ranking.
- `backend/tests/test_api.py`: succeeded+warning/histórico sem snapshots internos; fonte removida/alterada/inacessível; dois motivos de vazio; exportação de preview aprovado sem fonte.
- [Roteiro de VOD](vod-evaluation.md) e [medição contínua](continuous-speech-validation.md).

Testes executados a partir de backend, com temporários locais:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_api.py tests/test_benchmark_analysis.py --basetemp .test-data/integration-evaluation-v2
```

O runner real e seus parâmetros estão no relatório de medição. Original sintético preservado por hash. As20 verificações não substituem os resultados históricos da suíte95/21 nem os59 testes próprios registrados pelo Claude. A sinalização da fonte e o motivo específico do vazio ainda dependem do consumo dos campos pelo frontend.

## Evidências do novo percurso

`backend/.test-data/integration-currentlot-79fe99d7/evidence.json`, com metadados, estados, jobs, histórico e FFprobe. `first-export.json` registra o hash anterior à segunda exportação. MP4s:

- `corte_53749628.mp4`;
- `corte_53749628_2.mp4`.

Fonte: fixture contínua em `backend/.test-data/analysis-validation/run-f1a655c0c7/`. Nenhum vídeo pessoal usado. A segunda exportação foi rápida demais para uma tentativa útil de cancelamento nativo pelo navegador; não foi registrada como cancelada. O botão estava disponível durante o estado ativo e o sucesso efetivo foi respeitado.

Depois das extensões aditivas, somente a API desta tarefa foi reiniciada graciosamente, com zero jobs ativos; frontend preservado. `api-extension-live.json` registra health pronto, novos campos disponíveis para o mesmo projeto e duas exportações preservadas. Jobs anteriores mantêm os resultados originais, sem preencher retroativamente `empty_reason`.

## Demonstração controlada separada

Em `http://localhost:5173/?mock=1`, a faixa de demonstração estava visível e informou que nada seria lido/exportado. Pasta fictícia contendo aviso provocou succeeded com caminho simulado e warning. A tela manteve o resultado e explicou que não era preciso exportar novamente por causa do aviso. Depois, outra tentativa foi cancelada: a tela aguardou o estado final e conservou o resultado anterior com seu aviso/histórico.

Nenhum arquivo desse caminho fictício foi tratado como exportação real. A verificação de falha de banco real controlada pertence ao teste HTTP com fixture, não a esta demonstração. A aba mock foi fechada; a aba com backend real permaneceu disponível.

## Limites e dependências

- O usuário autorizou avaliação local e indicou `https://www.twitch.tv/joaomontagner`. Em leitura, a página pública `/videos?filter=archives&sort=time` mostrou “Nenhum vídeo encontrado”; o Estúdio de Vídeo, com filtro Todos os vídeos, mostrou “Você não tem vídeos que correspondam a esses filtros.” Nenhum download, publicação ou mudança de configuração. Não se conclui a causa da ausência. Falta gravação local ou link de VOD disponível. Nenhum VOD real foi processado; não há precisão editorial calculada sem revisão humana/referência.
- Medição de memória do benchmark inclui Python/bibliotecas nativas, exclui filhos FFmpeg. Fala repetida não mede diversidade de assunto, ruído, múltiplos falantes ou crescimento ao longo de horas.
- Sucesso com zero sugestões não significa necessariamente falta de fala: `empty_reason` agora distingue ausência de segmentos retornados de transcrição existente sem candidatos. Claude ainda precisa consumir o novo campo, com fallback para jobs anteriores.
- Não houve teste novo de instalação limpa, retenção/exclusão automática, GPU, WSL ou serviços externos. Não há necessidade demonstrada para ampliar a stack.
- Próximo passo: usuário escolher/autorizar amostra representativa e revisar candidatos conforme o roteiro. O commit inicial continua fora da autorização.
