# Fila da execução prolongada do backend

## Atualização — formatos (2026-10-30)

- Backend/API:16:9 padrão e opção9:16 implementados; preferência capturada ao iniciar VOD e preservada em retries/projeto/corte. Acervo anterior não reprocessado.
- Mídia: normal preserva imagem; vertical tenta câmera acima/conteúdo abaixo com detecção local. Fallback preserva conteúdo e informa aviso. OpenCV apenas no venv.
- Verificação:94 testes/11 subtestes e25 focados posteriores, com sobreposição. Detecção/render positivos reais em mídia controlada;7 projetos/5 vídeos antigos preservados na API real.
- Claude: seletor global16:9/9:16, badge/proporção/layout/aviso na galeria. Nenhuma edição manual por corte; campos/rotas já disponíveis.
- Limite externo: VOD real do canal para validar enquadramento e seleção editorial. [Relatório](output-formats.md).

## Lote atual — automação e galeria (2026-10-30)

| Entrega | Estado | Evidência / limite |
| --- | --- | --- |
| Contrato antes da implementação | Publicado e implementado | GET/PATCH automation, GET gallery, review existente e attachment MP4 |
| Fonte Twitch pública | Implementada; descoberta real verificada | yt-dlp local fixado; canal retornou zero VODs; download real ainda não disponível |
| Supervisor persistente | Implementado/testado | Um VOD por vez, IDs/projeto estáveis,300s, deduplicação e etapas concluídas reaproveitadas |
| Galeria e avaliações | Backend implementado | Paginação SQLite, filtros, arquivo atual, avaliação sem render e persistência |
| Falhas e recursos | Testados | Backoff/tentativas, parcial inválido, espaço/bytes/timeouts, árvore própria encerrada, falha parcial de corte |
| Regressões | Aprovadas |67 testes afetados;34 finais de automação/provider, com sobreposição; corrida de histórico corrigida |
| Pipeline nativo automático | Verificado com fonte controlada |45s sintéticos, ASR/FFmpeg reais, MP4 pronto, avaliação persiste; não é download Twitch |
| Interface Claude | Percurso real verificado pelo GPT | Reprodução, filtros, avaliações/recarga e MP4 sem mudança de revisão/jobs/hash; falta Claude consumir gallery_updated_at |

[Operação e resultados](automation.md). Nova direção substitui a edição manual como fluxo principal; quadros abaixo preservam o histórico. Nenhum Git de escrita, instalação global, upload, publicação ou exclusão de mídia.

## Complemento: integração e avaliação

2026-10-29. Lote posterior concluído no escopo autorizado.20 testes afetados aprovados (16 API+4 runner), após metadados/mensagens adicionais no Service. Heurística preservada. Os apontamentos de UI no quadro histórico abaixo foram atendidos no código novo do Claude e conferidos pelo GPT, com as distinções desta tabela.

| Entrega | Estado | Evidência / pendência |
| --- | --- | --- |
| Contrato de recentes/histórico/job/cancelamento/warning | Conferido | Sem endpoint novo; aviso com sucesso e histórico testado por HTTP |
| Fonte disponível e motivo de vazio | Backend entregue | Campos aditivos,20 testes afetados aprovados; consumir no frontend: Claude |
| Fixture de fala mais contínua | Concluída | Runner existente ampliado;630s repetidos,20,5316s de transcrição, sem extrapolação editorial |
| Roteiro de VOD real | Preparado | [Roteiro](vod-evaluation.md); canal indicado sem vídeos nas listas pública e de produtor; falta fonte disponível e revisão humana |
| Novas telas reais | Verificadas | Recentes, sucesso vazio corrigido, retomada em andamento, edição/revisão e histórico |
| Cancelamento de render real | Verificado | Solicitação intermediária aguardou canceled; nova geração funcionou |
| Exportações reais | Verificadas | Dois arquivos21s/1080×1920/áudio, hash do primeiro preservado, histórico após recarga |
| Warning e cancelamento de exportação na UI | Verificados em mock identificado | Resultado anterior preservado; exportação real rápida demais para cancelamento útil na cópia |

