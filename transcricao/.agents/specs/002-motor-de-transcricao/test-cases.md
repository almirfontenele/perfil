# Test cases: Motor de Transcrição

## Preconditions

- Ambiente do projeto com as dependências declaradas em `plan.md` instaladas (`openai-whisper` e
  as dependências transitivas `torch`, `numpy`, `tiktoken`, `numba`, `tqdm`) e o binário `ffmpeg`
  disponível no `PATH`.
- Nos casos que exercitam a função de orquestração de `app/motor_transcricao/transcricao.py`, a
  chamada ao modelo Whisper (`base`) é substituída por um dublê de teste que devolve, de forma
  controlada, o idioma detectado, o texto transcrito (quando aplicável) e os sinais de confiança
  (`no_speech_prob` e confiança média por segmento) — conforme a estratégia de testes do
  `plan.md`; o modelo real não é carregado nesses casos.
- Nos casos que exercitam diretamente a função de classificação de
  `app/motor_transcricao/classificacao_falha.py`, nenhum áudio nem modelo é carregado: a entrada
  é um valor sintético de energia (RMS) do áudio e de sinais de confiança (`no_speech_prob`,
  confiança média), conforme `plan.md`.
- Os áudios usados como entrada já foram validados quanto a formato e duração pelo domínio
  Captura e Ingestão de Áudio — essa validação está fora do escopo desta unidade
  (`spec.md`, Scope Out).

## Story 1 — Transcrição bem-sucedida em português

### TC-1 (mandatory) — Transcrição concluída para áudio em português

1. Configurar o dublê de teste do modelo Whisper para que a detecção de idioma devolva `pt` como
   idioma de maior probabilidade e a transcrição devolva um texto de amostra para o áudio de
   entrada.
2. Invocar a função de orquestração de `app/motor_transcricao/transcricao.py` com esse áudio.

**Expected:** a chamada retorna de forma síncrona o texto transcrito devolvido pelo dublê, sem
nenhuma das quatro causas de erro do "Contrato de retorno interno" (`plan.md`), conforme a Story
1 do `spec.md`; a devolução desse texto na resposta ao canal de entrada (CLI ou API HTTP) que
originou a chamada é responsabilidade do domínio Captura e Ingestão de Áudio (`spec.md`,
Cross-domain dependencies).

## Story 2 — Idioma não suportado

### TC-2 (mandatory) — Rejeição quando o idioma detectado não é português

1. Configurar o dublê de teste do modelo Whisper para que a detecção de idioma devolva um idioma
   diferente de `pt` (por exemplo, `en`) como idioma de maior probabilidade para o áudio de
   entrada.
2. Invocar a função de orquestração de `app/motor_transcricao/transcricao.py` com esse áudio.

**Expected:** a chamada retorna a causa de erro `idioma_nao_suportado`, sem texto transcrito, e a
etapa de transcrição do dublê de teste não é executada — a detecção de idioma ocorre antes de
qualquer tentativa de transcrever, conforme a Story 2 do `spec.md` e a decisão de detecção de
idioma do `plan.md`.

## Story 3 — Falha por silêncio

### TC-3 (mandatory) — Causa `silencio` classificada a partir da energia do áudio

1. Chamar a função de classificação de `app/motor_transcricao/classificacao_falha.py` com um
   valor de energia (RMS) abaixo do limiar mínimo de silêncio definido na implementação, com
   quaisquer sinais de confiança.

**Expected:** a função devolve a causa `silencio`, conforme a decisão de classificação do
`plan.md` e a Story 3 do `spec.md`.

### TC-4 (mandatory) — Falha por silêncio propagada pela orquestração

1. Configurar o dublê de teste do modelo Whisper para que a detecção de idioma devolva `pt` e a
   transcrição de um áudio no idioma correto não produza texto, com energia do áudio abaixo do
   limiar mínimo de silêncio.
2. Invocar a função de orquestração de `app/motor_transcricao/transcricao.py` com esse áudio.

**Expected:** a chamada retorna a causa de erro `silencio`, sem texto transcrito, conforme a
Story 3 do `spec.md`. Relacionado a TC-3.

## Story 4 — Falha por ruído

### TC-5 (mandatory) — Causa `ruido` classificada a partir da energia e da confiança do áudio

1. Chamar a função de classificação de `app/motor_transcricao/classificacao_falha.py` com um
   valor de energia (RMS) acima do limiar mínimo de silêncio, combinado com `no_speech_prob` alto
   e confiança média baixa em todos os segmentos.

**Expected:** a função devolve a causa `ruido`, distinta de `silencio`, conforme a decisão de
classificação do `plan.md` e a Story 4 do `spec.md`.

### TC-6 (mandatory) — Falha por ruído propagada pela orquestração

1. Configurar o dublê de teste do modelo Whisper para que a detecção de idioma devolva `pt` e a
   transcrição de um áudio no idioma correto não produza texto, com energia do áudio acima do
   limiar mínimo de silêncio e `no_speech_prob` alto/confiança média baixa em todos os segmentos.
2. Invocar a função de orquestração de `app/motor_transcricao/transcricao.py` com esse áudio.

**Expected:** a chamada retorna a causa de erro `ruido`, sem texto transcrito e distinta da causa
`silencio`, conforme a Story 4 do `spec.md`. Relacionado a TC-5.

## Story 5 — Falha interna do motor

### TC-7 (mandatory) — Falha interna do motor durante a inferência

1. Configurar o dublê de teste do modelo Whisper para que a detecção de idioma devolva `pt` e a
   chamada de transcrição levante uma exceção não relacionada a silêncio ou a ruído (por exemplo,
   uma falha simulada de inferência).
2. Invocar a função de orquestração de `app/motor_transcricao/transcricao.py` com esse áudio.

**Expected:** a chamada retorna a causa de erro `falha_interna_motor`, sem texto transcrito e
distinta das causas `silencio` e `ruido`, conforme a Story 5 do `spec.md` e o "Contrato de
retorno interno" do `plan.md`.

## Story 6 — Sem persistência do resultado

### TC-8 (mandatory) — Nenhum dado permanece após uma transcrição bem-sucedida

1. Executar o cenário de TC-1.
2. Inspecionar o sistema de arquivos e o ambiente de execução da aplicação em busca de qualquer
   arquivo ou registro em banco de dados criado a partir dessa chamada.

**Expected:** nenhum arquivo de áudio nem texto transcrito permanece armazenado após a chamada
retornar, conforme a Story 6 do `spec.md` — o domínio não usa banco de dados nem armazenamento de
arquivos (`spec.md`, Domain boundary; `plan.md`, Modelo de dados).

### TC-9 (mandatory) — Nenhum dado permanece após uma falha classificada

1. Executar o cenário de TC-4, TC-6 ou TC-7 (falha por silêncio, ruído ou falha interna do
   motor).
2. Inspecionar o sistema de arquivos e o ambiente de execução da aplicação em busca de qualquer
   arquivo ou registro criado a partir dessa chamada.

**Expected:** nenhum dado do áudio processado nem da causa de erro permanece armazenado após a
chamada retornar, conforme a Story 6 do `spec.md`.

### TC-10 (mandatory) — Chamadas independentes não compartilham estado

1. Executar o cenário de TC-1 (áudio em português, resultado com texto transcrito).
2. Em seguida, executar o cenário de TC-2 (áudio em idioma não suportado) com um dublê de teste
   configurado de forma independente do primeiro.

**Expected:** o resultado da segunda chamada (`idioma_nao_suportado`) não referencia nem é
influenciado pelo texto transcrito ou pelo áudio da primeira chamada, conforme a Story 6 do
`spec.md`.
