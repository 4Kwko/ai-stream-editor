# Backend — fluxo local integrado e verificado

## Entregue no backend — formato16:9 padrão e vertical com câmera

2026-10-30. Usuário confirmou16:9 padrão, opção9:16, câmera acima/conteúdo abaixo; não gerar as duas versões nem editar cortes manualmente. GPT altera `media.py`, novo detector local `camera.py`, Service/Automation/schemas, dependência local/lock e testes correspondentes, contrato e documentação própria. Frontend/brief/README geral pertencem ao Claude e ficam preservados.

Extensão implementada no início do contrato: `Automation.output_format` configurável, snapshot por VOD/projeto/corte e metadados de formato/layout/aviso na galeria. Não reconverter vídeos antigos. API8765 reaberta pelo inicializador existente, reutilizando o frontend6812/5173. GET real confirmou padrão16:9, supervisor ativo e preservação dos7 projetos/5 vídeos antigos9:16. Quando a câmera não for detectável com segurança, preservar conteúdo e mostrar aviso, sem declarar adaptação inexistente.

Verificação:94 testes e11 subtestes de formatos/câmera/API/automação/ciclo de vida/mídia passaram em39,19s; após ajuste de enquadramento perto da borda,25 testes focados passaram em8,68s. OpenCV headless4.14.0.94 instalado somente no venv, sem mudar NumPy existente; pip check aprovado. Detecção local de rosto estável, seis frames limitados, sem reconhecimento de identidade nem upload.

Execução nativa com vídeo controlado e imagem pública de teste do OpenCV: detector real + FFmpeg real geraram1920×1080/source_preserved e1080×1920/camera_top_content_bottom, ambos com áudio e legendas. ASR simulado identificado; não é VOD do usuário nem sua webcam. Imagens extraídas inspecionadas; arquivos e hashes originais preservados; trocar configuração não reprocessou os resultados. Evidência `backend/.test-data/output-formats-native/run-91d45594c1/evidence.json`; estado real em `live-evidence.json` na pasta pai.

**Para Claude:** consumir GET/PATCH `/automation` com `output_format: "16:9"|"9:16"`; acrescentar seletor global à configuração inicial (padrão16:9), badge/proporção correspondente na galeria e layout_warning quando houver. Vídeos antigos sem campos permanecem9:16/full_frame. Não alterar cada corte, não criar editor, não gerar ambas as versões e não tratar preferência nova como pedido para reprocessar acervo. A interface ainda não foi alterada pelo GPT. O relatório próprio do Claude agora confirma o percurso real da galeria anterior; a oscilação de avaliação do53749628 foi o teste controlado do GPT, já restaurado e registrado.

Limite: detector infere uma região em torno de um rosto estável, sem localizar precisamente bordas da webcam; ambiguidade/ausência usa fallback com aviso. A adaptação no VOD real do canal continua sem validação porque não havia gravação disponível. [Decisão004](../decisions/004-output-formats-and-camera.md) e [validação](../implementation/output-formats.md).

## Backend entregue: automação Twitch → galeria (2026-10-30)

Nova direção confirmada: buscar VODs automaticamente, gerar cortes completos e avaliar apenas Gostei/Não gostei. GPT escreve backend/provider/supervisor/galeria/testes, dependências locais e documentação própria; Claude mantém frontend/launcher/brief/README. Aplicada a skill Ponytail para reutilizar fila, banco e mídia existentes. Nenhum arquivo do Claude será editado.

**Contrato implementado em integration-contract.md e disponível na API8765.** GET/PATCH `/automation`, GET `/gallery`, PATCH de review existente e GET `/clips/{id}/file`. Formatos/estados/paginação/compatibilidade definidos no início do contrato. O comando do lançador `python -m ai_stream_editor.local` foi preservado.

**API atualizada e rotas disponíveis em8765.**67 testes afetados passaram (provider/automação/API/ciclo de vida), com fontes controladas e FFmpeg real (ASR simulado). Corrigida corrida que tornava sucesso de exportação visível em memória antes do desfecho do commit do histórico; sucesso publicado/warning e cancelamento tardio permanecem protegidos. Novo teste determinístico aprovado.

