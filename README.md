# AI Stream Editor

Ferramenta pessoal que busca automaticamente os VODs do canal Twitch configurado (inicialmente `joaomontagner`) e gera cortes verticais com áudio e legenda PT-BR. O usuário abre uma galeria de vídeos prontos e marca **Gostei** ou **Não gostei**.

## Direção atual (2026-10-30)

A galeria automática ([decisão D9 do brief](docs/planning/product-brief.md)) substitui o editor manual como experiência principal. A interface mostra o estado da automação e os cortes prontos, e grava as avaliações; não há ajuste de início e fim, edição de legenda nem etapas manuais.

Quem busca, baixa, transcreve e gera os cortes é o backend, enquanto os serviços estiverem rodando neste PC. Com o app fechado ou o PC desligado, nada é buscado.

Estado da integração: veja [frontend-status](docs/coordination/frontend-status.md) e [backend-status](docs/coordination/backend-status.md). O texto abaixo descreve o MVP de edição manual e fica como histórico até ser revisado.

Para abrir: atalho **AI Stream Editor** na área de trabalho, ou `frontend/launcher/dist/AI Stream Editor.exe`. Ele usa `python -m ai_stream_editor.local`.

## Estado anterior (MVP de edição manual, 2026-10-29)

Em 2026-10-29, a autorização de execução autônoma restabeleceu GPT no backend/integração e Claude no frontend. Existem API Python, banco SQLite, processamento FFmpeg/faster-whisper local e interface React/TypeScript. O fluxo integrado foi executado com vídeo sintético PT-BR: análise, correção de legenda/limites, preview 9:16, aprovação e exportação, preservando o original.

Backend: **95 testes e 21 subtestes aprovados**, transcrição real offline de fixture artificial de 10 min e meio e fluxo pela interface real. Cancelamento, recuperação, exportação, legendas, vídeos rotacionados/anamórficos e inicialização local receberam verificações adicionais. A detecção continua heurística; qualidade editorial e desempenho em VODs reais longos precisam de avaliação. Os testes e o estado do frontend são mantidos pelo Claude em seu relatório.

## Executar

Requer Python 3.12, FFmpeg/FFprobe e Node 24. Nesta máquina, dependências locais e modelo base já estão preparados. Na raiz, em um terminal:

```powershell
.\scripts\start-local.ps1
```

Esse comando reutiliza serviços reconhecidos e inicia apenas os ausentes, sem instalar nada nem encerrar aplicações alheias. Para iniciar separadamente, use:

```powershell
.\scripts\start-backend.ps1
```

Em outro terminal:

```powershell
cd frontend
npm run dev
```

Abra http://127.0.0.1:5173. Desde 2026-10-30 a página é a galeria de cortes automáticos. O fluxo anterior (colar o caminho de um vídeo, analisar, revisar, gerar preview, aprovar e exportar) saiu da interface. Não há publicação.

Diagnóstico sem alterações: `scripts/check-local.ps1`. Uso de disco sem limpeza: `scripts/check-local.ps1 -StorageOnly`. O FFmpeg precisa oferecer libx264, libass e scale/reset_sar; a versão 9.0.1 foi verificada.

Em uma instalação nova, use primeiro `scripts/setup-backend.ps1`, depois `scripts/start-backend.ps1 -PrepareModel`, e siga o [README do frontend](frontend/README.md) para suas dependências. Pesos são baixados de fonte pública; a transcrição e análise usam só arquivos locais. Nenhum serviço pago é necessário. Detalhes e testes no [README do backend](backend/README.md).

## Continuidade

- [Estado do backend e pedidos de integração](docs/coordination/backend-status.md)
- [Contrato HTTP](docs/coordination/integration-contract.md)
- [Retomada do backend](docs/implementation/backend-continuity.md)
- [Fila de entregas e evidências](docs/implementation/backend-work-queue.md)
- [Validação da análise e medições](docs/implementation/analysis-validation.md)
- [Validação de mídia](docs/implementation/media-validation.md)
- [Decisão técnica do MVP](docs/decisions/001-mvp-local.md)

Próximo passo: avaliar um vídeo representativo escolhido pelo usuário. Dados de execução e modelos ficam por padrão em `%LOCALAPPDATA%/AIStreamEditor`, fora do OneDrive. A pasta do código permanece no OneDrive; não houve mudança de sistema nem operação Git de escrita.

Esta pasta (`ai lives`) é a raiz do projeto. O repositório Git está em `main`, sem commits nem remote. `graft/` é um índice regenerável, fora do versionamento. Os documentos de setup e planejamento anteriores ficam como histórico; sua autorização antiga não limita a implementação atual.

## Orientação

- [Regras do agente](AGENTS.md) e [instruções do Claude Code](CLAUDE.md)
- [Regras de trabalho](docs/coordination/collaboration-rules.md)
- [Setup do Claude Code](docs/setup/claude-setup.md), [inventário](docs/setup/claude-skills-inventory.md) e [validação](docs/setup/claude-validation-report.md)
- [Registro de decisões](docs/decisions/README.md)

Histórico do setup com dois agentes (S0.1–S0.4), mantido como registro:

- [Auditoria do ambiente](docs/setup/environment-audit.md)
- [Setup do Codex](docs/setup/codex-setup.md) e [validação do Codex](docs/setup/codex-validation-report.md)
- [Inventário de skills do Codex e da instalação Remotion](docs/setup/skills-inventory.md)

A instalação local de Remotion está em `.agents/skills/remotion-best-practices/`. São referências de terceiros, não uma aplicação do projeto, e o Claude Code não as descobre nesse caminho.
