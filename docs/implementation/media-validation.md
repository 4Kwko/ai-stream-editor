# Validação de mídia local

## Complemento final de legibilidade pelo GPT

Após reler a observação do Claude sobre texto pequeno e baixo, o padrão do render passou de2,7% para3,3% da altura na fonte e de8% para15% na margem inferior. Em1080×1920:63px de fonte e288px de margem, com contorno preto e paginação de até duas linhas preservados. Esses valores são uma escolha reversível do produto, sem certificação das áreas ocupadas pela interface de cada plataforma.

Os20 testes de mídia e11 subtestes passaram em10,44s após esse ajuste. A comparação de pixels em fundo não uniforme exige que os glifos mantenham folga da base; a sincronização e proporção permaneceram aprovadas. Amostra de1s em `backend/.test-data/integration-extended-63b48748/legibility-raised.mp4` e PNG correspondente foi inspecionada: duas linhas maiores, legíveis e acima da posição anterior. O preview do corte integrado também foi regenerado. As exportações anteriores foram preservadas; alterações de perfil no código exigem regenerar manualmente previews antigos.

As seções seguintes preservam as medições e amostras dos lotes anteriores, com seus próprios parâmetros.

Data: 2026-10-29. Escopo: B4/B5, C1/C2 e parte de C3 da execução prolongada. Somente mídia sintética local; nenhum VOD do usuário, download, serviço externo ou instalação.

## Resultado verificado

19 testes passaram, sem falhas nem skips, no Windows 11 com Python 3.12.10 e FFmpeg/FFprobe 9.0.1. A suíte levou 10,801 s no runner; o tempo registrado pelo benchmark, incluindo preparação da suíte, foi 11,3452 s. A geração da amostra visual ocorre depois dessa medição.

Relatório reproduzível desta execução: `outputs/media-validation/20261029T203309578761Z/report.json`. Os artefatos ficam na pasta ignorada `outputs/`; não são dados versionáveis. Após o benchmark, o mesmo teste de falhas de entrada foi ampliado para um arquivo sintético removido e passou separadamente em 0,154 s.

Arquivos de escrita: `backend/ai_stream_editor/media.py`, `backend/tests/test_media.py`, `backend/tests/benchmark_media.py` e este documento. A API pública das operações de mídia foi preservada. O Graft foi consultado antes das alterações, incluindo os consumidores no serviço, no smoke e nos testes.

## Matriz real FFmpeg

Entradas de 1,2 s a 20 fps; cada saída tem 0,9 s, 180 × 320, H.264, com AAC quando há áudio. Nomes de entrada, saída e extração incluem espaços, acentos e cedilha. Tempos são observações desta máquina, sem extrapolação para VODs ou render 1080p.

| Caso | Entrada codificada | Canais na saída | Render observado |
| --- | --- | --- | --- |
| Horizontal | 320 × 180 | 1 | 0,2987 s |
| Vertical | 180 × 320 | 2 | 0,2716 s |
| Quadrado | 200 × 200 | 1 | 0,2691 s |
| Sem áudio | 320 × 180 | 0 | 0,2374 s |
| Resolução pequena | 160 × 90 | 2 | 0,2617 s |
| Rotação 90° | 320 × 180, exibição 180 × 320 | 1 | 0,2893 s |
| Rotação 270° | 320 × 180, exibição 180 × 320 | 2 | 0,2597 s |

Verificações automáticas: dimensões, duração, canais, hash da origem e ausência de sobrescrita. As rotações foram gravadas como display matrix e comparadas com frames da origem autorrotacionada pelo FFmpeg. A extração de entradas com áudio produziu PCM WAV mono de 16 kHz; a entrada sem áudio retornou erro compreensível na extração e renderizou normalmente sem faixa de áudio.

`probe_video()` mantém `width`/`height` codificados e agora também informa `rotation_degrees`, `display_width` e `display_height`. Isso evita apresentar como horizontal uma entrada codificada horizontalmente cuja exibição é vertical. Os novos campos são aditivos; exposição desses campos na API do produto depende do serviço.

## Sincronização depois de mover o início

Fixture de 3 s: flash branco e tom de 1 kHz começam em 1 s e terminam em 1,15 s. Cortes de 2 s foram gerados com início em 0,4 s e 0,9 s. A legenda acompanha o sinal com tempos relativos ao corte.

| Início do corte | Sinal esperado na saída | Flash medido | Áudio medido | Diferença A/V |
| --- | --- | --- | --- | --- |
| 0,4 s | 0,6 s | 0,6 s | 0,6 s | 0 s |
| 0,9 s | 0,1 s | 0,1 s | 0,09 s | 0,01 s |

Medição visual em passos de 50 ms, áudio em blocos de 10 ms e limiar de amplitude; a compressão AAC pode antecipar energia pequena. Esses números não demonstram precisão submilissegundo. A comparação de pixels entre versões com/sem legenda confirmou ausência antes, presença durante e ausência após o intervalo de cada legenda.

## Legendas e legibilidade

Defeitos reproduzidos antes da correção:

- Texto de aproximadamente 923 caracteres em um segundo gerava cerca de 28 linhas, cobrindo quase toda a tela. Evidência anterior em `outputs/media-validation/baseline/legenda-longa-antes.png`.
- Uma legenda de 0,011 s a 0,014 s virava um evento ASS de 0,01 s a 0,01 s, com duração nula.

