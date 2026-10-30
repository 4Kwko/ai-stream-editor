# Backend local

API Python com automação de VODs públicos da Twitch até cortes16:9 ou9:16 prontos para uma galeria de Gostei/Não gostei. A análise usa regras sobre a transcrição: não é entendimento semântico nem previsão de viralização. As rotas do editor anterior continuam disponíveis por compatibilidade; não são o fluxo principal atual.

Atualização de formato:16:9 é o padrão dos próximos cortes. GET/PATCH `/api/automation` permite mudar output_format para9:16, com tentativa local de câmera acima/conteúdo abaixo. Sem detecção confiável, preserva o conteúdo inteiro e informa aviso. Preferência não reconverte vídeos antigos. [Operação e validação dos formatos](../docs/implementation/output-formats.md). Claude mantém o seletor visual na configuração inicial.

## Automação — 2026-10-30

Ao iniciar o backend pelo comando existente, o supervisor consulta joaomontagner a cada300s, sem depender da página aberta. Descoberta/obtenção via yt-dlp local; transcrição/render locais. Primeiro considera só o VOD mais recente, espera evidência de término e não baixa todo o histórico. Precisa de PC/serviços ativos. Configuração persistente via GET/PATCH `/api/automation`, galeria paginada via GET `/api/gallery`. Avaliar não gera novo vídeo; `/api/clips/{id}/file` entrega o MP4 já pronto. [Operação, testes e limites](../docs/implementation/automation.md).

O canal retornou zero VODs na consulta real. A cadeia automática passou com fonte sintética controlada e ASR/FFmpeg reais; isso não comprova download Twitch nem qualidade editorial de lives. Dependência nova fixada no lock: yt-dlp2026.10.26, apenas no venv. Sem cookies/credenciais de navegador, serviços pagos, upload ou limpeza automática.

## Executar no Windows

Requer Python 3.12 e FFmpeg/FFprobe com libx264 e filtro subtitles/libass no PATH. Não requer GPU. Na raiz do projeto:

```powershell
.\scripts\setup-backend.ps1
.\scripts\start-backend.ps1 -PrepareModel
```

O setup instala dependências apenas em `backend/.venv`. `-PrepareModel` baixa os pesos públicos do modelo multilíngue base de Systran/faster-whisper; não envia áudio. Nesta máquina o ambiente e o modelo já foram preparados. Para iniciar de novo basta:

```powershell
.\scripts\start-backend.ps1
```

API: http://127.0.0.1:8765/api/health; documentação interativa: http://127.0.0.1:8765/docs. Uma instância por pasta de dados. Encerre com Ctrl+C no terminal que iniciou o servidor. Nenhum modelo é baixado automaticamente durante a análise: a inferência usa somente arquivos locais.

Em outro terminal, use `npm run dev` dentro de `frontend/`, conforme seu README, e abra http://127.0.0.1:5173. A experiência atual é a galeria de vídeos prontos; não há ajustes manuais entre etapas. Não use `?mock=1` para testar processamento real. A documentação/testes históricos abaixo descrevem também o editor anterior, mantido somente nas APIs.

Alternativa em um terminal, depois de preparar ambos os ambientes:

```powershell
.\scripts\start-local.ps1
```

O inicializador reconhece os serviços existentes nas portas 8765/5173 e só inicia os que faltarem. Recusa porta ocupada por serviço desconhecido ou inacessível, sem instalar nada. Ctrl+C encerra apenas seus processos; serviços preexistentes continuam ativos. `-CheckOnly` confere sem iniciar. O encerramento aguarda até 30 s por processo e informa se ele ainda está terminando, sem forçar a parada. No Windows, a API usa SelectorEventLoop no próprio processo e até 10 s para terminar conexões HTTP antes do fechamento da aplicação; não há mudança de configuração do sistema.

## Dados e configuração

Por padrão banco SQLite, transcrições, previews e modelos ficam em `%LOCALAPPDATA%/AIStreamEditor`, fora do OneDrive. Os originais permanecem no local escolhido e as exportações ficam na pasta informada. São dados locais persistentes, sem limpeza automática; previews antigos podem consumir espaço. Não há criptografia própria nem exclusão pela interface nesta versão.

Variáveis opcionais, definidas no terminal antes de iniciar:

| Variável | Padrão |
| --- | --- |
| `AI_STREAM_DATA_DIR` | `%LOCALAPPDATA%/AIStreamEditor` |
| `AI_STREAM_MODEL_DIR` | `<data_dir>/models` |
| `AI_STREAM_MODEL` | `base` (`tiny` e `small` também podem ser preparados) |
| `AI_STREAM_FFMPEG` / `AI_STREAM_FFPROBE` | executáveis no PATH |

