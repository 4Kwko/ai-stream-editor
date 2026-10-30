# Formatos16:9 e9:16

Backend entregue em2026-10-30. Usuário confirmou16:9 padrão e opção9:16 com câmera acima/conteúdo abaixo. [Contrato](../coordination/integration-contract.md) e [ADR004](../decisions/004-output-formats-and-camera.md). Interface/configuração visual é do Claude; GPT não alterou frontend.

## Comportamento

GET/PATCH `/api/automation` aceita/devolve output_format16:9 ou9:16. Preferência vale para próximos VODs iniciados, não reconverte acervo. VOD/retry/projeto/corte preservam seu snapshot. Novos projetos locais também seguem a configuração. Artefatos anteriores sem campo continuam9:16. Avaliação não modifica formato, revisão ou arquivo.

Formato normal preserva imagem inteira, áudio e legendas. Vertical usa detecção local de região de rosto estável e compõe dois painéis. Se detectar câmera, layout camera_top_content_bottom; caso contrário, full_frame com aviso legível. Perfil normal usa source_preserved. Formato/layout/aviso são publicados em Clip, GalleryItem e resultado do render. Não há coordenadas de recorte editáveis na API do produto.

## Verificação automatizada

94 testes e11 subtestes passaram em39,19s no conjunto afetado: formatos/câmera/API/automação/ciclo de vida/mídia. Após o ajuste de centralização perto da borda,25 testes focados passaram em8,68s. As execuções se sobrepõem; não somar. Incluem:

- default/migração16:9 preservando canal/pausa;
- preferência alterada após criação do projeto e entre retries;
- mudança de configuração/avaliação sem novos jobs nem alteração de hash;
- arquivos antigos preservados como9:16;
- render horizontal e vertical reais com áudio;
- câmera acima e conteúdo abaixo conferidos por pixels em fixture colorida;
- ausência, ambiguidade e indisponibilidade com fallback/aviso;
- classificação nativa negativa em vídeo sintético;
- estabilidade/centralização do recorte, cancelamento e coordenadas inválidas;
- matriz existente de mídia, rotação/SAR, legendas, sincronização e recuperação.

OpenCV headless4.14.0.94 foi instalado apenas em backend/.venv e fixado no lock/pyproject. NumPy2.5.4 mantido; pip check passou. Nenhuma ferramenta global/WSL/GPU instalada.

## Execução nativa positiva

Evidência ignorada pelo Git: `backend/.test-data/output-formats-native/run-91d45594c1/evidence.json`.

Vídeo controlado4s/1280×720/testsrc com áudio de tom e uma [imagem pública de teste do OpenCV](https://github.com/opencv/opencv/blob/4.x/samples/data/lena.jpg) compondo uma câmera. Fonte/proveniência/hash ficam em `.test-data/output-formats-native/photo-provenance.json`; não houve acesso a fotos pessoais nem versionamento desse material. Não é VOD real nem webcam do usuário. ASR foi simulado e identificado; OpenCV e FFmpeg foram reais.

Detector retornou região estável. Pipeline via API ASGI gerou1920×1080/source_preserved e1080×1920/camera_top_content_bottom,4s,10fps, áudio/legendas. Frames dos dois resultados foram extraídos e inspecionados. Origem preservada por hash; mudança da preferência final para16:9 não criou jobs nem alterou os resultados existentes. O teste anterior está preservado em run-f00b95d532; não usar a primeira calibração como resultado final.

## API em execução

A API estava parada ao verificar as portas; o inicializador existente a reabriu e reutilizou o Vite já ativo. GET real confirmou16:9 padrão, supervisor ativo,7 projetos e5 cortes anteriores ainda9:16/full_frame. Evidência `.test-data/output-formats-native/live-evidence.json`. A preferência é persistida no banco de dados existente.

Próximos passos: Claude adicionar o seletor global e metadados na galeria; VOD público disponível para conferir detecção/framing no canal. Não declarar rastreamento de rosto, identificação exata da webcam ou qualidade editorial comprovada. A busca do canal continua automática, enquanto o backend estiver ativo.
