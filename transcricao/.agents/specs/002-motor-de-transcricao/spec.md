# Spec: Motor de Transcrição

## Overview

Conversão síncrona, por um motor Whisper local, do áudio já validado pelo domínio Captura e
Ingestão de Áudio em texto transcrito em português (pt-BR), com detecção de idioma e distinção
das causas de falha de transcrição, sem persistir o resultado.

## Domain

- Slug: `motor-de-transcricao`
- Skill: [`.agents/skills/motor-de-transcricao/SKILL.md`](../../skills/motor-de-transcricao/SKILL.md)

## Scope

**In:**

- Detecção do idioma falado no áudio recebido, antes de transcrever.
- Transcrição do áudio para texto exclusivamente quando o idioma detectado é português (pt-BR).
- Rejeição do áudio, sem transcrever, quando o idioma detectado não é português.
- Transcrição feita por um motor Whisper executado localmente, sem chamada a serviço remoto de
  transcrição.
- Processamento síncrono: a chamada de origem (CLI ou API HTTP) permanece bloqueada até o
  resultado — texto transcrito ou erro — estar pronto.
- Distinção da causa de falha de transcrição de um áudio no idioma correto entre: silêncio (sem
  fala perceptível), ruído (dominado por ruído sem fala identificável) e falha interna do motor
  durante a inferência.
- Devolução do resultado (texto transcrito ou causa do erro) pelo mesmo canal de entrada (CLI ou
  API HTTP) que originou a chamada, sem reter nenhum dado após a resposta.

**Out:**

- Recebimento de áudio pelos canais CLI e API HTTP e validação de formato e de duração —
  responsabilidade do domínio Captura e Ingestão de Áudio.
- Definição da rota HTTP e do formato exato dos payloads de sucesso e de cada erro — formalizados
  no `openapi.yaml` quando o endpoint HTTP correspondente for implementado, conforme a
  technical-skill `documentacao-de-api`.
- Persistência de áudio, de texto transcrito ou histórico de transcrições anteriores — não
  suportado, por decisão transversal do projeto.
- Suporte a idiomas além de português (pt-BR), detecção multilíngue ou transcrição forçada de
  áudio em outro idioma — não suportado.

## Domain boundary

**This spec implements:**

- Módulo de detecção do idioma falado no áudio recebido.
- Módulo de transcrição via motor Whisper local (`openai-whisper` ou `faster-whisper` — escolha
  de implementação registrada em `plan.md`).
- Regra de rejeição de áudio cujo idioma detectado não é português.
- Classificação da falha de transcrição de um áudio no idioma correto em três causas
  distinguíveis: silêncio, ruído e falha interna do motor durante a inferência.
- Ponto de entrada deste domínio, consumido em processo pelo domínio Captura e Ingestão de
  Áudio: recebe o áudio já validado e devolve o texto transcrito ou o erro classificado.
- Infraestrutura de decodificação do áudio recebido (WAV, MP3, M4A, OGG, FLAC) para o formato de
  entrada exigido pelo motor Whisper — cross-cutting criada por esta unidade, por ser a primeira
  do app a precisar de decodificação para inferência (distinta da inspeção de metadados de
  formato/duração já resolvida pelo domínio Captura e Ingestão de Áudio).

**Belongs to other domains (cross-domain, does not become a task here):**

- Recebimento de áudio pelos canais CLI e API HTTP e validação de formato e de duração →
  domínio `Captura e Ingestão de Áudio`.
- Rota HTTP e payload exato de sucesso e de cada causa de erro deste domínio → `openapi.yaml`,
  mantido conforme a technical-skill `documentacao-de-api`.

## User stories

1. Como usuário que enviou um áudio em português, quero receber o texto transcrito na mesma
   chamada que originou o envio, para obter o resultado sem depender de consulta posterior.
2. Como usuário que enviou um áudio em um idioma diferente de português, quero ser informado de
   que o idioma detectado não é suportado, para saber que preciso reenviar o áudio em português.
3. Como usuário que enviou um áudio sem fala perceptível, quero receber um erro específico de
   silêncio, distinto de outras causas de falha, para entender o motivo real da falha.
4. Como usuário que enviou um áudio dominado por ruído sem fala identificável, quero receber um
   erro específico de ruído, distinto de silêncio ou de falha interna do motor.
5. Como usuário afetado por uma falha interna do motor de transcrição durante a inferência,
   quero receber um erro específico dessa causa, distinto dos erros de silêncio e de ruído, para
   diferenciar um problema do motor de um problema do próprio áudio.