[Relatório completo](integration-evaluation-report.md) e [método da medição](continuous-speech-validation.md). Claude já registrou59 testes e percurso próprio; apresentação dos dois campos novos fica com ele. Não houve nova instalação, busca de mídia pessoal, Git de escrita ou alteração de regras/configurações.

## Quadro histórico do lote de confiabilidade

2026-10-29. GPT mantém este arquivo. Escopo concluído: backend, scripts, contrato e documentação própria. Frontend/configurações do Claude e Remotion preservados. Nenhuma operação Git de escrita, instalação global, envio de mídia, custo ou publicação.

Evidências: **95 testes e 21 subtestes aprovados** na suíte integrada; 29 testes afetados da API/ciclo de vida passaram após o último ajuste de publicação. Execuções reais de reconhecimento, mídia, navegador e processo são distintas dos testes com transcritor simulado. Relatórios: [análise](analysis-validation.md), [mídia](media-validation.md), [encerramento nativo](shutdown-validation.md), [backend](backend.md) e [pedidos ao Claude](../coordination/backend-status.md).

| Tarefa | Estado | Arquivos / problema tratado | Critério e evidência obtida | Limite remanescente |
| --- | --- | --- | --- | --- |
| A1 | Concluída | service/test_service_lifecycle: queued | Canceled imediato; callback não executado com worker bloqueado | Cooperativo se já iniciado |
| A2 | Concluída | service/media/analysis | Cancelamento em extração/render/reconhecimento/exportação, sem publicação cancelada | Nativo: 1,14 s observado, sem garantia |
| A3 | Concluída | service/local/__main__/smoke_shutdown | API com decode real ativo fechou em0,859s, canceled já persistido, sem filhos; falha de banco também libera recursos | Não interrompe nativo à força |
| A4 | Concluída | service/store | Projetos/correções/previews persistem; export publicado reconciliado por identidade | Sem retomar decode/render parcial |
| A5 | Concluída | testes ciclo de vida/API | Duplo render/export, editar/rejeitar durante cópia, cancelar na publicação | Não cobre perda física de dispositivo |
| B1 | Concluída | service/analysis | Limites e tempos relativos válidos em testes e navegador | Quantização pelos frames |
| B2 | Concluída | caption_corrections persistente | Correção volta ao restaurar mesmas palavras; não contamina variante diferente | IDs personalizados sem origem não reconstruídos |
| B3 | Concluída | expected_revision/API | 409 contra edição antiga; mudança invalida preview | Recarga de conflito pertence à UI |
| B4 | Concluída | media/test_media | FFmpeg real: acentos, pontuação, escapes, quebras, texto longo/curto | Paginação proporcional, sem fonética |
| B5 | Concluída na amostra | ASS/PNG1080 | Duas linhas/margens/contorno em fundo variável inspecionados | Não certifica todo vídeo possível |
| C1 | Concluída na matriz | media/probe/render | Sete entradas, mono/estéreo/silêncio, rotação90/270, nomes PTBR e dois SAR | HDR/VFR/multifaixas não certificados |
| C2 | Concluída | flash/beep sintético | Trims0,4/0,9s, A/V0–10ms e legenda no intervalo | Resolução áudio10ms/vídeo50ms |
| C3 | Concluída | service/media | Inválido, removido, alterado, permissão controlada e sem áudio | Não altera ACLs reais |
| C4 | Concluída | export/staging | Destinos/colisões/PTBR e arquivos preexistentes preservados | Não simula todo dispositivo removível |
| C5 | Concluída | publicação/recuperação | MP4 fechado antes do sucesso; falha DB não desfaz resultado; FFprobe real | Identidade não confirmável exige conferir pasta |
| C6 | Concluída backend | histórico/API/store | Revisão/data/caminho persistem e são recuperados em nova instância | Tela de histórico: Claude |
| D1 | Concluída | benchmark_analysis | Fixture630s Maria+pausas+testsrc2; só candidato renderizado | Artificial, pouco densa |
| D2 | Concluída na medição | PCM/benchmark | Waveform<=300s por chamada; picos residente e privado separados | Sem crescimento medido em VOD contínuo de horas |
| D3 | Concluída | benchmark/Job timings | Tempos reais por etapa, runtime/threads/tipo de fixture documentados | Memória/CPU de filhos FFmpeg excluídas |
| D4 | Concluída | diagnostics/service | Categorias/espaço livre somente leitura; ENOSPC/permissão úteis | Permissão é indicativa |
| D5 | Concluída sem exclusão | staging/doctor/docs | Limpa só temporários próprios; relatório e proposta de retenção | Remoção futura exige política do usuário |
| E1 | Concluída | test_analysis | Reação, explicação, rotina, silêncio, repetição, bordas e fronteiras | Casos sintéticos identificados |
| E2 | Concluída baseline | heurística v2 | Contexto inicial, redução de silêncio, dedup por tempo/texto | Pode suprimir histórias de texto parecido |
| E3 | Concluída | reason | Justificativas correspondem aos marcadores usados | Sem análise visual |
| E4 | Concluída | score/contrato/docs | Heurística explicitada; nenhum LLM remoto | Sem probabilidade de viralização |
| E5 | Concluída backend | evidência/silêncio real | Silêncio30s:0 segmentos/candidatos; UI10s:sucesso vazio | Retry da UI precisa correção Claude |
| F1 | Concluída backend | project_summaries/API | Novos primeiro, job/status/count/rotação/SAR, sem transcript em Python na lista | Tela de recentes: Claude |
| F2 | Concluída backend | Project.analysis_job_id/jobs | API informa job running; UI recarrega projeto/correções/preview | UI precisa aproveitar todas as novas rotas |
| F3 | Concluída backend | erros seguros | Arquivo ausente recuperável, disco/permissão,409 e warning | UI ainda não mostra warning de persistência |
| F4 | Concluída | preview/Range | 206/416, no-store, revisão antiga409, ausente missing | Cache externo não auditado |
| F5 | Concluída com pendência UI | navegador real | Fixture longa, edição texto+limites, preview1080, aprovação, export2 e recarga/reinício | Retry após sucesso vazio produz409: Claude |
| G1 | Concluída no escopo | lock/pyproject/setup | Versões/lock exato/pip check sem conflitos; nenhuma dependência nova necessária | Sem instalação limpa adicional |
| G2 | Concluída | start-local/local.py | Reusa Vite, inicia API, recusa porta estranha; processo real de parada/desconexão | Não força processo demorado ao encerrar |
| G3 | Concluída | check-local/diagnostics | Versões/filtros/reset_sar/modelo/dados/API sem criar banco/pasta | Permissão consultada, sem gravar teste |
| G4 | Concluída | README/backend/continuity | Comandos, dados, diagnóstico, reinício e falhas registrados | Avaliação real depende do usuário |
| H | Concluída no código conectado | config/service/media/API | Rede/URL/dispositivos, host/origem, subprocesso sem shell, ASS, preview restrito e colisões | Não é auditoria de sistema/certificação |

## Próximos passos dependentes de outros responsáveis

1. Claude: corrigir retry no sucesso vazio e apresentar recentes/histórico/warnings/cancelamento render/export. Contrato e casos reproduzíveis no backend-status.
2. Usuário: selecionar/autorizar VOD representativo para utilidade editorial, ruído/múltiplas vozes e recursos em conteúdo contínuo. Nenhuma busca de mídia pessoal foi feita.
3. Retenção: manter dados atuais. Proposta futura de lista/seleção antes de remover previews antigos, com política aprovada; sem remoção automática nesta etapa.

Não há bloqueio para repetir o fluxo sintético. Esses limites não autorizam serviços externos, downloads maiores, mudanças de máquina ou edição dos arquivos do Claude. Não houve ponte autenticada direta entre os agentes; arquivos de coordenação são o canal.

Complemento B5 após a última leitura do Claude: fonte/margem elevada para63/288px em1080×1920.20 testes de mídia e11 subtestes passaram após o ajuste; a amostra visual nova foi inspecionada. Não houve repetição da suíte inteira por essa alteração de layout. O frontend-status agora também relata a integração real feita pelo Claude; os pedidos de UI acima permanecem separados disso.
