# Contrato local do MVP — v1

## Formato de saída — 2026-10-30 (implementado na API8765)

Usuário confirmou: **16:9 por padrão**, opção de mudar para **9:16 com câmera em cima e conteúdo embaixo**. Configuração inicial/global, sem edição de cada corte e sem gerar ambas as versões. Escolha vale para VODs iniciados depois da mudança; VOD ativo e artefatos antigos são preservados.

Extensão aditiva de GET/PATCH `/automation`: `output_format: "16:9"|"9:16"`, padrão16:9, inclusive ao migrar configuração anterior sem campo. O backend captura o formato no início do VOD e guarda no projeto/corte. Não reconverte o acervo ao mudar a configuração.

Clip e GalleryItem recebem `output_format`, `layout` e `layout_warning` (texto PT-BR/null). Formato16:9 mantém a imagem original inteira, sem recorte da câmera; formato9:16 tenta localizar uma região de câmera estável, por detecção local de rosto, e monta câmera acima/conteúdo abaixo. `layout`: `source_preserved|camera_top_content_bottom|full_frame`. Sem evidência suficiente de câmera, preserva o conteúdo inteiro no vertical e informa `layout_warning`; não afirma câmera adaptada. A detecção é heurística, não reconhecimento de identidade. Clips antigos sem campos continuam9:16/full_frame, preservando previews e avaliações.

Para Claude: acrescentar seleção16:9/9:16 na configuração inicial, mostrar formato/layout/aviso no card e respeitar a proporção do vídeo. Não incluir sliders, recorte manual ou controles de edição por corte. API atualizada, formato padrão16:9 e campos novos conferidos por HTTP; pode integrar. Project também informa output_format. PATCH de configuração não altera revisão/avaliação nem regenera artefatos anteriores.

## Extensão de automação e galeria — 2026-10-30

**Implementado e disponível na API8765 em 2026-10-30.**67 testes afetados passaram; consulta real da fonte concluiu com zero VODs. Fluxo automático com fonte controlada/FFmpeg real foi verificado, sem afirmar download Twitch real. Rotas v1 continuam válidas. O backend faz o encadeamento mesmo sem página aberta; requer os serviços e o computador ligados.

| Rota relativa a /api | Entrada | Saída |
| --- | --- | --- |
| GET /automation | — | Automation; somente leitura, não dispara busca/processamento |
| PATCH /automation | `{enabled?: boolean, channel_login?: string}` | Automation; configuração inicial persistente; canal é login sem URL, minúsculo, 3–25 caracteres `[a-z0-9_]` |
| GET /gallery | `review_status=all|pending|approved|rejected` (padrão all), `limit=1..50` (padrão20), `cursor` inteiro positivo opcional | `{items: GalleryItem[], next_cursor: integer|null}` |
| PATCH /clips/{id} | `{review_status: pending|approved|rejected, expected_revision?: integer}` | Clip existente; avaliar não altera revisão/mídia nem dispara job |
| GET /clips/{id}/file | `revision` inteiro positivo opcional | Mesmo MP4 já pronto, como attachment; não exige aprovação, não copia/renderiza; suporta Range, no-store |

Automation: `{enabled, channel_login, channel_url, poll_interval_seconds, runtime_active, status, message, last_checked_at, next_check_at, active_vod, counts}`. Datas UTC ISO ou null. Inicial: enabled true, canal joaomontagner, intervalo300s. `runtime_active` indica supervisor iniciado, não página aberta. `status`: `stopped|disabled|checking|waiting|downloading|analyzing|rendering|attention|configuration_required`. Message é PT-BR sem caminhos privados/tokens. `counts`: `{queued, processing, completed, failed, skipped}` para o canal atual. `active_vod`: null ou `{id, title, url, stage, project_id, job_id, progress, progress_scope}`; progresso é da etapa, ou null, nunca percentual total. Jobs existentes continuam consultáveis por ID. Source sem VOD é waiting, não falha. Dependência ausente é configuration_required; falhas de rede/acesso são attention, sem fingir canal vazio.

