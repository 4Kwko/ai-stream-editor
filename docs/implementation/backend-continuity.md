# Retomada do backend

## Atualização de formato — 2026-10-30

Usuário confirmou16:9 padrão, com opção9:16/câmera em cima/conteúdo embaixo, configurada uma vez. Backend implementado e API8765 ativa: GET/PATCH automation.output_format, snapshot por VOD/projeto/corte, metadados de formato/layout/aviso na galeria. Não gerar ambas as versões e não reconverter acervo. Legacy sem campos continua9:16/full_frame. [Contrato](../coordination/integration-contract.md), [ADR004](../decisions/004-output-formats-and-camera.md), [validação](output-formats.md).

94 testes e11 subtestes passaram; depois25 focados passaram com centralização na borda. OpenCV/FFmpeg reais em vídeo controlado produziram1920×1080 e1080×1920, áudio/legenda, câmera detectada e hashes preservados. A imagem pública de teste/ASR simulado são identificados no relatório. Não equivale a validar a câmera do João em VOD real.

Inicializador existente reabriu somente a API que estava parada; Vite6812/5173 preservado. GET real: padrão16:9, supervisor waiting,7 projetos/5 vídeos antigos preservados. Evidência `backend/.test-data/output-formats-native/live-evidence.json`. PIDs são registros da ocasião: verificar identidade/porta antes de qualquer parada. Próximo passo do Claude: seletor global e proporção/layout/aviso dos cards; GPT não editou frontend. A busca do canal continua automática.

## Prioridade atual — 2026-10-30

A nova direção do usuário substitui o editor manual: VODs do canal configurado são descobertos/obtidos/analisados/renderizados pelo backend; a galeria apenas recebe Gostei/Não gostei. Leia [automação](automation.md), [ADR003](../decisions/003-automatic-vods-and-gallery.md) e a extensão no início do contrato antes do histórico abaixo. Não retomar a expansão do editor.

Backend implementado e API8765 atualizada, supervisor ativo e canal joaomontagner aguardando VOD disponível. Consulta real retornou zero vídeos. Fonte pública não exige configuração de credenciais nesta rota; conteúdo restrito falha, sem extrair cookies. Frontend/launcher do Claude preservados; comando local existente mantido. Rotas novas: GET/PATCH automation, GET gallery, attachment do MP4; review usa PATCH existente.

Testes:67 afetados aprovados, mais34 de automação/provider após últimos ajustes, com sobreposição. Smoke automático com ASR/FFmpeg reais e fonte sintética45s produziu um vídeo1080×1920 com áudio, sem navegador ou comandos de processamento; avaliação persistiu após reinício sem novo job. Evidência `backend/.test-data/automation-live-20261030/native-c0d8265057/evidence.json`. Nenhum VOD real obtido; essa validação e qualidade editorial permanecem pendentes de conteúdo disponível.

Galeria real conferida pelo GPT: status waiting,5 cortes sintéticos anteriores, reprodução efetiva, Não gostei/filtro/recarga, depois Gostei/filtro; revisão e jobs intactos, hash do MP4 preservado. Evidência `backend/.test-data/automation-live-20261030/gallery-ui-evidence.json`. Claude mantém seu próprio relatório/testes; seu último status ainda registrava404 antes da atualização da API. Usar o novo `Automation.gallery_updated_at` para avisar cortes novos, inclusive com falha parcial; pedido registrado no backend-status.

Próximo marco: VOD público disponível para validar obtenção real e qualidade editorial. Não repetir setup nem alterar ranking para a fixture. Inicializador/PC precisam permanecer ativos. Não prometer retomada de download/decode, exclusão automática, gravação ao vivo ou publicação.

2026-10-29. Leia `AGENTS.md`, a autorização atual, `docs/coordination/backend-status.md`, o contrato e o status do frontend. GPT mantém backend/scripts/contrato/README; não edita frontend nem arquivos do Claude. Nenhuma ponte autenticada direta com Claude foi estabelecida; coordenação pelos arquivos de status.

