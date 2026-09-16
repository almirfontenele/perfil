# Tasks: Motor de Transcrição

- [ ] **T1. Transcrição bem-sucedida e rejeição por idioma não suportado**
  - Depends on: none
  - Introduz `openai-whisper` como dependência do projeto (traz `torch`, `numpy`, `tiktoken`,
    `numba` e `tqdm` como dependências transitivas) e a estrutura `tests/motor_transcricao/` —
    nomeado como pré-requisito desta task, por ser a primeira a precisar deles; exige também o
    binário `ffmpeg` disponível no `PATH` do ambiente de execução, usado internamente pela
    biblioteca para decodificar o áudio recebido.
  - Função de orquestração em `app/motor_transcricao/transcricao.py`, consumida em processo pelo
    domínio Captura e Ingestão de Áudio: carrega o modelo Whisper `base`, decodifica o áudio
    recebido e detecta o idioma falado antes de transcrever (Story 1 do `spec.md`; regra de
    negócio 2 da skill do domínio).
  - Quando o idioma detectado é português, produz o texto transcrito e o devolve de forma
    síncrona (Story 1 do `spec.md`); quando é qualquer outro idioma, devolve a causa
    `idioma_nao_suportado` sem tentar transcrever (Story 2 do `spec.md`).
  - Nenhuma escrita em arquivo ou banco de dados durante o fluxo, em nenhum dos dois casos
    (Story 6 do `spec.md`).
  - Testes unitários cobrindo TC-1, TC-2, TC-8 e TC-10 do `test-cases.md`, com a chamada ao
    modelo Whisper substituída por um dublê de teste.

- [ ] **T2. Classificação da causa de falha em silêncio, ruído ou falha interna do motor**
  - Depends on: T1
  - Função de classificação em `app/motor_transcricao/classificacao_falha.py`: combina a energia
    (RMS) do áudio decodificado com os sinais nativos do Whisper (`no_speech_prob` e confiança
    média por segmento) para distinguir silêncio de ruído, conforme a heurística registrada no
    `plan.md`.
  - Estende a função de orquestração de `app/motor_transcricao/transcricao.py` (T1): quando o
    idioma detectado é português mas a transcrição não produz texto, consulta a função de
    classificação e devolve a causa `silencio` ou `ruido`; qualquer exceção da biblioteca não
    coberta por essas duas causas é devolvida como `falha_interna_motor` (Stories 3, 4 e 5 do
    `spec.md`).
  - Nenhuma escrita em arquivo ou banco de dados durante o fluxo, em nenhuma das três causas de
    falha (Story 6 do `spec.md`).
  - Testes unitários cobrindo TC-3, TC-4, TC-5, TC-6, TC-7 e TC-9 do `test-cases.md`, com a
    chamada ao modelo Whisper substituída por um dublê de teste e a função de classificação
    também testada isoladamente com valores sintéticos de energia e de confiança.
