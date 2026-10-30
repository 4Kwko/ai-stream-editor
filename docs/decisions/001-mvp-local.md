# ADR 001 — Pipeline local inicial

Data: 2026-10-29. Status: adotada sob autorização de implementação autônoma; escolhas reversíveis. Responsável: GPT no backend; frontend mantido por Claude.

## Contexto

Uso pessoal Windows, PT-BR, mídia local, orçamento externo não autorizado e GPU desconhecida. A entrega útil é um MP4 vertical revisado, com correção de limites/texto, sem publicação. O usuário delegou a escolha da menor solução funcional, substituindo a limitação anterior a planejamento.

## Decisão

Python/FastAPI em loopback 8765, fila de um worker, SQLite stdlib, FFmpeg existente e faster-whisper base CPU/int8 offline após preparação explícita dos pesos. Interface React/TypeScript em 5173 por contrato HTTP. Layout inicial preserva a imagem inteira sobre fundo desfocado; legendas são embutidas. Sugestões usam heurística textual identificada e revisão humana obrigatória para exportação.

## Alternativas consideradas

| Alternativa | Avaliação |
| --- | --- |
| APIs externas de transcrição/LLM | Exigiriam envio de conteúdo e possível cobrança, fora da autorização |
| Exigir CUDA/GPU | Hardware não confirmado e mudanças de sistema não autorizadas |
| LLM local maior para ranking inicial | Download, memória e latência adicionais antes de validar o fluxo; fica para avaliação editorial posterior |
| Remotion para render | FFmpeg já disponível resolve o layout; licença de redistribuição da skill permanece aberta |
| Fila distribuída e banco servidor | Infraestrutura desnecessária para um usuário e um processamento por vez |

## Consequências

Fluxo funciona sem servidor externo nem GPU, com dependências locais separadas. A heurística não garante encontrar os melhores momentos; CPU e disco podem limitar VODs longos. Mudanças futuras devem preservar as revisões de cortes, os originais e o contrato consumido pela interface. WSL é opcional e não foi necessário nem validado nesta implementação.