## Estado entregue após a execução prolongada

- Backend implementado, ambiente `backend/.venv` instalado e modelo base em `%LOCALAPPDATA%/AIStreamEditor/models/base` preparado.
- API e frontend reais passaram juntos por importação de vídeo sintético, análise, edição, preview, aprovação e exportação. Modo mock não foi usado nesse fluxo.
- Suíte integrada: **95 testes e 21 subtestes passaram**. Após o último ajuste de publicação, os 29 testes afetados da API/ciclo de vida passaram novamente. Não confundir os mocks identificados nos testes com os smokes reais.
- Cancelamento imediato na fila, falha de persistência no encerramento, revisão/cache de preview, correções de legenda por variante e exportação com histórico/recuperação estão implementados. Intenções de exportação são internas; não remover à mão nem aceitar sucesso só por nome de arquivo.
- Model base real em fixture630s: transcrição5,9666s; pico residente407,223MiB e privado amostrado1.954,922MiB. Muito silêncio, sem extrapolar para VOD contínuo. Análise v2 retorna zero candidatos quando não há evidência mínima.
- Mídia inclui rotação, SAR anamórfico/reset_sar, paginação ASS e watchdog por avanço real. Ver os relatórios de análise/mídia para métodos e limites.
- Outra passagem real na interface, com fonte visual variável, produziu `backend/.test-data/integration-extended-63b48748/corte_ff1ecd58.mp4` e `_2.mp4`: 24,25s,1080×1920, áudio, correção de legenda e dos dois limites. Recarga/reinício preservaram corte e preview; a segunda exportação não substituiu a primeira.
- Novo inicializador: `scripts/start-local.ps1`. Diagnóstico/espaço sem gravação: `scripts/check-local.ps1` e `-StorageOnly`. Não instalar silenciosamente nem encerrar serviços preexistentes. A API Windows usa SelectorEventLoop por processo para evitar o travamento observado com Proactor/Python3.12 ao desconectar vídeo.
- Smokes reais: `backend/.test-data/launcher-06aaece9/` (três respostas de vídeo abortadas, shutdown e Vite preservado) e `backend/.test-data/shutdown-a5c114d48f/` (decode nativo ativo, shutdown0,859s, canceled persistido antes de recuperar, sem filhos). O código3 do processo isolado após CTRL_BREAK não foi apresentado como retorno zero.
- Servidor de backend desta execução foi iniciado na porta 8765. Frontend já estava em 5173 por outra sessão. Verifique health antes de iniciar; não encerre processos de outra sessão.

## Próximo passo

1. Usuário autorizou avaliação local e indicou o canal Twitch joaomontagner. A lista pública de transmissões anteriores e o Estúdio de Vídeo com Todos os vídeos não mostraram gravações. Falta gravação local ou VOD específico disponível; não inferir causa, procurar mídia pessoal nem pedir novamente a autorização já dada. Nenhum download ou processamento real foi feito. Seguir `vod-evaluation.md` quando houver fonte disponível.
2. Claude já registrou59 testes e seu percurso próprio. O código novo de recentes/histórico/warnings/cancelamento e sucesso vazio também passou no GPT. Restam consumir as extensões aditivas `Project.source_available`/`source_status` e `result.empty_reason`; tipos/mocks e UI pertencem ao Claude. Não bloquear exportação de preview aprovado só porque a fonte está ausente.
3. Só corrigir novas falhas demonstradas. Não reauditar setup nem repetir toda a suíte sem motivo. Alterações deste lote no Service são de metadados/mensagens, sem mudar ranking ou processamento; contrato existente continua compatível.

Os lotes independentes estão concluídos no escopo verificado. Restam avaliação com VOD disponível e apresentação das duas extensões pelo Claude. Não apagar dados para encerrar a tarefa: manter previews/exports; retenção futura exige política aprovada. Não houve instalação limpa adicional.

## Lote posterior de integração e avaliação