Descoberta externa real com yt-dlp2026.10.26 consultou joaomontagner e retornou zero VODs, sem erro. Supervisor ativo, intervalo300s, status waiting. Nenhum vídeo real baixado. Atualização final preservou os7 projetos e o frontend5173; galeria retorna5 artefatos existentes. Evidência `backend/.test-data/automation-live-20261030/final-evidence.json`.

Smoke automático com fonte controlada concluído:45s sintéticos → ASR base CPU/int8 offline real → um MP4 de45s/1080×1920/áudio/legendas; avaliação persistiu após reinício, sem novo job e com hashes preservados. Sem navegador para conduzir as etapas. Evidência `backend/.test-data/automation-live-20261030/native-c0d8265057/evidence.json`. Não equivale a download Twitch nem validação editorial. Após os últimos ajustes,34 testes finais de provider/automação passaram em7,86s; há sobreposição com os67 anteriores, não somar.

Para Claude: a proposta de frontend-status foi lida; prevalecem os nomes do contrato publicado (`GET /automation`, `review_status`, cursor inteiro, review via PATCH existente). Pode integrar agora com8765. Campos/rotas são aditivos; arquivo pronto usa `/clips/{id}/file?revision=N`, sem render/export intermediário. O comando do lançador permanece intacto. Nenhum arquivo frontend foi alterado.

Pedido sobre sinal de cortes novos atendido e carregado na API final: `Automation.gallery_updated_at` (ISO/null) muda a cada render bem-sucedido, inclusive quando outro corte do mesmo VOD falha. **Usar esse sinal em vez de depender apenas de counts.completed.** Totais por filtro ficam pendentes opcionais; não inventar total a partir da página atual.

GPT já percorreu a galeria real nova: waiting, Todos com5 cortes sintéticos anteriores, player com readyState4/21s/sem erro e reprodução efetiva, Não gostei + filtro + recarga, depois Gostei + filtro. Avaliação final restaurada à original, revisão3 e5 jobs intactos; attachment HTTP200 tem hash igual ao MP4 anterior. Evidência `backend/.test-data/automation-live-20261030/gallery-ui-evidence.json`. Não houve download Twitch nem alterações frontend; atualizar seu relatório próprio com seu percurso quando fizer.

Arquivos de produto alterados: `automation.py`/`twitch.py` novos; Service (importação com ID estável, galeria e corrida do histórico), Store (página e sinal), API/schemas/serve, pyproject e lock. Testes próprios novos: test_automation/test_twitch e regressão no ciclo de vida. Documentação: [operação/validação](../implementation/automation.md), [ADR003](../decisions/003-automatic-vods-and-gallery.md), README do backend, continuidade, fila e contrato. Sem scripts globais/novos serviços Windows; yt-dlp só no venv, pip check aprovado. Nenhum Git de escrita, upload, publicação, alteração de arquivos do Claude ou exclusão de mídia.

Bloqueios reais: VOD público disponível para validar obtenção externa e qualidade editorial; Claude consumir gallery_updated_at para sinalizar renders parciais e registrar seu próprio percurso. A integração básica da galeria já passou no GPT. Não pedir ao usuário para colar VOD por rotina: a busca automática do canal está ativa com o backend ligado.

## Lote atual: integração e avaliação do MVP concluído no escopo autorizado

2026-10-29. GPT alterou runner/testes, metadados/mensagens do Service e documentos próprios; nenhum arquivo frontend ou algoritmo de ranking foi alterado. O usuário autorizou avaliação local e indicou o canal Twitch joaomontagner. Em leitura, a lista pública de transmissões anteriores mostrou “Nenhum vídeo encontrado” e o Estúdio de Vídeo, com Todos os vídeos, mostrou nenhum resultado. Nenhum VOD foi baixado ou processado. Falta gravação local ou VOD específico disponível; não inferir por que estão ausentes. [Relatório do lote](../implementation/integration-evaluation-report.md).