6. Como usuário que recebeu um resultado (texto ou erro), quero que nenhum dado da minha chamada
   permaneça acessível depois da resposta, para que meu áudio e minha transcrição não fiquem
   disponíveis além do necessário para aquela chamada.

## Acceptance criteria

**Story 1 — Transcrição bem-sucedida em português:**

- Given um áudio já validado quanto a formato e duração pelo domínio Captura e Ingestão de
  Áudio, cujo idioma detectado é português (pt-BR), when o domínio Motor de Transcrição processa
  esse áudio, then ele produz o texto transcrito e o devolve na mesma resposta da chamada de
  origem (CLI ou API HTTP).

**Story 2 — Idioma não suportado:**

- Given um áudio já validado quanto a formato e duração, cujo idioma detectado não é português,
  when o domínio processa esse áudio, then ele rejeita o áudio sem transcrevê-lo e a chamada de
  origem retorna informando que o idioma detectado não é suportado, sem produzir texto
  transcrito.

**Story 3 — Falha por silêncio:**

- Given um áudio no idioma correto (pt-BR) sem fala perceptível, when a transcrição é tentada,
  then o domínio identifica a causa da falha como silêncio e a chamada de origem retorna esse
  erro específico, sem produzir texto transcrito.

**Story 4 — Falha por ruído:**

- Given um áudio no idioma correto dominado por ruído sem fala identificável, when a transcrição
  é tentada, then o domínio identifica a causa da falha como ruído e a chamada de origem retorna
  esse erro específico, distinto do erro de silêncio.

**Story 5 — Falha interna do motor:**

- Given um áudio no idioma correto, when o motor Whisper falha internamente durante a inferência
  por uma causa que não é silêncio nem ruído, then o domínio identifica a causa da falha como
  falha interna do motor e a chamada de origem retorna esse erro específico, distinto dos erros
  de silêncio e de ruído.

**Story 6 — Sem persistência do resultado:**

- Given uma transcrição concluída com sucesso ou com um dos erros identificados, when a resposta
  é entregue pela chamada de origem, then nem o áudio recebido nem o texto transcrito (ou o erro)
  permanecem acessíveis em banco de dados ou em armazenamento de arquivos após essa resposta.
- Given duas chamadas independentes processadas por este domínio, when a segunda é processada,
  then ela não tem acesso a nenhum dado da primeira.

## Cross-domain dependencies

- **`captura-e-ingestao-de-audio`** — entrega a este domínio o áudio já validado quanto a
  formato e duração, por chamada de função em processo (decisão registrada em
  [`../001-captura-e-ingestao-de-audio/plan.md`](../001-captura-e-ingestao-de-audio/plan.md)), e
  repassa o resultado (texto transcrito ou causa do erro) pelo mesmo canal de entrada que
  originou o envio.
- **`documentacao-de-api`** — formaliza no `openapi.yaml` a rota, o payload de sucesso e o
  payload de cada causa de erro deste domínio, no momento em que o endpoint HTTP correspondente
  for implementado; este spec não fixa rota nem formato de payload.

## Risks and observations

- A escolha entre `openai-whisper` e `faster-whisper`, o modelo Whisper específico e a
  biblioteca ou heurística usada para detectar idioma, silêncio e ruído são decisões de
  implementação a resolver em `plan.md` — tanto `functional-map.md` quanto a skill do domínio já
  registram essas escolhas como detalhe de implementação da Fase 2, não como decisão de negócio
  deste spec.
- A precisão da distinção entre silêncio e ruído depende da capacidade de detecção da
  biblioteca/heurística escolhida; casos-limite (fala muito baixa ou parcialmente coberta por
  ruído) ficam sujeitos à decisão técnica registrada em `plan.md`/`research.md`.
- A disponibilidade local dos pesos do modelo Whisper e a capacidade de CPU/GPU da máquina de
  execução são dependências técnicas transversais deste domínio, detalhadas em
  [`../../skills/motor-de-transcricao/references/technical-dependencies.md`](../../skills/motor-de-transcricao/references/technical-dependencies.md);
  o provisionamento desses pesos no ambiente de execução é tratado em `plan.md`.
- Este domínio ainda não existe no código do repositório — mesmo estado greenfield do domínio
  `Captura e Ingestão de Áudio`. A spec cobre a materialização completa do domínio, não um delta
  sobre implementação existente.