Agora textos longos são quebrados conservadoramente em páginas de até duas linhas. O tempo de cada página é proporcional à quantidade de texto; páginas consecutivas não se sobrepõem e não removem palavras. Um texto que precisa de várias páginas e ultrapassa 35 caracteres por segundo é recusado com instrução para reduzir/dividir o texto ou ampliar o tempo. Esse limite é uma política conservadora do MVP, não um estudo de velocidade de leitura. Os dados da legenda continuam preservados para correção; o render retorna erro.

O arredondamento ASS usa centésimos externos ao intervalo original para evitar duração zero. Uma legenda menor que um frame ainda pode não coincidir com um frame exibido. Não há alinhamento de palavras nem sincronização fonética das páginas.

Passaram casos com ação/emoção/João/São Paulo, nomes em inglês, C++, pontuação, CRLF, quebra explícita e caracteres de override ASS. Barras e chaves são neutralizadas como texto, sem executar comandos de posicionamento. O teste com texto longo sobre padrão não uniforme confirmou pixels das legendas na região inferior em três instantes, sem cobrir a região central do conteúdo.

Inspeção visual real de `outputs/media-validation/20261029T203102476363Z/legibilidade-1080.png`: 1080 × 1920, conteúdo horizontal completo centralizado, fundo variável desfocado e legenda branca em duas linhas com contorno preto, margens laterais e inferior. Os acentos em “Ação, João!” estão legíveis. A execução final repetiu a geração da mesma amostra em `20261029T203309578761Z`. Isso confirma a amostra sintética, sem certificar contraste em todo vídeo real possível.

## Falhas, cancelamento e timeout

- Arquivo inválido, arquivo removido, diretório, URL e caminho UNC são recusados. Falta de permissão é exercitada por exceções controladas, sem alterar ACLs nem permissões reais.
- Destino existente permanece byte a byte intacto, inclusive no fallback sem hardlink. Uma falha ao abrir a origem do fallback também limpa apenas um destino criado pela própria operação.
- Cancelamento antes de iniciar não publica nada. Cancelamento durante render real finalizou e limpou o temporário em 0,5486 s, medidos desde a chamada inteira, incluindo inspeção e início do render. Esse tempo não representa latência do reconhecimento nativo.
- FFprobe tem limite de 30 s; seu timeout foi exercitado por exceção controlada. Não foi necessário aguardar 30 s nem bloquear um arquivo real.
- O watchdog padrão do FFmpeg exige avanço em até 120 s. O teste reduziu o limite para 0,2 s e encerrou um processo filho próprio sem progresso em 0,2169 s. Um segundo teste demonstrou e corrigiu o caso em que mensagens repetidas com `out_time_us=0` renovavam o relógio sem avanço real. O filho é encerrado e aguardado; progresso repetido já não evita o timeout.
- Staging exclusivo, subprocessos sem shell, protocolos limitados a `file,pipe` e publicação sem sobrescrita foram preservados. Originais mantiveram seus hashes em todos os casos da matriz.

O serviço é responsável por detectar alteração da origem após importação, revisar estado/revisão dos cortes e coordenar publicação/cancelamento de jobs. Essas garantias exigem os testes de integração do serviço, além desta validação de mídia.

## Reprodução e limites

Na raiz do projeto, com FFmpeg/FFprobe já disponíveis:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONUTF8='1'
$env:PYTHONPATH=(Join-Path (Get-Location) 'backend')
python backend/tests/benchmark_media.py
```

O runner cria uma nova pasta de evidências a cada execução. As fixtures da suíte são temporárias e próprias do teste. A amostra 1080p tem um segundo; a matriz usa resolução reduzida. Não foram medidos memória, throughput de VOD longo, HDR, VFR, rotação arbitrária, múltiplas faixas de áudio ou qualidade editorial. Nenhuma inferência de desempenho em horas de live deriva destes números. Não houve mudança de dependência, hardware, WSL, configurações globais, Remotion, frontend ou Git.

## Complemento: pixels anamórficos

Na mesma data, uma entrada sintética de 320 × 180 com um quadrado branco de 80 × 80 pixels codificados demonstrou distorção com SAR 2:1. A referência FFmpeg, convertida para pixels quadrados antes de ajustar ao quadro vertical, exibia a forma com 44 × 22 pixels; o render anterior exibia 44 × 44. O `setsar=1` depois do scale apagava a proporção dos pixels sem compensar a geometria.

O renderer passou a aplicar `reset_sar=1` dentro dos dois filtros scale, junto de `force_original_aspect_ratio`. Assim o ajuste considera a proporção de exibição e já entrega pixels quadrados. Essa combinação é descrita na [documentação oficial do scale](https://ffmpeg.org/ffmpeg-filters.html#scale) e foi confirmada no FFmpeg 9.0.1 instalado. Builds antigos sem a opção `reset_sar` não estão certificados; não foi adicionada uma dependência nem instalado outro FFmpeg.

O teste real comparou a forma central com uma referência independente que primeiro aplica `scale=trunc(iw*sar/2)*2:ih,setsar=1`:

| SAR da entrada | Referência | Render corrigido |
| --- | --- | --- |
| 2:1 | 44 × 22 pixels | 44 × 22 pixels |
| 16:15 | 44 × 42 pixels | 44 × 42 pixels |

As origens mantiveram o hash e as saídas passaram a informar dimensão codificada igual à dimensão de exibição. A suíte de mídia afetada foi executada novamente: **20 testes aprovados em 11,216 s**, sem falhas nem skips; a suíte completa do projeto não foi repetida neste complemento. Relatório atualizado em `outputs/media-validation/20261029T203745143350Z/report.json`. Os sete casos anteriores, inclusive rotação, sincronização, cancelamento e legendas, continuaram passando.
