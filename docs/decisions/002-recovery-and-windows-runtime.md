# ADR 002 — Recuperação de exportação e encerramento no Windows

Data: 2026-10-29. Status: adotada sob autorização da execução prolongada. Decisões locais e reversíveis, sem instalação ou mudança de sistema.

## Problemas demonstrados

Injeção de erro SQLite após o rename deixava um MP4 publicado como failed e sem histórico. Uma gravação redundante de sucesso também podia reclassificar um resultado concluído. Falha ao salvar cancelamento impedia a limpeza no encerramento. Separadamente, a API com Python 3.12/Proactor apresentou ConnectionResetError ao recarregar vídeo e ficou presa ao encerrar.

## Decisão

- Persistir intento de exportação antes de publicar, com revisão, caminho, snapshot do job e identidade do temporário. Depois do rename/hardlink, registrar histórico+sucesso numa transação e remover o intento.
- Se esse commit falhar, manter sucesso e caminho em memória com warning, sem regravação redundante. Recuperar na inicialização somente quando a identidade do arquivo coincidir, incluindo dispositivo, inode não zero, tamanho e modificação. Um nome existente por si só não comprova publicação.
- Durante close, acionar todos os cancelamentos e liberar executor/trava em finally, mesmo com banco indisponível.
- Usar asyncio SelectorEventLoop no processo da API Windows, via configuração suportada do Uvicorn instalado, e timeout de 10 s para encerrar conexões HTTP. O fechamento da aplicação ainda aguarda seus workers cooperativos.

## Alternativas e consequências

Não é possível tornar rename e SQLite uma única transação. Fazer só um retry imediato não cobre queda do processo; apagar o MP4 após falha de banco arriscaria perder um resultado útil. O intento fornece reconciliação pequena sem broker ou banco externo.

Identidade ausente, arquivo alterado/movido ou filesystem não confirmável deixam o resultado como não confirmado, com pedido para conferir o destino. Banco permanentemente inacessível precisa voltar a funcionar. Uma queda pode deixar temporário próprio; não há limpeza automática.

Selector é uma escolha por processo; não altera políticas globais do Windows, não muda permissões nem instala runtime. A aplicação usa subprocessos FFmpeg síncronos fora do loop, sem depender de asyncio subprocess no Windows. A configuração requer o Uvicorn >=0.54 declarado e já instalado. Não foram certificados outros runtimes Python ou FFmpeg antigos.

## Verificação

Testes controlados reproduzem falha de commit, reinício, arquivo alheio, cancelamento durante publicação e erro ao persistir cancelamento. Smoke de processo real com três respostas de vídeo abortadas confirmou shutdown completo, retorno zero e Vite externo preservado em `backend/.test-data/launcher-06aaece9/evidence.json`.
