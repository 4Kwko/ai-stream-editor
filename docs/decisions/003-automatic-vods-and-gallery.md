# ADR 003 — VODs automáticos e galeria de avaliação

Status: adotada para implementação local em2026-10-30, sob a nova direção explícita do usuário. Substitui o editor manual como fluxo principal, preservando APIs/dados anteriores. GPT mantém backend; Claude mantém interface/brief/README.

O usuário configura o canal uma vez. Com os serviços ativos, o backend descobre VODs, obtém mídia, transcreve, seleciona e renderiza automaticamente. A interface apenas reproduz e registra Gostei/Não gostei; avaliação não modifica o MP4 nem treina o modelo. Publicação continua fora do escopo.

## Integração externa

A [API oficial Get Videos](https://dev.twitch.tv/docs/api/reference/#get-videos) lista metadados de vídeos publicados e requer token; não equivale a fornecer download do MP4. Seria alternativa para descoberta com configuração inicial de credenciais, mas não resolveria sozinha a obtenção.

Foi escolhido [yt-dlp](https://github.com/yt-dlp/yt-dlp), fixado em2026.10.26 no ambiente local, para descoberta e obtenção de arquivos públicos. O [extractor Twitch](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/twitch.py) implementa listagem de arquivos e resolução de mídia. É integração de terceiro sujeita a mudanças da Twitch; não é API oficial. Não lê cookies, netrc, plugins nem configurações pessoais. Sem autenticação de usuário nesta etapa; conteúdo restrito falha com orientação, sem contorno.

## Execução e persistência

Um supervisor por Service acompanha o canal; trabalhos pesados usam o executor único existente. Estado persiste no mesmo SQLite. Nenhum Redis, serviço hospedado, serviço Windows ou tarefa agendada. CLI `serve` inicia o supervisor; factories de teste não acessam rede implicitamente. O comando `python -m ai_stream_editor.local` do lançador permanece válido.

Consulta padrão300s, até50 arquivos recentes. Primeira consulta considera apenas o mais recente e registra os demais como skipped. Depois processa IDs inéditos. Deduplicação por canal+ID e projeto UUID determinístico. Antes de baixar, duração precisa ser igual em duas consultas; o extractor também precisa informar is_live false. É evidência operacional, não garantia oficial de término. Gravação em andamento/desconhecida é adiada.

Até três tentativas de um VOD, com espera crescente. Etapas concluídas são reutilizadas: não repetir análise persistida nem render atual. Não há retomada de download parcial nem decode nativo. Falha de um corte permite gerar os demais. Zero sugestões conclui o VOD. Desabilitar impede novos VODs; o já iniciado termina. A instância/trava existente evita supervisores concorrentes para o mesmo banco.

## Arquivos e recursos

Downloads usam diretório novo por tentativa, formato com vídeo/áudio até720p e remux MP4. Limite8GiB por tentativa, contando intermediários, reserva mínima2GiB; chamadas têm timeout e retries limitados. Resultado precisa existir, ter áudio e duração compatível com os metadados. Um arquivo parcial não vira projeto. Arquivos anteriores e incompletos são preservados; não há limpeza automática. Mídia, transcrição e inferência ficam locais.

Galeria pagina no SQLite, filtra avaliações e verifica presença/revisão dos arquivos sem carregar transcrições. MP4 é servido pela rota restrita existente acrescida de attachment, sem copiar/renderizar. pending/approved/rejected são reaproveitados para avaliações. Rotas anteriores continuam disponíveis por compatibilidade, sem obrigar a UI a oferecer edição.

## Limites

É necessário manter computador e backend em execução. Janela de50 itens pode perder conteúdo antigo após períodos offline extensos. Obtenção real ainda não pôde ser validada: o canal autorizado retornou zero VODs. Qualidade editorial segue sem avaliação humana em live representativa; o baseline permanece heurístico. A remoção de edição torna erros de transcrição/limites motivo para descartar um corte, conforme a direção atual.
