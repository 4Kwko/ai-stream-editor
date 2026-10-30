# Medição complementar com fala sintética mais contínua

2026-10-29. Runner existente ampliado em `backend/tests/benchmark_analysis.py`; algoritmo de seleção, transcritor do produto e frontend não foram alterados. Não havia VOD real autorizado no pedido ou nos documentos atuais.

## Mudança e evidência

`--speech-layout continuous` repete a mesma fala Maria PT-BR sem inserir pausas adicionais entre as cópias. As pausas internas da fala original permanecem. O modo sparse anterior continua sendo o padrão. A última cópia é cortada exatamente no fim; o runner registra eventos e cobertura nominal dos trechos inseridos, que não é atividade de voz medida nem conteúdo único.

Foi corrigida também a validação das dimensões do runner: larguras abaixo de160px são recusadas antes de extrair/transcrever, em vez de falhar somente no render. Não há alteração do limite do produto nem adoção de outra stack.

Quatro testes novos verificam PCM contínuo sem lacunas adicionais, cronograma sparse, cópia final parcial, duração exata e rejeição antecipada de entrada inválida. Normalização/container são stubs explicitamente identificados nesses testes; a execução abaixo usa FFmpeg e reconhecimento reais.

## Execução real offline

```powershell
cd backend
.\.venv\Scripts\python.exe tests\benchmark_analysis.py --run-real --speech-layout continuous --duration 630 --model-dir 'C:\Users\jvmon\AppData\Local\AIStreamEditor\models' --model base
```

Evidência: `backend/.test-data/analysis-validation/run-f1a655c0c7/evidence.json`, com vídeo, transcrição sintética e preview diagnóstico no mesmo diretório. Pasta única, sem sobrescrever execuções anteriores. Fonte sintética preservada por hash; nenhuma busca de arquivo pessoal, instalação, download de pesos ou comunicação externa.

Windows/Python3.12.10, faster-whisper1.2.1, CTranslate2 4.8.4, CPU/int8 e quatro threads de reconhecimento. Vídeo testsrc2 320×180 a8fps,630s; cobertura nominal de trechos inseridos630s/630s. Foram reconhecidos146 segmentos e1.002 palavras, contra29 segmentos e238 palavras na fixture anterior com pausas adicionais.

| Etapa | Tempo de parede |
| --- | ---: |
| Gerar mídia | 2,7922s |
| Extrair áudio | 0,3114s |
| Transcrever, carga inicial do modelo incluída | 20,5316s |
| Sugerir momentos | 0,0406s |
| Render diagnóstico360×640 | 0,7877s |

Foi gerado um candidato0–45,94s; o preview diagnóstico tem46s devido à quantização de8fps. Isso mede processamento e não prova utilidade editorial: a fala é repetida e a deduplicação reduz conteúdo semelhante. Não se mudou o ranking para obter outro resultado.

## Memória e cancelamento

Durante a transcrição, pico residente amostrado:439,426MiB; contador de pico residente do Windows até o fim dessa etapa:545,238MiB. Pico privado comprometido amostrado:2.063,633MiB (aproximadamente2,02GiB), terminando a etapa em1.794,461MiB. Amostragem a cada50ms pode perder picos, por isso o contador residente do Windows é maior.

As métricas abrangem somente o processo Python e suas bibliotecas nativas, excluindo FFmpeg/FFprobe filhos. Não há medição do pico total de todos os processos no render. Transcrição e render têm escopos/durações diferentes; não interpretar sua razão de tempos como comparação de eficiência.

Cancelamento com modelo aquecido foi observado1,2381s após a solicitação; continua cooperativo. Silêncio real de30s novamente produziu zero segmentos/candidatos. As checagens são funcionais nessa execução, sem garantia de latência geral.

## Comparação e limites

A fixture sparse anterior de630s foi transcrita em5,9666s; a nova levou20,5316s, cerca de3,44vezes esse tempo. Ambas usam o mesmo trecho sintético repetido e a mesma família de runtime/modelo. São execuções distintas, sem controle estatístico de concorrência ou temperatura de cache.

A comparação demonstra a influência da quantidade de fala. Não permite prever tempo de uma live real: faltam variação de assunto, ruído, falantes, música e avaliação editorial. Também não mede crescimento de memória ao longo de horas. Um VOD explicitamente autorizado continua necessário, conforme o [roteiro de avaliação](vod-evaluation.md).
