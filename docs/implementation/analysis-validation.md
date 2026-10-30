# Validação local da análise — 2026-10-29

Escopo deste lote: `backend/ai_stream_editor/analysis.py`, `backend/tests/test_analysis.py`, `backend/tests/benchmark_analysis.py` e este relatório. Frentes E1–E5 e D1–D3, com uma medição adicional de cancelamento nativo. Não houve instalação, download, API remota, upload de mídia, alteração global ou operação Git de escrita.

## Resultado

A análise offline com `base`, CPU e int8 processou uma fixture artificial PT-BR de **630 segundos**, gerou legendas e uma sugestão de **25,2 segundos**, renderizada em MP4 9:16. Silêncio real de 30 segundos retornou zero segmentos e zero sugestões. O ranking continua sendo uma heurística textual; não mede probabilidade de viralização, não analisa ações visuais e pode deixar de encontrar momentos úteis sem os marcadores considerados.

**29 testes e 10 subtestes passaram** na suíte de análise. Os testes de reconhecimento unitários usam runtime simulado e são identificados como tal no arquivo. A execução real descrita abaixo usa o modelo local e FFmpeg instalados; nenhum resultado simulado foi apresentado como reconhecimento real.

## Casos determinísticos e correções demonstradas

| Caso sintético | Antes deste lote | Resultado verificado após a correção |
| --- | --- | --- |
| Conversa comum, sem evento | Produzia 6 cortes | Nenhum candidato; não preenche cota |
| Reação idêntica repetida continuamente | Produzia 6 cortes | Nenhum candidato para repetição isolada |
| Palavra `bezerro` em conversa comum | Acionava a pista `erro` | Só palavras/expressões completas acionam pistas |
| `Incrível!` durante 0,4 s | Produzia candidato | Evidência insuficiente; nenhum candidato |
| Reação de 6 s entre longos silêncios | Arrastava o corte para 60 s | Mantém fala e margem curta; menos de 20 s |
| Mesmo momento em tempos distantes | Produzia 2 sugestões | Uma sugestão por conteúdo praticamente idêntico |
| Explicação com abertura, desenvolvimento e conclusão | Já preservava o exemplo | Preserva os três estágios e explica os sinais textuais |
| Três reações diferentes, incluindo as bordas do vídeo | Já preservava o exemplo | Três momentos, dentro dos limites reais |
| Contexto transcrito atravessando 300 s | Já preservava o exemplo | Contexto antes e depois da fronteira, tempos globais |
| Justificativa e score | Sem garantia estatística | Texto declara heurística e pontuação sem interpretação probabilística |
| Segmento nativo atravessando silêncio, com palavras temporizadas | Detectado na execução real: 5 candidatos, incluindo 60 s de duração | Ranking usa sentenças e pausas das palavras; não trata todo o intervalo nativo como fala |
| Repetição parcial de um momento completo | Detectada na execução real | Deduplica subconjuntos textuais muito semelhantes |
| Introdução curta antes da reação | Melhor pontuação podia começar no meio da sequência | Preserva a sequência contínua anterior, dentro da duração máxima |

O gate mínimo exige quatro palavras distintas e pelo menos dois segundos de fala temporalmente sustentada. Descarta repetição excessiva. Qualifica expressões de reação/descoberta ou uma sequência com marcadores de explicação e conclusão; estas regras são reversíveis e não constituem compreensão semântica. O intervalo preferido de 30–60 s não força silêncio para alcançar 30 s: uma fala útil isolada pode gerar corte mais curto.

A supressão combina sobreposição temporal maior que metade do menor corte e semelhança de sequências de três palavras. Esta última também elimina um trecho quase inteiramente contido no texto de outro. Pode suprimir histórias distintas que reutilizem quase o mesmo texto; não é identificação semântica.

