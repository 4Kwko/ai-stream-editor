# Automação local: VOD → corte pronto

Implementada pelo GPT em2026-10-30. [Contrato](../coordination/integration-contract.md) e [decisão](../decisions/003-automatic-vods-and-gallery.md). Claude mantém galeria, configuração inicial e seus testes.

Atualização posterior confirmada pelo usuário: próximos cortes usam16:9 por padrão, com opção9:16/câmera acima/conteúdo abaixo. A escolha é capturada por VOD; vídeos anteriores são preservados. [Formatos e validação](output-formats.md). As medições históricas abaixo usaram o perfil vertical anterior.

## Uso

Preparado o ambiente/modelo, iniciar pelo lançador existente ou `scripts/start-local.ps1`. `serve` inicia um supervisor local, independente da aba aberta. Canal inicial joaomontagner, habilitado, intervalo300s. GET `/api/automation` mostra estado; PATCH da mesma rota altera enabled/channel_login sem gravar configurações globais. Não aceita segredos. Canal vazio mostra waiting; dependência ausente mostra configuration_required; falha externa mostra attention.

Na primeira consulta, só o VOD mais recente entra na fila; anteriores observados ficam skipped. Depois entram IDs novos. São necessárias duas consultas com duração estável e metadados que indiquem is_live false. Uma gravação ainda crescendo fica aguardando. Só arquivos públicos são obtidos. Não há captura ao vivo nem uso de cookies do navegador.

Desabilitar impede nova descoberta/processamento; um VOD já ativo termina. Trocar de canal durante processamento retorna409. Ao encerrar, supervisor/interações externas param e o Service cancela cooperativamente seus jobs. Ao reiniciar, IDs/projetos/etapas já concluídos são reaproveitados. Arquivos parciais não são considerados prontos nem retomados. Não há limpeza automática.

## Componentes

- `twitch.py`: comandos yt-dlp sem config/plugins/cache pessoais; IDs/URLs canônicos; timeouts, cancelamento da árvore própria, limite de bytes/espaço, validação de mídia.
- `automation.py`: supervisor, configuração e registros persistentes de VOD, deduplicação, espera/tentativas e encadeamento no executor existente.
- `Store.gallery_page`/`Service.gallery`: paginação por cursor estável, filtros e compatibilidade com projetos locais anteriores; só mídia atual presente.
- API: GET/PATCH automation, GET gallery e attachment `/clips/{id}/file`. PATCH review existente não cria trabalho nem muda conteúdo/revisão.

Um VOD por vez. Falha de um corte não invalida outros; uma tentativa posterior só renderiza os que faltam. Até três tentativas por VOD; erros definitivos não bloqueiam a fila seguinte. Fontes sem candidatos são concluídas, sem loop de reanálise. Watcher tem exclusão mútua, além da trava de instância existente do banco.

## Verificação

Conjunto afetado de automação/provider/API/ciclo de vida:67 testes aprovados em17,58s. Após três verificações adicionais de retomada, pausa concorrente e quota de processo rápido,34 testes finais de automação/provider passaram em7,86s, incluindo o sinal de cortes novos. Há sobreposição entre execuções; não somar os totais. API/ciclo de vida permaneceram sem alterações após a primeira execução aprovada.

Testes externos são controlados: canal vazio, metadados inválidos, conteúdo em andamento/de outro canal, mídia parcial, indisponibilidade e retries, deduplicação, crescimento de duração, histórico inicial, falha parcial de render, retomada após análise persistida, avaliações sem jobs, paginação com arquivo ausente, legado, concorrência e parada. Teste nativo de cancelamento do provider criou e encerrou sua própria árvore de processos; nenhuma credencial ou Twitch foi usada nesses testes.

Correção adicional demonstrada: o sucesso de exportação aparecia em memória antes de terminar o commit do histórico. Agora o estado terminal é exposto após o desfecho da transação; arquivo já publicado continua sucesso com warning se o banco falhar. Teste com barreira determinística cobre a corrida; os testes de sucesso publicado/recuperação/cancelamento tardio passaram.

## Execução nativa isolada

Evidência ignorada pelo Git: `backend/.test-data/automation-live-20261030/native-c0d8265057/evidence.json`.

Fonte controlada retornou uma amostra sintética local de45s, sem rede nem navegador. Supervisor fez duas descobertas, obteve uma fonte e executou análise/render automaticamente. ASR base CPU/int8 real offline; FFmpeg real. Transporte de API: ASGI TestClient, não navegador/TCP. Resultado: um MP4 de45s,1080×1920,8fps, áudio e legendas; Gostei persistiu após reabrir e não criou novos jobs. Hash do original sintético e do MP4 preservados.

Tempo observado do pipeline15,64s; análise8,984s (extração0,125s, transcrição8,844s, seleção/gravação0,015s), render5,078s. Testes de unidade rodavam em paralelo; não é benchmark controlado nem previsão para lives reais. Memória não foi medida nesta execução.

## Twitch e implantação local

Consulta pública real via provider retornou zero VODs para o canal autorizado. API atualizada com supervisor ativo, status waiting e intervalo300s. Reutilizou7 projetos e tornou5 artefatos anteriores visíveis na galeria; frontend5173 preservado. Evidência `backend/.test-data/automation-live-20261030/evidence.json`. Nenhum VOD real baixado/processado: a obtenção externa, qualidade editorial e desempenho em lives continuam pendentes de conteúdo disponível.

Atualização final carregou os limites/sinal mais recentes, manteve7 projetos/5 artefatos e supervisor waiting. Evidência `final-evidence.json` na mesma pasta. Esse reinício não refez consulta fora da cadência já persistida nem iniciou processamento pela leitura da galeria.

O roteiro de teste nativo fica em `.test-data/automation-live-20261030/native-smoke.py`; usa somente a fixture sintética já existente e pasta nova por execução. Não substituir o caminho por um vídeo pessoal sem autorização. Dependências reproduzíveis estão no lock; yt-dlp foi instalado apenas no venv e pip check passou.

## Galeria real do Claude

GPT percorreu a interface nova em5173, sem mock: estado waiting do canal real, filtro Todos com5 cortes sintéticos anteriores, abertura de player e reprodução efetiva (readyState4,21s, sem erro), Não gostei, filtro correspondente, recarga preservando escolha, depois Gostei e filtro. Avaliação final restaurada à original. Nenhum controle de edição apareceu nesse percurso.

Conferência TCP posterior: MP4 attachment200 com hash igual ao arquivo anterior; revisão3 e5 jobs do projeto preservados. Não houve renderização/exportação adicional. Evidência `backend/.test-data/automation-live-20261030/gallery-ui-evidence.json`. A chegada de um VOD real e seu download continuam não verificados.

`Automation.gallery_updated_at` sinaliza renders concluídos por data UTC, inclusive se o VOD terminar com falha parcial. A UI deve usá-lo em vez de depender apenas do total de VODs concluídos. Não muda por avaliação ou consulta. Totais globais por filtro não foram acrescentados: a página mostra seus itens, não deve inventar um total.
