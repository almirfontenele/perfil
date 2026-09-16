# Research: Motor de Transcrição

## Biblioteca de transcrição Whisper local

**Contexto.** O domínio precisa de um motor Whisper executado localmente, sem chamada a serviço
remoto, para converter o áudio validado em texto. A skill do domínio e o `functional-map.md`
citam `openai-whisper` e `faster-whisper` como bibliotecas equivalentes para essa necessidade,
sem fixar qual delas adotar.

**Alternativas:**

- **`openai-whisper`** — implementação de referência da OpenAI, em PyTorch; API simples
  (`load_model` + `transcribe`), maior consumo de memória e tempo de inferência por chamada.
- **`faster-whisper`** — reimplementação otimizada sobre CTranslate2; inferência mais rápida e
  com menor uso de memória para o mesmo modelo, ao custo de uma API própria e de um formato de
  modelo convertido, distinto do formato nativo do PyTorch.

**Decisão:** `openai-whisper`.

**Base de confirmação:** confirmado pelo usuário (resposta ao gap `gap-13-biblioteca-whisper`).

**Consequências:** `openai-whisper` entra como dependência do projeto, trazendo `torch`,
`numpy`, `tiktoken`, `numba` e `tqdm` como dependências transitivas. A decodificação do áudio
recebido (WAV, MP3, M4A, OGG, FLAC) para o formato de entrada do modelo é feita internamente
pela biblioteca via `whisper.load_audio()`, que depende do binário externo `ffmpeg` disponível
no `PATH` do ambiente de execução — dependência de sistema, não de pacote Python.

## Tamanho do modelo Whisper

**Contexto.** O domínio precisa carregar um checkpoint específico do modelo Whisper para
realizar a inferência a cada chamada síncrona. O tamanho do modelo determina o consumo de
CPU/GPU e memória, o tempo de resposta por chamada e a acurácia da transcrição e da detecção de
idioma; nenhuma fonte do projeto declarava um requisito de desempenho ou de acurácia que
permitisse derivá-lo sem reserva.

**Alternativas:**

- **`tiny`** — menor consumo de recursos e menor latência; acurácia mais baixa, mais sujeita a
  erros de transcrição e de detecção de idioma.
- **`base`** — equilíbrio leve entre velocidade e acurácia, ainda viável em CPU comum.
- **`small`** — acurácia intermediária, com consumo de recursos moderado.
- **`medium`** — acurácia alta, exige mais CPU/GPU e memória; tempo de inferência maior por
  chamada síncrona.
- **`large`** — acurácia máxima entre os checkpoints padrão; maior custo de CPU/GPU e memória,
  menos adequado a um processamento síncrono sem hardware dedicado.

**Decisão:** `base`.

**Base de confirmação:** confirmado pelo usuário (resposta ao gap `gap-14-modelo-whisper`).

**Consequências:** o domínio carrega o modelo com `whisper.load_model("base")`; os pesos desse
checkpoint são baixados automaticamente para o cache local do `openai-whisper` na primeira
execução, sem exigir uma etapa de provisionamento própria desta unidade. O checkpoint `base`
mantém a chamada síncrona viável em CPU comum, com acurácia suficiente para o caso de uso sem
requisito de precisão declarado.

## Classificação da causa de falha de transcrição (silêncio vs. ruído)

**Contexto.** A regra de negócio 6 da skill do domínio exige distinguir, para um áudio no idioma
correto cuja transcrição não é concluída normalmente, a causa entre silêncio (sem fala
perceptível), ruído (dominado por ruído sem fala identificável) e falha interna do motor. Os
sinais nativos do `openai-whisper` (`no_speech_prob` e confiança média por segmento) sozinhos não
bastam: um áudio silencioso e um áudio ruidoso sem fala identificável podem produzir o mesmo
sinal de baixa confiança, sem informação suficiente para diferenciá-los.

**Alternativas:**

- **Sinais nativos do Whisper combinados com energia (RMS) do áudio bruto** — usa apenas a saída
  já produzida pela transcrição (`no_speech_prob`, confiança média) e uma medição simples de
  energia do áudio decodificado, sem dependência nova: energia abaixo de um limiar mínimo indica
  silêncio; energia acima do limiar com baixa confiança/`no_speech_prob` alto indica ruído.
- **Biblioteca dedicada de detecção de atividade de voz (VAD)** — por exemplo `webrtcvad` ou
  `silero-vad`, aplicada ao áudio bruto antes da transcrição para decidir se há fala presente;
  mais precisa em áudios com fala de baixa energia, mas introduz uma dependência nova e uma etapa
  de pré-processamento adicional ao fluxo síncrono.

**Decisão:** sinais nativos do Whisper combinados com energia (RMS) do áudio bruto.

**Base de confirmação:** confirmado pelo usuário (resposta ao gap
`gap-15-classificacao-silencio-ruido`).

**Consequências:** nenhuma dependência nova além de `numpy` (já trazida por `openai-whisper`)
para o cálculo de energia; `classificacao_falha.py` implementa essa heurística como função pura,
testável com entradas sintéticas. Os limiares de energia e de `no_speech_prob`/confiança são
calibrados durante a implementação com áudios de amostra representativos de cada causa —
registrado como risco em `plan.md`, não como decisão em aberto, pois a abordagem em si já está
confirmada.
