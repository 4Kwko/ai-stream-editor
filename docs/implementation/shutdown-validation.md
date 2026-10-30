# Encerramento da API com reconhecimento nativo ativo

2026-10-29. Teste real isolado, escrito pelo subagente de análise e conferido pelo GPT após ele atingir o limite. Arquivo: `backend/tests/smoke_shutdown.py`. Sem instalação, download, serviço externo, mídia pessoal ou operação Git de escrita.

## Evidência

`backend/.test-data/shutdown-a5c114d48f/evidence.json` e `server.log`. Servidor próprio na porta efêmera 58999, diretório de dados exclusivo. As portas do produto 8765 e 5173 estavam disponíveis antes e depois; não foram sinalizadas nem encerradas.

- Modelo base existente, CPU/int8 offline; vídeo artificial PT-BR de630s já gerado pela execução.
- Job observado running, etapa Transcrevendo em PT-BR. Marcadores envolveram `next()` do gerador nativo real sem substituir arrays, argumentos ou segmentos. O sinal ocorreu entre native_next_begin e native_next_end.
- CTRL_BREAK foi enviado apenas ao grupo do servidor filho. Encerramento em **0,859s**, sem limpeza forçada. Log: Application shutdown complete; sem traceback.
- O processo retornou código3 após o sinal no Windows. Isso não foi tratado como retorno zero: a evidência funcional é fechamento completo, cancelamento persistido e ausência de descendentes.
- Banco privado foi lido em modo somente leitura **antes** de instanciar Service novamente: job canceled, erro Processamento cancelado., resultado null, sem transcrição nem cortes parciais. elapsed_seconds2,078 inclui o processamento anterior ao sinal.
- A trava pôde ser readquirida depois dessa comprovação; o estado continuou canceled. Não foi a recuperação de startup que criou esse resultado.
- Toolhelp observou somente IDs/pais/nomes para reter os descendentes do servidor próprio. Não restaram descendentes; os FFmpeg/FFprobe observados eram do teste. Não foram consultadas linhas de comando nem credenciais de outros aplicativos.

## Reprodução

Com API/interface principais preservadas, a partir de backend:

```powershell
.\.venv\Scripts\python.exe tests\smoke_shutdown.py --run-real
```

O runner exige o modelo local e a fixture sintética específica. Cria nova pasta de evidência e usa porta efêmera; recusa8765/5173. A primeira tentativa restrita (`shutdown-501373dee8`) não disponibilizou o servidor em30s e não é evidência de funcionamento. A execução seguinte autorizada (`shutdown-a5c114d48f`) passou; o relatório registra ambas separadamente.

O resultado é uma observação nessa máquina/fixture, sem garantia de latência em outro decode ou VOD. Cancelamento continua cooperativo. Complementa testes de fila/recuperação do serviço e o smoke do inicializador com conexões de vídeo abortadas; não substitui avaliação editorial.