Extensão aditiva: `gallery_updated_at`, UTC ISO ou null, muda quando um render termina com sucesso, mesmo se outros cortes do VOD falharem. A UI pode comparar o valor e oferecer/recarregar cortes novos sem depender de `counts.completed` (que conta VODs inteiros). Não muda por avaliação nem por consultas. É um sinal de render persistido, não contador total nem garantia de que ninguém removeu arquivos depois. Totais por filtro ainda não são publicados; a galeria continua paginada sem carregar todos os registros.

Desabilitar impede novos VODs e novas buscas; o VOD já em execução termina. Alterar canal enquanto há VOD ativo retorna409. Alterar canal em repouso inicia uma descoberta inicial independente. Configuração não contém credenciais; rota pública usa apenas conteúdo acessível anonimamente. Conteúdo restrito não é contornado.

GalleryItem: `{id, project_id, title, reason, score, review_status, revision, duration_seconds, created_at, preview_url, download_url, source}`. URLs locais absolutas com revisão. `source`: `{type: local|twitch, vod_id: string|null, channel_login: string|null, url: string|null, title: string|null}`. Não inclui transcrição, caminhos privados ou tokens. Compatível com projetos locais anteriores. Só entram artefatos de revisão atual, presentes e reproduzíveis; cortes ainda gerando/falhos ficam fora. `score` continua heurístico, não probabilidade. Created_at usa data do corte quando existente, senão análise/projeto.

Galeria usa cursor opaco para a UI (inteiro de ordem persistida); mais novos primeiro. Repassar next_cursor, sem somar páginas por conta própria. A ordem não muda ao avaliar. Uma mudança de filtro reinicia o cursor. Consultas não iniciam nenhum job. Avaliações são persistidas no backend. Não gostei não apaga arquivos; Gostei não renderiza nem publica. MP4 disponível mesmo pendente/rejeitado, sem conversão.

Primeira descoberta: enfileirar somente o VOD mais recente e registrar os anteriores como skipped (não baixar o acervo inteiro). Nas próximas, enfileirar IDs inéditos observados; deduplicação persistente por canal+ID. Descoberta limitada a50 itens recentes por consulta; períodos offline maiores que essa janela podem perder VODs antigos. Antes de baixar, exigir duração igual em duas consultas e `is_live: false` nos metadados do extractor; desconhecidas/em andamento são adiadas. Essa é a evidência operacional de término usada nesta integração, não confirmação oficial da Twitch. Uma fonte indisponível não bloqueia outras. Até três tentativas por VOD, com espera de300/600s; descoberta usa espera crescente até3600s. Reinício reaproveita projeto/análise/previews concluídos, sem prometer retomada nativa ou de download parcial. Nenhuma exclusão automática de mídia.

Erros seguem v1:422 para configuração/parâmetro inválido;409 para conflito de revisão, fonte/canal ocupado ou arquivo indisponível;404 para corte inexistente. Arquivo original ausente não impede acessar um MP4 pronto. Rotas novas mantêm validação de Host/Origin e loopback.

Responsável de escrita: GPT. Atualização 2026-10-29. Backend em `http://127.0.0.1:8765/api`; frontend de desenvolvimento em `http://127.0.0.1:5173`. JSON usa snake_case, tempos em segundos, datas UTC ISO 8601. Sem autenticação externa, publicação ou upload de VOD.

## Rotas