As mudanças de contexto afetam os limites sugeridos, mas **não alteram o contrato nem a formação dos IDs/grupos de legenda**. `captions_for_window` continua recortando palavras visíveis e tempos relativos; a persistência das correções pertence à camada de serviço.

## Execução real reproduzível

Comando executado a partir de `backend/`, sem instalar ou preparar modelo:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONUTF8='1'
& '.\.venv\Scripts\python.exe' tests/benchmark_analysis.py --run-real --model-dir 'C:\Users\jvmon\AppData\Local\AIStreamEditor\models' --model base
```

O script só usa a fala Maria já sintetizada em `backend/.test-data/smoke/speech.wav`. Gera novos diretórios com identificador único e não sobrescreve os anteriores. Define offline e desativa telemetria apenas no próprio processo. Recusa modelo ausente; não inicia download. A variável `LOCALAPPDATA` do shell restrito estava redirecionada para um diretório de pacote. Por isso o caminho real do modelo foi passado explicitamente; o redirecionamento não foi tratado como perda do modelo nem motivou alteração de segurança.

Evidência final: `backend/.test-data/analysis-validation/run-62809db563/evidence.json`. A transcrição completa está em `transcript.synthetic.json`, e a prévia em `diagnostic-preview.mp4`, no mesmo diretório. As mídias e resultados ficam fora do versionamento. A primeira execução, `run-318086e2e9`, registra o problema dos segmentos que atravessavam silêncio; `run-8b7cd0b063` registra a melhoria intermediária antes do ajuste de contexto.

### Fixture e ambiente

- Windows 11, Python 3.12.10; CPU Intel64 Family 6 Model 151, 20 processadores lógicos; reconhecimento limitado a quatro threads. GPU não usada.
- `faster-whisper` 1.2.1, `ctranslate2` 4.8.4, `numpy` 2.5.4; FFmpeg/FFprobe 9.0.1 já presentes.
- Vídeo `testsrc2`, 320×180, 8 fps, H.264/AAC; duração confirmada de 630 s. Fala PT-BR de aproximadamente 21,41 s repetida sete vezes, iniciando em 4, 94, 184, 294, 404, 494 e 594 s, intercalada com silêncio. Dois eventos atravessam as fronteiras de 300 e 600 s.
- WAV extraído: PCM16 mono, 16 kHz, 20.160.078 bytes. Vídeo de entrada: 11.152.077 bytes. Diretório final: aproximadamente 54,3 MB, incluindo a fonte WAV artificial, áudio extraído, vídeo, transcrição e prévia.
- A fonte sintética original foi preservada por SHA-256: `9ab7be95c9b51de103db17efd91fb85edf925e6b276f749a84107da2b729d6b5`.

### Tempos e memória observados

| Etapa | Tempo de parede | Pico residente amostrado do processo Python |
| --- | ---: | ---: |
| Gerar fixture completa | 1,0011 s | 27,934 MiB |
| Extrair áudio | 0,2916 s | 27,402 MiB |
| Transcrever 630 s, carga inicial de `base` incluída | 5,9666 s | 388,906 MiB |
| Sugerir cortes | 0,0025 s | 228,605 MiB |
| Renderizar apenas o candidato | 0,5646 s | 229,883 MiB |
| Testar cancelamento com modelo aquecido | 1,1909 s | 394,547 MiB |
| Transcrever 30 s de silêncio, modelo aquecido | 0,0453 s | 231,191 MiB |

A amostragem de 50 ms pode perder picos breves. O contador de pico residente do Windows, para toda a vida do processo, registrou **407,223 MiB até o fim da transcrição** e **410,242 MiB até o fim do cancelamento**. Memória privada comprometida foi maior: pico amostrado de **1.954,922 MiB na transcrição**, encerrando essa etapa em **1.792,563 MiB**; pico de **1.974,590 MiB durante o cancelamento**. Memória residente e memória privada são métricas distintas; os números residentes não representam todo o comprometimento de memória.

As medidas abrangem o processo Python e bibliotecas nativas carregadas, **excluindo os processos filhos FFmpeg/FFprobe**. O tempo de CPU registrado também exclui os filhos. Portanto não há medição do pico total do conjunto de processos na extração/render. O script registra a ausência de métricas se a consulta do Windows não estiver disponível.

Por inspeção e teste unitário, cada chamada ao reconhecedor recebe no máximo 300 s de waveform mono float32: 4.800.000 amostras, ou 19,2 MB de dados da array. A leitura do PCM é feita em blocos; nenhum vídeo inteiro é decodificado em uma array Python. O teste simulado comprova tamanhos, offsets globais e último bloco parcial. Isso não fixa o pico do runtime nativo: modelo, buffers nativos e a transcrição acumulada também ocupam memória. O áudio completo continua existindo em disco. Ainda não foi medido um VOD de várias horas nem feita comparação controlada de crescimento de memória entre durações.

### Resultado e limites

O reconhecimento real produziu 29 segmentos e 238 palavras. Progresso monotônico, final 1,0. Houve diferenças de pontuação e segmentação perto das fronteiras — por exemplo, uma frase foi dividida entre `um...` e `momento interessante`. As janelas de 300 s não compartilham estado acústico; contexto na fronteira continua sendo uma limitação do reconhecimento.

Das sete repetições artificiais, restou uma sugestão em **181,97–207,17 s**, com introdução, reação e fechamento. Score **0,927**, explicitamente heurístico. A renderização selecionada tinha 25,2 s; FFprobe confirmou MP4 com áudio, 360×640 e 25,25 s, compatível com a quantização de quadros a 8 fps. Não foi renderizado o VOD inteiro nem feita inspeção editorial humana dessa prévia.

No cancelamento, a solicitação ocorreu após 0,0502 s e a função retornou `Processamento cancelado.` **1,14 s depois**. É um único teste com modelo aquecido, nesta fixture e máquina. A checagem é cooperativa entre retornos do gerador nativo e blocos; não interrompe imediatamente uma operação nativa. O teste unitário também verifica que um cancelamento entre blocos impede a próxima chamada ao reconhecedor. Este teste direto não substitui a validação de fila, API, exportação e encerramento da aplicação.

Trinta segundos de PCM realmente silencioso foram processados pelo mesmo modelo e produziram **zero segmentos e zero candidatos**.

A fixture tem aproximadamente 150 s de fala repetida e muito silêncio, baixa resolução e 8 fps. Os tempos são evidência funcional local, **sem previsão confiável para live contínua de horas, qualidade de transcrição PT-BR em jogo, ruído, múltiplas vozes ou acerto editorial**. Essa avaliação demanda VOD autorizado e revisão humana posterior. Não foram usados vídeos pessoais para contornar essa pendência.

## Testes e ambiente restrito

Comando unitário final, a partir de `backend/`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONUTF8='1'
& '.\.venv\Scripts\python.exe' -c "import pathlib,tempfile,pytest; p=pathlib.Path('.cache/analysis-tests').resolve(); p.mkdir(parents=True,exist_ok=True); tempfile.tempdir=str(p); raise SystemExit(pytest.main(['tests/test_analysis.py','-q']))"
```

Resultado: **29 passed, 10 subtests passed**, em 0,33 s. Inclui validação de números não finitos, limites, agrupamento/retiming das legendas, deduplicação determinística, modelo ausente sem rede, escolha restrita de modelo, normalização temporal, blocos de memória limitados, progresso após timestamp nativo acima do fim do bloco, WAV truncado e cancelamento entre blocos.

O primeiro uso de diretório temporário padrão falhou por permissão no caminho redirecionado do ambiente restrito. A mesma suíte passou com temporários locais do projeto, sem afrouxar controles. A consulta ampla de processos por CIM não estava disponível; isso não impediu o benchmark nem motivou encerrar processos. Nenhuma elevação foi necessária para os resultados finais acima.