Ao mudar o modelo, prepare seus pesos antes de analisar. A troca de modelo/diretório é uma decisão explícita. Não mude o diretório para uma pasta compartilhada em rede. A API não tem autenticação de múltiplos usuários: deve permanecer em loopback, para uso pessoal. Processos locais autorizados pelo sistema podem acessá-la. Host e Origin são restringidos a localhost/127.0.0.1 nas portas documentadas; a interface de desenvolvimento suportada usa 5173.

Dados/modelos exigem caminhos absolutos locais; UNC, dispositivos e unidades de rede mapeadas são rejeitados. O layout requer o filtro `scale` com `reset_sar`, verificado no FFmpeg 9.0.1 utilizado. A opção preserva a proporção de vídeos anamórficos além da orientação de vídeos rotacionados.

## Diagnóstico e espaço, sem alterar dados

```powershell
.\scripts\check-local.ps1
.\scripts\check-local.ps1 -StorageOnly
```

O diagnóstico consulta versões, filtros/encoder do FFmpeg, arquivos do modelo, diretório de dados e a API em loopback. `-NoApi` evita até a consulta HTTP. Não cria banco, não baixa modelo e não instala ferramentas. A indicação de permissão usa consulta do sistema, sem gravar um arquivo para testar; não garante que uma gravação futura funcionará. O relatório de espaço não segue symlinks/junctions, não apaga nada e só conta a pasta de dados configurada. Exportações e fixtures em outras pastas não entram nesse total.

Projetos recentes trazem o último job de análise, estado e número de cortes. Novas rotas de jobs e histórico de exportações permitem recuperar trabalho sem depender apenas do navegador. A tela de projetos recentes e a apresentação desse histórico dependem do Claude; as rotas já funcionam.

## Testes

Na raiz:

```powershell
.\scripts\test-backend.ps1
```

Verificação integrada de 2026-10-29: **95 testes e 21 subtestes passaram**. Depois da proteção adicional de leitura do banco após publicação, os 29 testes afetados da API/ciclo de vida passaram novamente. Os testes de API injetam transcrição simulada identificada e usam FFmpeg real; os de análise verificam heurística, intervalos, blocos de áudio e chamadas do runtime simulado. Não substituem as execuções reais abaixo.

Após o ajuste final de legibilidade, os20 testes de mídia e11 subtestes passaram novamente. Fonte padrão63px e margem inferior288px em1080×1920 deixam a legenda maior e mais alta; não garantem ausência de sobreposição pela interface de toda plataforma. Previews antigos são preservados; use Atualizar preview para aplicar o perfil novo.

`tests/smoke_local.py` executa transcrição real offline, API, FFmpeg, correção de legenda, preview com Range, aprovação e exportação 1080×1920. Requer um WAV de fala local explicitamente autorizado; não gera nem busca mídia do usuário:

```powershell
cd backend
.\.venv\Scripts\python.exe -m tests.smoke_local --speech CAMINHO_ABSOLUTO_DO_WAV --model-dir "$env:LOCALAPPDATA\AIStreamEditor\models"
```

Foi executado com fala sintética PT-BR criada localmente: modelo base, 7 legendas, 1 corte, MP4 1080×1920 com áudio, Range 206 e hash do original preservado. Evidência local ignorada pelo Git: `.test-data/smoke/run-d0ef6ee0/evidence.json`. Depois, o mesmo vídeo passou pela interface real em 5173, com correção de texto e início em 0,5 s; exportou `corte_b956b52e.mp4` na mesma pasta de evidências. Nenhum vídeo pessoal foi usado.

Na execução prolongada, uma fixture artificial de 630 s, com sete repetições da fala e longos silêncios, foi transcrita offline em 5,9666 s; gerou um candidato de 25,2 s. Pico residente do Windows até a transcrição: 407,223 MiB; pico de memória privada comprometida amostrada: 1.954,922 MiB. A memória privada é maior que a residente; não interpretar o teste como consumo de apenas 400 MB. FFmpeg filho não entra nessa medição. [Método, números e limitações](../docs/implementation/analysis-validation.md).

Outra passagem pelo navegador usou essa mídia longa com imagem variável: erro recuperável de arquivo inexistente, importação válida, análise, correção de legenda e dos dois limites, preview, aprovação, exportação e recarga preservando o estado. Saída: `.test-data/integration-extended-63b48748/corte_ff1ecd58.mp4`, 24,25 s a 1080×1920 com áudio; frame de legenda inspecionado. A matriz real de mídia cobriu sete entradas e vídeos anamórficos, com sincronização flash/beep de 0–10 ms na resolução de medição. [Relatório de mídia](../docs/implementation/media-validation.md).

O inicializador também passou por processo real, reutilizando Vite e encerrando a API após três conexões de vídeo abortadas: `.test-data/launcher-06aaece9/evidence.json`. Não apareceu ConnectionResetError nessa verificação. O encerramento anterior com Proactor havia travado; a API antiga desta sessão, já sem processamento filho, foi encerrada para aplicar a correção.

