# AI Stream Editor: frontend

Galeria de cortes prontos: React 19 + TypeScript + Vite 8. Fala com o backend em `http://127.0.0.1:8765/api`; o contrato está em `docs/coordination/integration-contract.md` (extensão "automação e galeria", 2026-10-30).

## O que a tela faz

- **Automação.** Mostra o estado de `GET /automation`: canal, se está aguardando gravação, obtendo vídeo, analisando ou gerando cortes, e se há problema que precisa de atenção.
  - O progresso é da etapa atual, sem total nem tempo restante.
  - "Configurar canal" altera só o login público do canal e liga ou desliga a busca (`PATCH /automation`). Não pede senha nem chave.
- **Galeria.** Lista os cortes prontos (`GET /gallery`), 20 por vez com "Carregar mais".
  - Filtros: Para avaliar, Gostei, Não gostei e Todos.
  - Um player por vez, montado só depois do clique em "Assistir".
  - "Baixar MP4" usa o mesmo arquivo pronto, sem nova renderização.
- **Avaliação.** Gostei e Não gostei gravam no backend (`PATCH /clips/{id}` com `review_status`). Há confirmação "Salvo", proteção contra clique duplo e erro visível quando a gravação falha. Avaliar não altera nem regenera a mídia.
- **Atualização.** Consulta o status a cada 10 s, só com a aba visível. Quando um VOD novo termina, a lista carrega sozinha se estiver vazia; se já houver cortes na tela, aparece o aviso "Há cortes novos prontos".

A interface não baixa VODs nem dispara processamento. Isso é feito pelo backend, enquanto os serviços estão rodando neste PC.

## Abrir com um clique (este PC)

`frontend/launcher/dist/AI Stream Editor.exe` (há um atalho na área de trabalho):

- **Se o backend e a interface já estão rodando,** só abre o navegador.
- **Se não estão,** chama `backend\.venv\Scripts\python.exe -m ai_stream_editor.local` (o mesmo de `scripts/start-local.ps1`) e espera os dois ficarem prontos.
- **A janela** fica aberta enquanto o app roda; fechá-la encerra só o que ela iniciou.

O lançador não instala nada e depende do ambiente já preparado neste PC: `backend\.venv`, `frontend\node_modules` e Node no PATH. Por isso o .exe precisa ficar dentro da pasta do projeto.

Gerar ou atualizar o .exe (usa o compilador C# do .NET Framework 4, que já vem no Windows):

```powershell
cd frontend
npm run launcher
```

## Executar em desenvolvimento

Requer Node 24 (testado com 24.19.0 / npm 11.17.0).

```powershell
cd frontend
npm install
npm run dev        # http://127.0.0.1:5173 (backend real via proxy /api)
npm run dev:mock   # abre http://127.0.0.1:5173/?mock=1 (dados simulados)
```

O Vite encaminha `/api` para `http://127.0.0.1:8765`. Integração validada só com `npm run dev` (porta 5173, a origem aceita pelo backend).

## Verificar

```powershell
npm run typecheck
npm run lint
npm test
npm run build
```

## Modo demonstração (mock)

`src/api/mock.ts` simula a API em memória, seguindo o contrato. Só é usado com `?mock=1` ou `VITE_API_MODE=mock`, e a interface mostra a faixa "Modo demonstração". Não há vídeo real nem ligação com a Twitch. O mock não comprova integração.

Cenários com `?mock=1&cenario=`:

| Cenário | Situação |
| --- | --- |
| `pronto` (padrão) | 5 cortes, automação em dia |
| `vazio` | Canal sem gravação disponível |
| `config` | Configuração necessária no backend |
| `parado` | Serviço de automação parado |
| `processando` | VOD em análise; os cortes chegam após algumas consultas |
| `falha` | Problema em um VOD; avaliar um dos cortes falha |
| `muitos` | 60 cortes, para testar a paginação |

## Design system

Direção "sala de corte", com auditoria, referências e curadoria em `docs/implementation/design-system.md`.

- **Cores, tipografia, espaçamento, raios e movimento:** todos em `src/styles/tokens.css`. Para trocar a paleta, edite só o bloco "Paleta base".
- **Fontes:** IBM Plex Sans e Mono (OFL 1.1), empacotadas localmente via `@fontsource`. O app funciona offline.
- **Atalhos na galeria:** setas percorrem os cortes, `G` marca Gostei, `N` marca Não gostei e `Enter` assiste. Em "Para avaliar", o foco avança sozinho depois de salvar.

## Estrutura

| Caminho | Conteúdo |
| --- | --- |
| `src/api/types.ts` | Tipos do contrato e interface `Api` |
| `src/api/client.ts` | Cliente HTTP único (erros, `detail` do FastAPI, cancelamento, URLs) |
| `src/api/mock.ts` | Mock identificado, com cenários |
| `src/hooks/useAutomationStatus.ts` | Consulta periódica do status, cancelada ao desmontar |
| `src/styles/tokens.css` | Tokens semânticos (única fonte de cor, tipo, espaço, forma e movimento) |
| `src/components/AutomationPanel.tsx` | Faixa de estado da automação e configuração do canal |
| `src/components/GalleryCard.tsx` | Card: player sob demanda, avaliação, download |
| `src/components/SegmentedControl.tsx` | Filtros (padrão radio, indicador deslizante) |
| `src/components/Icon.tsx` | Ícones próprios (grade 16, traço 1,5) |
| `src/App.tsx` | Galeria, filtros, paginação e avaliação |
| `launcher/` | Lançador .exe |

## Limitações conhecidas

- O contrato não traz totais por filtro. A tela mostra quantos cortes estão carregados e se há mais.
- Não há miniatura: cada card mostra "Assistir" e carrega o vídeo só no clique.
- O filtro escolhido fica no `localStorage` deste navegador. As avaliações ficam no backend.