Runner `benchmark_analysis.py` ganhou `--speech-layout continuous`; sparse continua padrão. Após os pedidos opcionais do Claude, Project ganhou disponibilidade/estado da fonte por metadados e a análise ganhou motivo factual de vazio. Quatro testes do runner e16 da API passaram (20 afetados em6,71s), incluindo sucesso HTTP com warning/histórico sob falha controlada de commit, fonte ausente/alterada/inacessível e preview aprovado exportável sem original. Nenhuma dependência, endpoint ou heurística nova.

Benchmark real offline: `backend/.test-data/analysis-validation/run-f1a655c0c7/evidence.json`,630s de mesma fala Maria sem pausas adicionais,20,5316s de transcrição; residente Windows545,238MiB, privado amostrado2.063,633MiB, excluindo filhos FFmpeg. Não usar como previsão de VOD real.

Novo percurso da UI real: `backend/.test-data/integration-currentlot-79fe99d7/evidence.json`. Recentes, vazio sem retry, reload durante análise, cancelamento de render, edição de texto/limites, aprovação, dois MP4 e histórico após recarga. Arquivos21s/1080×1920/áudio, primeiro hash preservado. Warning visual e cancelamento de exportação foram verificados à parte em mock identificado; a cópia real terminou rápido demais para cancelar no navegador.

Relatórios: `integration-evaluation-report.md`, `continuous-speech-validation.md` e `vod-evaluation.md`. A fila tem complemento atual antes do quadro histórico. Frontend e suas configurações permaneceram intocados pelo GPT.

API deste lote atualizada graciosamente de PID7240 para30244 (lançador do venv20360) após confirmar zero jobs ativos; frontend5173 preservado. Health pronto, projeto de integração existente retornou `source_available: true`/`source_status: available` e histórico manteve duas exportações. Recarga no navegador preservou texto/limites, revisão3, aprovação, preview e histórico. Evidência `backend/.test-data/integration-currentlot-79fe99d7/api-extension-live.json`. PIDs são registro da ocasião: conferir porta/identidade antes de qualquer ação futura. Novos campos não reescrevem jobs antigos.

O subagente atingiu o limite após executar o smoke de encerramento. A evidência foi conferida pelo GPT e documentada em `shutdown-validation.md`; não reabrir a tarefa como se só faltasse rodar aquele teste nem habilitar cobrança adicional.

Conferência da retomada: `backend/.test-data/integration-extended-63b48748/final-evidence.json`, com dois exports, primeiro hash preservado e Range/revisão/MP4 verificados. A interface estava parada e foi reaberta pelo inicializador; a API existente foi reutilizada. O LOCALAPPDATA fornecido pelo app pode apontar para o LocalCache de seu pacote; consulte `check-local.ps1` para o caminho efetivo, sem tratar redirecionamento como perda de modelo ou mover dados automaticamente.

Última leitura do Claude confirmou a integração real feita por ele e apontou legenda pequena/baixa. GPT ajustou fonte/margem para63/288px em1080×1920, rodou os20 testes de mídia+11 subtestes (aprovados), inspecionou `legibility-raised.png` e atualizou o preview integrado. API foi reiniciada graciosamente apenas após confirmar ausência de jobs ativos; frontend preservado. As exportações anteriores continuam intactas e usam o perfil da ocasião.

Prévia final para revisão: `backend/.test-data/integration-extended-63b48748/legibility-integrated.mp4`, com job registrado no JSON correspondente. É cópia do preview atualizado via interface, não uma terceira exportação. A pasta mantém os dois MP4 de exportação anteriores. Os links da documentação foram verificados após o fechamento.

## Restrições preservadas

Sem commits, branches, worktrees, instalação global, mudanças de sistema/WSL, cobrança extra, serviços pagos, deploy, upload de mídia ou leitura de credenciais. Não iniciar Codex CLI com home real. Não mexer na skill Remotion. Download de pesos públicos já preparado não autoriza envio de conteúdo nem uso de provedores externos.