- Contrato conferido e ampliado em resposta aos dois pedidos do Claude: Project agora informa `source_available`/`source_status` por metadados; resultado de análise informa `empty_reason` legível ou null. Sem novo endpoint, migração ou reanálise destrutiva. Preview aprovado continua exportável mesmo se o original sumir.
- Runner recebeu `--speech-layout continuous`, preservando sparse como padrão. Usa a mesma fala Maria sintética sem pausas adicionais, corta a última repetição no fim e registra cobertura nominal dos trechos, sem chamar isso de atividade de voz medida. Após as extensões do Service,16 testes da API e4 do runner passaram:20 testes afetados em6,71s, sem repetir a suíte inteira.
- Pequena correção no runner: dimensões abaixo do mínimo do render são recusadas antes de gastar tempo reconhecendo áudio. Nenhuma alteração de ranking ou do pipeline do produto.
- Medição real offline concluída:630s,146 segmentos,1.002 palavras, transcrição20,5316s; pico residente Windows545,238MiB e pico privado amostrado2.063,633MiB. Um candidato renderizado em360×640,46s. Mesma fala repetida: não prova acerto editorial nem tempo de VOD real. [Método e limites](../implementation/continuous-speech-validation.md).
- A interface nova do Claude foi verificada no navegador real: recentes, abrir sucesso vazio sem retry inválido, escolher outra fonte, recarregar durante reconhecimento ativo, cancelar render até canceled, editar texto/início/fim, gerar novo preview, aprovar, exportar duas vezes e conferir histórico após recarga. Saídas21s/1080×1920/áudio. Primeiro hash preservado. Registro `backend/.test-data/integration-currentlot-79fe99d7/evidence.json`.
- Warning de persistência validado por HTTP em teste controlado: succeeded, output_path e histórico permanecem acessíveis, sem expor dados internos. UI do aviso e cancelamento de exportação verificados separadamente em modo mock identificado, conservando sucesso anterior. Exportação real foi rápida demais para observar cancelamento durante a cópia; essa afirmação não foi feita.
- API atualizada graciosamente após confirmar zero jobs ativos; frontend preservado. Health pronto, projeto anterior retornou novos campos e histórico continuou com duas exportações. Evidência `backend/.test-data/integration-currentlot-79fe99d7/api-extension-live.json`; não confundir publicação dos campos com consumo pela UI.
- [Roteiro de avaliação com VOD](../implementation/vod-evaluation.md) preparado. Próximo passo depende de fonte disponível/intervalo e revisão humana, não de stack nova.

### Para o Claude neste lote

Rotas compatíveis; os dois campos opcionais pedidos foram entregues e testados. Consumir `Project.source_status`/`source_available` ao abrir/listar, com fallback se ausentes; avisar sobre original ausente/alterado sem bloquear exportação de preview atual aprovado. Consumir `result.empty_reason` como texto, sem deduzir causa adicional. Campos são aditivos; tipos/mocks e apresentação ficam com Claude. Nenhum arquivo seu foi editado pelo GPT.

O bug de retry vazio e recentes/histórico passaram no percurso do GPT. A última leitura do frontend-status já registra59 testes, typecheck/lint/build e percurso real próprios do Claude; seus limites de warning/cancelamento efetivo de exportação foram respeitados. Backend não deve reanalisar projeto concluído para contornar a UI.

## Histórico: resultado do lote anterior de confiabilidade

2026-10-29: GPT concluiu os lotes de Service/API/Store, configuração, diagnóstico, inicialização e integração. Subagentes exclusivos concluíram mídia e análise; frontend e configurações do Claude preservados. [Fila por tarefa](../implementation/backend-work-queue.md).

Suíte integrada: **95 testes e 21 subtestes aprovados**; após a proteção adicional contra leitura de banco depois da publicação, 29 testes afetados de API/ciclo de vida passaram novamente. Sem nova dependência instalada. Cancelamento queued imediato, encerramento com liberação de trava mesmo com falha de banco, temporários preexistentes preservados, erros de disco/permissão úteis, cache de correções por ID+texto original visível, preview ausente/revisão antiga, histórico e recuperação de exportações implementados.

Teste de falha SQLite após publicar mantém succeeded/output_path com warning e recupera o histórico no reinício por identidade do arquivo; um MP4 alheio com mesmo nome não é aceito. Não há gravação redundante que possa reclassificar sucesso. [ADR 002](../decisions/002-recovery-and-windows-runtime.md).

Mídia: 20 testes próprios, incluindo rotação e SAR anamórfico, sincronização flash/beep (0–10 ms na resolução medida), páginas de legenda, ASS curto, cancelamento e watchdog com avanço real. Análise: 29 testes e 10 subtestes próprios; heurística v2 evita repetição, silêncios desnecessários e pistas por substring, admite zero candidatos. Reconhecimento offline real de 630 s artificiais em 5,9666 s, pico residente Windows 407,223 MiB até transcrição e pico privado amostrado 1.954,922 MiB. A fixture tem muita pausa; não extrapolar para VOD contínuo.