| Método/caminho relativo a /api | Entrada | Saída |
| --- | --- | --- |
| GET /health | — | `{status, ffmpeg_available, ffprobe_available, transcription_available, model_ready}` |
| POST /projects | `{source_path}` | Project (201); caminho absoluto local, não URL |
| GET /projects | — | Project[] (recuperar trabalho após reinício) |
| GET /projects/{id} | — | Project |
| POST /projects/{id}/analyze | — | Job (202), inclui `job_id` como alias de `id` |
| GET /jobs/{id} | — | Job |
| POST /jobs/{id}/cancel | — | Job; cancelamento cooperativo |
| GET /projects/{id}/clips | — | Clip[] |
| GET /projects/{id}/jobs | — | Job[], mais recentes primeiro |
| GET /projects/{id}/exports | — | Export[], mais recentes primeiro |
| GET /clips/{id}/exports | — | Export[], mais recentes primeiro |
| PATCH /clips/{id} | campos opcionais `start_seconds, end_seconds, captions, review_status` | Clip |
| POST /clips/{id}/render | — | Job (202) |
| GET /clips/{id}/preview | header Range opcional | MP4 do preview atual (200/206); 409 se desatualizado |
| POST /clips/{id}/export | `{output_directory}` | Job (202); somente corte aprovado e preview atual |

Project: `{id, source_path, name, duration_seconds, width, height, fps, has_audio, created_at, analysis_job_id, analysis_status, analyzed_at, clip_count, rotation_degrees, display_width, display_height, source_available, source_status}`. Campos novos são extensões aditivas. `analysis_job_id` é o último job de análise (null antes da primeira tentativa); `analysis_status` é seu status ou `not_started`; `analyzed_at` é UTC ISO ou null para projetos anteriores à extensão/não analisados. `clip_count` conta os cortes persistidos. Width/height são codificados; display_width/display_height consideram rotação/SAR. Projetos antigos usam zero graus e dimensões codificadas como fallback. A listagem não carrega a transcrição na resposta nem a materializa em Python.

`source_status`: `available|missing|changed|unavailable`; `source_available` é true somente para available. Consulta apenas metadados do caminho já importado, sem FFprobe nem leitura do conteúdo: compara tamanho/modificação com o registro original. Missing indica arquivo ausente; changed indica divergência desses metadados; unavailable indica caminho/acesso não confirmável. É uma observação daquele instante, sem garantia de leitura futura nem hash integral; jobs continuam validando a fonte. Sem fingerprint legado, compara com o estado atual. Fonte ausente/alterada não deve impedir exportar um preview já aprovado e atual: exportação não precisa reler o original. UI deve tolerar ausência dos campos em backends anteriores.

Export: `{id, job_id, project_id, clip_id, revision, created_at, output_path}`. Histórico persistente das exportações bem-sucedidas realizadas após esta extensão; caminhos são registros, não promessa de que o arquivo continua no lugar. Exportações anteriores continuam visíveis nos jobs existentes, sem migração fictícia. Não há rota para ler qualquer caminho registrado.

Clip: `{id, project_id, start_seconds, end_seconds, title, reason, score, review_status, captions, preview_url, preview_status, revision}`. `review_status`: `pending|approved|rejected`. `preview_status`: `missing|stale|ready`. `preview_url` é URL local quando atual, caso contrário null. `score` é pontuação heurística de 0 a 1, não probabilidade de viralizar.

Caption: `{id, start_seconds, end_seconds, text}`, tempos relativos ao início do corte. IDs estáveis; textos não vazios; intervalos positivos dentro da duração, sem sobreposição.

Job: `{id, job_id, project_id, clip_id, kind, status, stage, progress, error, result, created_at, updated_at}`. `kind`: `analyze|render|export`; status `queued|running|succeeded|failed|canceled`; `progress`: 0–1 ou null; `error`: texto em PT-BR ou null. `result` pode conter `clip_ids`, `preview_url` ou `output_path`. Jobs interrompidos por reinício terminam como failed; o usuário pode iniciar outro. Não se promete retomada no meio do reconhecimento/render.

Extensões do Job: `progress_scope: "stage"`, `started_at`, `finished_at`, `elapsed_seconds`, inicialmente null quando ainda não há medição. O progresso mede a etapa indicada, não estima tempo total por pesos arbitrários. Pode reiniciar ao mudar etapa. Resultado de análise inclui `analysis_method: "transcript_heuristic_v2"` e `timings_seconds` reais de extraction/transcription/suggestion_and_save. `clip_ids: []` é sucesso válido. `result.empty_reason` é texto legível em PT-BR ou null: distingue transcrição sem segmentos de transcrição existente sem candidato pelas regras atuais. Não diagnostica silêncio, música ou qualidade do áudio. O mesmo texto aparece em `result.message` quando vazio; jobs anteriores podem não ter o campo. Job pode incluir `warning` em falha de persistência sem desfazer o resultado publicado.

