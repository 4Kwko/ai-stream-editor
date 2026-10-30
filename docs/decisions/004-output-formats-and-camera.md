# ADR004 — Formato normal por padrão e vertical com câmera

Adotada em2026-10-30 por confirmação explícita do usuário:16:9 padrão, opção9:16, câmera acima e conteúdo abaixo. Sucede o formato vertical único da ADR003, mantendo geração automática e apenas avaliação na galeria.

## Configuração e compatibilidade

`Automation.output_format` persiste a preferência global. Na migração de configuração antiga, acrescenta16:9 sem alterar canal/pausa. O VOD captura a preferência ao iniciar processamento; retries preservam a escolha. Projeto e cortes guardam o formato. Mudar a configuração não refaz um VOD ativo nem os vídeos já concluídos. Registros antigos sem formato continuam9:16/full_frame para não reclassificar ou invalidar arquivos existentes.

Saída normal1920×1080 preserva a imagem toda, com margens quando a fonte tiver outra proporção, áudio e legendas. Saída vertical1080×1920 tenta recortar a região de câmera acima e coloca o VOD inteiro abaixo sobre fundo desfocado. Não depende de sliders ou aprovação antes de gerar.

## Adaptação local

Escolhido OpenCV headless4.14.0.94, fixado no venv/lock, com o classificador Haar distribuído pelo próprio pacote. A [documentação OpenCV](https://docs.opencv.org/4.x/db/d28/tutorial_cascade_classifier.html) descreve detecção de faces por CascadeClassifier; o [pacote headless](https://pypi.org/project/opencv-python-headless/) inclui os modelos e dispensa interface gráfica. Sem API remota, modelo baixado em runtime ou identificação de pessoas.

FFmpeg extrai seis frames reduzidos e limitados do intervalo. Um rosto precisa aparecer em pelo menos quatro frames, em posição compatível. Dois grupos igualmente persistentes ou resolução variável são ambíguos. O recorte infere margem para cabeça/ombros e tenta manter o rosto centralizado perto das bordas; fica estático durante o corte. Não é rastreamento dinâmico nem detector preciso da moldura da webcam.

Sem câmera confiável, mantém o conteúdo inteiro no vertical e informa layout_warning. Não inventa uma caixa, não solicita ajuste por corte e não impede salvar outros resultados. Falhas de ferramenta que impedem o próprio render continuam erros de job. Cancelamento interrompe extração própria e não publica vídeo parcial.

## Consequências e limites

Nova dependência local de41MB, sem troca do NumPy preparado.16:9 não executa o detector. Só a opção vertical paga esse custo de CPU. Amostragem pode perder câmera intermitente; personagens/cenas podem produzir falsos positivos. O conteúdo inferior preserva a webcam já embutida no VOD; não reconstrói pixels ocultos por ela. Legendas/áudio usam o pipeline existente.

Testes controlados verificaram proporções, posição dos painéis, persistência/retries, legado, cancelamento, coordenadas inválidas e fallback. Detecção positiva nativa usou imagem pública de teste do OpenCV dentro de vídeo gerado localmente; não certifica a webcam do usuário. Precisa de VOD real para avaliar enquadramento e legibilidade no conteúdo do canal. Claude mantém seletor global e apresentação dos metadados na galeria.