Fluxo real novo em 5173: arquivo inexistente produziu erro recuperável; fixture de 630 s gerou candidato; edição de legenda e dos dois limites, preview, aprovação, exportação e recarga/reinício preservaram o estado. MP4 1080×1920 com áudio, 24,25 s; segunda exportação gerou `corte_ff1ecd58_2.mp4` sem sobrescrever a primeira. Evidência: `backend/.test-data/integration-extended-63b48748/`. Silêncio real de 10 s pelo frontend em localhost produziu mensagem de zero sugestões corretamente.

Inicializador `scripts/start-local.ps1` e diagnóstico `scripts/check-local.ps1` disponíveis. Smoke de processo real preservou Vite externo e encerrou a API após três desconexões de preview (`backend/.test-data/launcher-06aaece9/`). O travamento observado no Proactor/Python 3.12 foi tratado com SelectorEventLoop apenas na API Windows e limite de drenagem HTTP; nenhum arquivo instalado ou configuração do sistema foi alterado. API final iniciada em 8765; frontend existente mantido em 5173.

Na retomada pedida pelo usuário, a API seguia disponível e a interface havia parado. O inicializador reutilizou a API e reabriu somente o Vite, sem alterar seus arquivos. Conferência final: health com todos os recursos prontos, duas exportações no histórico, hash da primeira preservado, segundo MP4 24,25s/1080×1920/áudio, Range206/no-store e URL de revisão antiga409. Registro `backend/.test-data/integration-extended-63b48748/final-evidence.json`. Nova aba do editor confirmou corte aprovado, limites/texto corrigidos e preview disponível.

Teste isolado adicional: servidor em porta efêmera encerrou com decodificação nativa real em andamento, persistiu canceled antes de qualquer recuperação, liberou trava e não deixou descendentes. Encerramento em 0,859 s; 8765/5173 permaneceram disponíveis. Evidência `backend/.test-data/shutdown-a5c114d48f/`; [relatório](../implementation/shutdown-validation.md). O subagente atingiu o limite depois de executar o teste; GPT conferiu a evidência e fechou os documentos, sem contratar créditos.

### Pedidos atuais ao Claude

1. **Bug reproduzido, prioridade alta:** após sucesso com zero candidatos, botão “Analisar de novo” chama analyze no projeto concluído e recebe 409. Mostrou erro + “Tentar novamente” mantendo o mesmo botão. Distinguir sucesso vazio de falha: oferecer “Novo vídeo”/orientação; não repetir automaticamente nem alterar o contrato para descartar trabalho. Reproduzido com `backend/.test-data/integration-extended-63b48748/silence-10s.mp4`. Não editei frontend.
2. Exibir projetos recentes e abrir pelo ID: GET `/projects` retorna novos primeiro, com analysis_job_id/status/analyzed_at/clip_count e campos de exibição para rotação/SAR. GET `/projects/{id}/jobs` permite reconstruir jobs sem depender só de localStorage.
3. Apresentar histórico: GET `/projects/{id}/exports` e `/clips/{id}/exports`. `warning` pode acompanhar sucesso publicado com persistência pendente; mostrar aviso sem transformar o resultado em falha. Registros internos de recuperação não fazem parte da resposta.
4. Cancelamento de render/export usa a rota existente. Preservar expected_revision e os dois PATCHes. Correções na borda só voltam para a mesma variante de palavras; avisar para revisar quando elas mudam.
5. Progresso tem `progress_scope: stage`: percentual pertence à etapa atual e pode reiniciar na próxima; não é estimativa de tempo total. Zero candidatos é sucesso válido. Duração 3–180 s é política da UI, não requisito confirmado do backend. Desenvolvimento integrado suportado em 5173; preview4173 ainda não certificado.

Na leitura final do frontend-status, Claude também confirmou seu próprio percurso integrado real, além dos45 testes/typecheck/lint/build. A observação2a dele sobre legenda pequena/baixa foi atendida no render: fonte padrão63px e margem inferior288px em1080×1920 (antes52px/154px). São escolhas conservadoras de legibilidade, sem garantia de área segura universal de plataformas. Os20 testes de mídia e11 subtestes passaram após o ajuste, incluindo região dos glifos afastada da base. Amostra inspecionada: `backend/.test-data/integration-extended-63b48748/legibility-raised.png`; preview integrado também foi atualizado. Arquivos do Claude permaneceram intactos.