## Edição e segurança

- Não é necessário carregar arquivos por multipart: `source_path` é digitado/colado na interface local. O original não é movido. Projeto é validado com FFprobe.
- Alterar tempos ou legendas aumenta revision, invalida preview e volta review_status para pending, a menos que a mesma edição indique outro estado explicitamente. Alterar apenas aprovação não invalida preview.
- Ao mudar limites sem enviar captions, as legendas são recalculadas da transcrição. Correções são guardadas por ID e texto original visível: voltam quando o mesmo conjunto de palavras reaparece, inclusive após sair totalmente do intervalo. Quando as palavras da borda mudam, a correção anterior não é aplicada cegamente; revisar o texto. Se enviar captions, seus tempos já devem ser relativos aos novos limites. IDs personalizados sem correspondência com a transcrição não são recuperados automaticamente ao recalcular limites.
- Render usa uma revisão fixa: uma edição concorrente não publica um preview antigo como atual. Exportação exige revisão atual e aprovação. Preview aceita `?revision=N`, rejeita revisões antigas com 409 e usa Cache-Control no-store. Arquivo ausente é anunciado como `missing`, nunca ready.
- Uma operação do mesmo tipo ainda ativa para o mesmo item retorna 409, sem devolver um job com revisão ou pasta de exportação diferentes. `PATCH` pode incluir `expected_revision` para detectar uma edição baseada em versão antiga.
- Cancelar job queued o torna canceled imediatamente, sem executar a ação. Cancelar running é cooperativo; resultados já publicados terminam como succeeded. O encerramento recusa novas operações com 503, solicita cancelamento e aguarda os trabalhos antes de liberar a trava de instância.
- Saída única em pasta local absoluta existente; nunca sobrescreve outro arquivo ou o original. Exportação não admite caminhos de rede.
- Exportação grava um intento interno antes de publicar. Se o registro final falhar depois da publicação, retorna succeeded com output_path e warning, preserva histórico em memória e reconcilia no próximo início quando o banco estiver acessível. Só confirma o arquivo por identidade (dispositivo/inode/tamanho/modificação), não apenas por nome. Intenções/snapshots internos não são expostos nas rotas de histórico. Arquivo alterado/movido ou identidade não confirmável exige conferir o destino; não é aceito como sucesso automático.
- Erros usam `{detail: string}`; validações Pydantic podem usar `{detail: [...]}`. 404 para IDs ausentes; 409 para conflito de estado; 422 para entrada inválida; 403 para origem não autorizada. O middleware de host retorna 400 com texto simples para Host não autorizado. Não há rota genérica de arquivos.
- O serviço aceita apenas hosts/origens locais documentados. Servidor deve ser iniciado em loopback e uma instância por diretório de dados. Dados de execução e modelos ficam por padrão em `%LOCALAPPDATA%/AIStreamEditor`, fora do OneDrive; configurável por variável de ambiente local, sem serviços remotos.
- Erro de espaço detectado numa operação síncrona retorna 507 com detail; jobs usam failed com mensagem de disco/permissão. Nenhuma mudança de ACL é feita para tentar continuar. Dados e modelos configurados também exigem diretórios absolutos locais.

## Estado e limites

Contrato implementado e verificado com backend e frontend reais sobre mídia sintética em 2026-10-29. Mocks do frontend devem respeitar este formato, mas não contam como integração real. A transcrição é faster-whisper CPU/int8; o modelo precisa ser preparado por download público separado, nunca enviando áudio. Detecção inicial é um baseline explicável sobre transcrição, sem LLM remoto.
