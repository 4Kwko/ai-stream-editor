# Implementação do backend

2026-10-29. Responsável: GPT. Implementação autorizada pelo pedido de execução autônoma do MVP local. [Execução](../../backend/README.md), [contrato](../coordination/integration-contract.md), [decisão](../decisions/001-mvp-local.md).

## Componentes

| Arquivo em backend/ai_stream_editor | Função |
| --- | --- |
| `api.py`, `schemas.py` | HTTP, validação, proteção de host/origem e preview com Range |
| `service.py` | Estados, revisões, fila única, cancelamento e publicação dos resultados |
| `store.py`, `instance.py` | SQLite transacional e trava de instância por diretório |
| `media.py` | FFprobe, extração mono 16 kHz, FFmpeg e legenda ASS |
| `analysis.py` | Preparação explícita do modelo, transcrição CPU/int8 e heurística |
| `config.py`, `__main__.py` | Configuração e inicialização em loopback |
| `diagnostics.py`, `local.py` | Diagnóstico/espaço somente leitura e inicializador que só encerra seus próprios processos |

FastAPI não espera transcrição/render dentro da requisição: devolve job e o frontend consulta estado. ThreadPoolExecutor com um worker limita concorrência de mídia/modelo; SQLite guarda projetos, transcrições, cortes e jobs em JSON. Transcrição e cortes de uma análise entram na mesma transação. Conexões são fechadas após cada acesso. Operações repetidas ainda ativas retornam 409.

Cada alteração de conteúdo incrementa revision, invalida preview e volta para revisão. Render captura uma revisão e só publica se ela continuar atual. `expected_revision` detecta gravações sobre um estado antigo. Exportação exige aprovação e preview atual; copia em blocos para arquivo temporário exclusivo e publica sem sobrescrever, depois de reconferir revisão/estado/cancelamento. O serviço não entrega caminhos arbitrários: preview consulta somente o arquivo registrado sob a pasta privada de clips.

Cancelamento queued termina sem esperar o worker e sem executar a ação. Fechamento sinaliza todos os eventos antes de aguardar o executor e libera a trava mesmo se o banco falhar ao salvar cancelamentos. Correções de legenda ficam em cache persistente por ID+texto original visível, para recuperar variantes ao voltar os limites sem aplicar texto a palavras diferentes.

Histórico e estado de sucesso da exportação entram na mesma transação. Como filesystem e SQLite não compartilham transação, um intento interno durável precede o rename/hardlink. Se a transação final falhar após publicar, o resultado permanece succeeded em memória com warning; a inicialização reconcilia o intento por identidade do arquivo (inclui inode, dispositivo, tamanho e modificação). Não há escrita redundante que possa transformar sucesso em falha. Arquivo alheio com mesmo nome não é aceito. Detalhes em [ADR 002](../decisions/002-recovery-and-windows-runtime.md).

FFmpeg roda sem shell, com protocolos file/pipe restritos. O render mantém a imagem inteira sobre fundo desfocado, adiciona legenda ASS com texto escapado e produz H.264/AAC em MP4. O original não é alterado. O áudio temporário da análise é removido ao terminar; arquivos já existentes no destino nunca são apagados para resolver colisões.

O layout trata rotação e SAR com scale/reset_sar. Legendas longas têm páginas de até duas linhas; densidade excessiva retorna erro, sem cobrir a tela inteira. Watchdog exige avanço real de timestamp; mensagens repetidas sem avanço não adiam o timeout. [Validação e limites](media-validation.md).

## Versões observadas

Python 3.12.10, FFmpeg/FFprobe 9.0.1, FastAPI 0.162.0, Uvicorn 0.54.0, Starlette 1.10.0, Pydantic 2.14.2, faster-whisper 1.2.1, CTranslate2 4.8.4, PyAV 19.0.2, pytest 9.2.0 e httpx 0.28.1. `backend/requirements.lock` registra o ambiente exato instalado; `pyproject.toml` declara as dependências diretas. Wheels vieram do registro PyPI, sem instalação global.

Pesos: `Systran/faster-whisper-base`, licença MIT indicada na ficha pública. CPU/int8, idioma pt, VAD e timestamps por palavra; blocos de áudio de cinco minutos. A preparação consulta somente pesos públicos, sem token implícito; inferência exige cache local. A licença de redistribuição da skill Remotion continua sem esclarecimento e não afeta este pipeline, que não usa Remotion.

## Evidência e limites

95 testes e 21 subtestes aprovados na suíte integrada. Após a proteção adicional contra leitura do banco depois da publicação, os 29 testes afetados de API/ciclo de vida passaram novamente. Incluem FFmpeg real, entradas inválidas/sem áudio, original alterado, revisões concorrentes, cancelamento, retomada, trava, Range 206/416, temporários preexistentes, falha de commit após publicar e liberação de recursos com banco indisponível. Testes de API injetam transcrição simulada explicitamente. Reconhecimento real, benchmark e navegação real têm evidências separadas.

A heurística v2 usa palavras/sentenças para evitar silêncios longos que atravessam segmentos nativos, exige evidência mínima e marcadores textuais e deduplica conteúdo e sobreposição. Pode produzir zero candidatos; não força silêncio para alcançar 30 s. Pode perder bons momentos sem os marcadores ou suprimir histórias de texto parecido. Não há LLM, compreensão visual ou garantia editorial. [Casos e benchmark](analysis-validation.md).

Fixture artificial de 630 s: transcrição real offline base/CPU/int8 em 5,9666 s; pico residente registrado de 407,223 MiB até a transcrição e pico privado amostrado de 1.954,922 MiB. A medição exclui FFmpeg filho e contém muito silêncio. Cancelamento nativo aquecido observado em 1,14 s após o pedido. Não extrapolar para VOD contínuo de horas.

Outra passagem pelo frontend real confirmou erro recuperável de arquivo ausente, processamento da fixture longa, edição de texto/início/fim, render 1080×1920, aprovação, exportação e persistência após recarga/reinício. Evidência em `backend/.test-data/integration-extended-63b48748/`. O inicializador real preservou Vite preexistente e encerrou API após três respostas de vídeo abortadas (`backend/.test-data/launcher-06aaece9/`). Um problema Proactor/Python 3.12 observado nesse cenário motivou SelectorEventLoop apenas na API Windows e limite de 10 s para drenagem HTTP, mantendo o fechamento da aplicação.

Não há recuperação de reconhecimento/render no meio do processamento nem limpeza automática de dados antigos. Não foi testada instalação limpa adicional: lock exato, pip check, ambientes preparados anteriormente e execução real foram conferidos sem reinstalar. Permanecem avaliação editorial e recursos em VOD real, apresentação de projetos/histórico no frontend e política de retenção aprovada pelo usuário.

Complemento: [smoke isolado de encerramento](shutdown-validation.md) confirmou cancelamento persistido durante decode nativo real, antes de recuperação, em0,859s, sem filhos e sem afetar os serviços do produto. A interface trata sucesso vazio, mas seu botão “Analisar de novo” chama uma operação concluída e recebe409; a correção foi solicitada ao Claude e não foi feita em seus arquivos.

## Referências consultadas

- [FastAPI: aplicação e documentação HTTP](https://fastapi.tiangolo.com/tutorial/first-steps/).
- [Starlette FileResponse: suporte a Range](https://starlette.dev/responses/).
- [faster-whisper: uso, CPU/int8 e modelos locais](https://github.com/SYSTRAN/faster-whisper).
- [Modelo base público: origem e licença declarada](https://huggingface.co/Systran/faster-whisper-base).