Teste separado, em porta efêmera e banco exclusivos, enviou CTRL_BREAK durante um `next()` do reconhecedor nativo real. Encerramento em0,859s; job canceled já estava persistido antes de reabrir a aplicação, sem cortes/transcrição parciais e sem filhos restantes. A trava foi readquirida e8765/5173 permaneceram disponíveis. [Relatório completo](../docs/implementation/shutdown-validation.md). O estado de sucesso vazio também passou pela interface; o botão de retry nesse estado ainda produz409 e precisa de ajuste do Claude, registrado no backend-status.

## Consistência e recuperação

- Cancelamento na fila termina imediatamente; cancelamento em execução é cooperativo. Alteração de conteúdo invalida preview e exige nova revisão.
- Correções são guardadas por ID e texto original visível. Se o corte esconder toda uma legenda e depois restaurá-la, a correção volta. Se a borda mudar o conjunto de palavras, a variante antiga não é reaplicada cegamente; revisar o texto.
- Preview ausente aparece como missing. URLs de revisões antigas são rejeitadas; respostas usam no-store.
- Exportações mantêm histórico com revisão, data e caminho. Antes de publicar, a aplicação grava um registro interno de recuperação com identidade do arquivo temporário. Falha de banco após publicar preserva o sucesso em memória, com warning, e recupera o histórico no próximo início quando o banco voltar a funcionar.
- A recuperação exige a identidade do arquivo publicado (dispositivo, inode, tamanho e modificação). Se o arquivo foi movido/alterado ou o sistema de arquivos não oferece identidade confirmável, informa exportação não confirmada e pede conferir o destino; não aceita um MP4 alheio só por ter o mesmo nome. Não sobrescreve nem apaga esse arquivo.
- Uma falha abrupta pode deixar um temporário gerado no destino. Não há limpeza automática de exportações ou previews antigos; avaliar retenção com o usuário. Falha definitiva do próprio banco exige restaurar seu acesso antes de recuperar registros.

## Falhas e limites

- Modelo ausente: prepare os pesos; a análise apresenta erro e permite tentar novamente.
- Vídeo sem áudio ou inválido: rejeitado. Original modificado após importação: importe novamente.
- Cancelamento é cooperativo; uma chamada nativa de reconhecimento pode terminar antes de responder ao pedido. Jobs interrompidos por reinício ficam como falha, sem retomada interna.
- O áudio temporário ocupa disco durante a análise. O reconhecimento lê blocos de cinco minutos para limitar a memória do waveform; transcrição e índices ainda crescem com a duração. Cortes de bloco podem perder contexto de fala.
- CPU/int8 foi validado também com 630 s artificiais de muita pausa; tempo e qualidade em VODs contínuos de horas não foram medidos. Ruído, música, múltiplos falantes e gírias podem reduzir a precisão. Cancelamento nativo observado com modelo aquecido: 1,14 s após o pedido, sem garantia para outros conteúdos.
- A heurística v2 exige evidência textual mínima e pode produzir zero candidatos; não preenche cota com conversa comum/repetição. Isso também pode perder momentos úteis sem os marcadores contemplados. Não é entendimento semântico.
- Layout fixo: original inteiro sobre fundo desfocado, legenda embutida e saída 1080×1920. Não há detecção de câmera, cortes internos, tradução ou publicação.

Contrato completo em [integration-contract.md](../docs/coordination/integration-contract.md), arquitetura em [backend.md](../docs/implementation/backend.md).

## Avaliação e medição complementar

Antes de declarar acerto editorial, siga o [roteiro de avaliação com VOD autorizado](../docs/implementation/vod-evaluation.md). Nenhum arquivo pessoal deve ser procurado automaticamente. A revisão separa erros de transcrição, contexto, limites e momentos não encontrados; resultados privados ficam fora dos documentos versionáveis.

O runner existente agora aceita fala sintética sem pausas adicionais entre as cópias:

```powershell
cd backend
.\.venv\Scripts\python.exe tests\benchmark_analysis.py --run-real --speech-layout continuous --duration 630 --model-dir "$env:LOCALAPPDATA\AIStreamEditor\models" --model base
```

Sparse permanece padrão. Modelo ausente é erro, sem download automático. A execução contínua observada levou20,5316s na transcrição, com pico privado amostrado2.063,633MiB; é repetição artificial, sem prever tempo/qualidade em live real. [Medição e limites](../docs/implementation/continuous-speech-validation.md).

No lote de integração,15 testes afetados passaram e a interface nova foi percorrida sem mock para recentes, sucesso vazio, retomada, cancelamento de render, edição, duas exportações e histórico. [Relatório do lote](../docs/implementation/integration-evaluation-report.md). O backend não precisou de endpoints novos nem alteração de ranking para atender a UI.