### Limites e próxima ação

Backend utilizável com fixtures; faltam VOD representativo autorizado e avaliação humana de transcrição/momentos/desempenho contínuo. Não houve busca por mídia pessoal. Não há limpeza automática; relatório de espaço é somente leitura. Proposta de retenção: manter previews nesta etapa; antes de implementar remoção, apresentar lista/seleção e política aprovada pelo usuário, preservando originais/exportações. Instalação limpa adicional não foi executada: lock, pip check, versões e execução foram conferidos sem reinstalar.

Remotion continua fora da stack, com redistribuição não esclarecida e divergência estrita de version no histórico; skill preservada. WSL identificado anteriormente, opcional e sem funcionamento confirmado. Nenhum serviço pago, upload, publicação ou Git de escrita.

## Marco anterior preservado

2026-10-29. GPT implementou backend/processamento/integração sob autorização do MVP. Sem ponte autenticada direta com Claude; coordenação pelos arquivos. Nenhum arquivo frontend, configuração do Claude ou skill Remotion foi editado.

## Funciona e foi executado

- Contrato v1 implementado em `http://127.0.0.1:8765/api`: projetos, análise, jobs/cancelamento, edição com revision, preview/Range e exportação aprovada sem sobrescrever.
- FastAPI + SQLite + fila única + FFmpeg + faster-whisper base CPU/int8. Pesos públicos preparados; inferência offline. Sem GPU, API paga ou envio de mídia.
- 28 testes e 10 subtestes passaram. Testes da API injetam transcrição simulada, com FFmpeg real; smoke separado comprovou o modelo real e saída 1080×1920 com áudio, 7 legendas, Range 206 e original preservado.
- Integração pelo navegador em `http://127.0.0.1:5173`, sem mock: importou fala sintética PT-BR, analisou, corrigiu legenda, ajustou início para 0,5 s, renderizou, aprovou e exportou. Interface confirmou `corte_b956b52e.mp4` na pasta de evidências `backend/.test-data/smoke/run-d0ef6ee0/`. FFprobe confirmou 25 s, 1080×1920 e áudio; API confirmou revision 3, approved e preview ready. Registro: `ui-integration-evidence.json` nessa pasta.
- Backend foi iniciado nesta sessão na porta 8765; frontend já estava ativo em 5173 por outra sessão. Nenhum servidor alheio foi encerrado.

## Pedidos ao Claude / integração

- Fluxo básico real já passou; preservar `expected_revision`, tratamento 409 e a identificação da heurística.
- Documentação frontend descreve limite de 3 s a 3 min. Backend aceita qualquer intervalo positivo dentro do vídeo: evitar apresentar o limite da interface como requisito confirmado do produto; avaliar clipes curtos e ajuste além de 3 min como decisão de UX.
- A origem suportada de desenvolvimento é 5173. `vite preview` em 4173 ainda não faz parte da lista de origens; não anunciar esse modo como integração validada.
- O status do frontend ainda não estava publicado na última leitura; seus testes e conclusão devem ser relatados por Claude. A interface e seus documentos estavam disponíveis e foram preservados.

## Limites reais / próximos passos

Heurística textual, sem entendimento visual ou LLM. Qualidade editorial, ruído/múltiplos falantes e desempenho em VODs longos ainda sem validação real. Cancelamento cooperativo pode aguardar a chamada nativa; não há retomada de job interrompido nem limpeza automática de previews. O diretório de dados padrão fica fora do OneDrive; a própria pasta do código continua no OneDrive.

Não há bloqueio técnico para repetir o fluxo com mídia sintética. Próximo passo de produto: usuário escolher/autorizar vídeo representativo para medir qualidade e desempenho. Não procurar mídia pessoal por conta própria. Licença da skill Remotion continua aberta; Remotion não é usada. WSL opcional, não validado e não necessário para a execução atual. A divergência estrita da chave version permanece no histórico do setup, sem alteração da skill.

Execução: `backend/README.md`. Arquitetura: `docs/implementation/backend.md`. Retomada: `docs/implementation/backend-continuity.md`.
