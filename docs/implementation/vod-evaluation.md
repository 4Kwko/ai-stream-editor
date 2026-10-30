# Avaliação do MVP com um VOD autorizado

Estado em 2026-10-29: o usuário respondeu sim à avaliação local, mas ainda não informou o caminho do VOD. Este roteiro prepara a avaliação; não comprova qualidade editorial nem autoriza procurar vídeos no computador. Transcrição, análise e render permanecem locais. A próxima etapa depende de identificar o arquivo, sem pedir novamente a autorização já dada.

## 1. Escolher uma amostra

O usuário informa o caminho completo do arquivo e, de preferência, um intervalo representativo de aproximadamente 10–20 minutos. Começar pelo VOD inteiro não é necessário. Evitar selecionar somente abertura, tela de espera ou silêncio se o objetivo for avaliar cortes interessantes.

Antes de executar, registrar em uma pasta de resultados ignorada pelo Git:

- identificador da avaliação, arquivo autorizado e intervalo escolhido;
- duração, resolução, orientação, áudio e condições conhecidas, como ruído ou mais de uma voz;
- modelo, versões, threads e layout utilizado;
- tamanho/modificação e, quando viável, hash da origem;
- data e escopo da autorização.

Não colocar nomes de arquivos privados, transcrição ou conteúdo do VOD nos documentos versionáveis. Usar identificadores como R01 nestes documentos e guardar o relatório detalhado somente em `backend/.test-data/` ou outra pasta privada explicitamente escolhida. Não mover nem sobrescrever o original.

Se for preciso gerar uma amostra, criar outro arquivo em pasta de trabalho e registrar o deslocamento para o tempo original. O intervalo deve ser explícito. O usuário pode usar um arquivo menor já preparado por ele.

## 2. Separar as duas perguntas de qualidade

**Transcrição:** as palavras estão corretas? Conferir trechos com fala normal, nomes próprios, termos em inglês, gírias e momentos com ruído. Registrar exemplos de erro e o trabalho de correção. Uma amostra pequena não é uma taxa geral de acerto; não calcular WER sem uma referência transcrita e conferida.

**Seleção editorial:** os candidatos merecem virar cortes? Antes de ver as sugestões, o usuário pode anotar alguns momentos que considera úteis. Depois, comparar o que foi encontrado, o que ficou de fora e o contexto preservado. A própria saída do algoritmo não serve como referência independente.

O sistema atual usa sinais textuais, não análise visual ou entendimento semântico. Pode perder eventos sem os marcadores contemplados. Zero sugestões pode ser um resultado válido, mas precisa ser comparado com o conteúdo observado pelo usuário.

## 3. Revisar os candidatos

Para cada candidato, assistir ao preview e responder:

| Campo | O que registrar |
| --- | --- |
| Identificador e intervalo | ID do corte, início/fim na amostra e no original |
| Veredito | Útil sem ajustes / útil com ajustes / descartado |
| Contexto | Entende-se o assunto sem assistir ao restante da live? |
| Limites | Começou cedo/tarde ou terminou antes da conclusão? |
| Legenda | Erros de texto, sincronização, tamanho, contraste ou posição |
| Ajustes | Quanto mudou nos tempos e quais textos foram corrigidos |
| Esforço de revisão | Tempo gasto para chegar a um arquivo aproveitável |
| Exportação | MP4 gerado, áudio presente, destino e revisão conferidos |

Para momentos esperados não encontrados, anotar intervalo e descrição em palavras do usuário. Não inventar uma justificativa visual a partir da transcrição.

Resumo mínimo: quantidade revisada, aproveitável sem ajustes, aproveitável após ajustes, descartada e momentos anotados que não foram encontrados. Esses números descrevem somente a amostra avaliada.

## 4. Medir recursos sem misturar escopos

Registrar tempos de extração, transcrição, sugestão e render separadamente. Jobs expõem os tempos disponíveis; o progresso pertence à etapa, sem prever a duração total.

Quando medir memória, informar residente versus privada comprometida, frequência de amostragem e processos incluídos. Os benchmarks atuais incluem Python/bibliotecas nativas e excluem os filhos FFmpeg. Não apresentar residente como consumo total nem extrapolar uma fixture com muita pausa para fala contínua de horas.

Depois de uma amostra aceitável, avaliar um VOD completo escolhido pelo usuário e observar duração, estabilidade, espaço de temporários e revisão de vários cortes. GPU e serviços externos não são pré-requisitos desta rota CPU.

## 5. Conferir integridade e interface

- Correção de texto/limites persiste após salvar e recarregar.
- Alterações invalidam o preview e a aprovação deve corresponder ao resultado revisado.
- Render/exportação cancelados terminam com o estado informado pelo backend; publicação já concluída permanece sucesso.
- Uma segunda exportação não substitui o primeiro MP4 nem o original.
- Histórico informa revisão/data/caminho, sem prometer que um arquivo movido ainda existe.
- Sucesso vazio oferece uma ação válida, sem tentar novamente um projeto concluído.
- Warning de persistência permanece um aviso junto do resultado publicado, sem exigir nova exportação automaticamente.

Não provocar falhas alterando ACLs, encerrando processos alheios ou apagando arquivos pessoais. Casos de persistência usam injeção controlada em dados de teste.

## 6. Decidir o próximo ajuste

Corrigir primeiro os problemas que impediram aproveitar um corte: transcrição, falta de contexto, limites, legenda ou falha de fluxo. Não mudar vários parâmetros de ranking ao mesmo tempo para encobrir um resultado ruim.

O usuário decide se o resultado já poupa trabalho. Só ampliar a amostra ou comparar outra abordagem depois de registrar a evidência anterior. Serviços externos, publicação, modelos maiores e mudanças de stack continuam fora desta autorização.
