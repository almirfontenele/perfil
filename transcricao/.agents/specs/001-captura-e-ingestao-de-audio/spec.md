# Spec: Captura e Ingestão de Áudio

## Overview

Recebimento do áudio enviado pelo usuário — por CLI ou por API HTTP — com validação obrigatória
de formato e de duração antes de encaminhar o áudio ao domínio Motor de Transcrição, sem
persistir áudio ou resultado em nenhum momento do fluxo.

## Domain

- Slug: `captura-e-ingestao-de-audio`
- Skill: [`.agents/skills/captura-e-ingestao-de-audio/SKILL.md`](../../skills/captura-e-ingestao-de-audio/SKILL.md)

## Scope

**In:**

- Recebimento de áudio por dois canais de entrada: CLI (caminho de um arquivo de áudio local) e
  API HTTP (upload de arquivo via endpoint REST).
- Validação de formato do áudio recebido, aceitando WAV, MP3, M4A, OGG e FLAC e rejeitando
  qualquer outro formato.
- Validação de duração do áudio recebido, aceitando até 10 minutos e rejeitando acima desse
  limite, independentemente do tamanho do arquivo em bytes.
- Encaminhamento do áudio validado ao domínio Motor de Transcrição e devolução do resultado
  (texto transcrito ou motivo de rejeição/falha) de forma síncrona, pelo mesmo canal que originou
  o envio.
- Processamento inteiramente transitório: nenhum áudio recebido — validado ou rejeitado — é
  persistido em banco de dados ou em armazenamento de arquivos.

**Out:**

- Transcrição do áudio em texto, detecção de idioma falado e distinção das causas de falha de
  transcrição — responsabilidade do domínio Motor de Transcrição.
- Qualquer histórico de envios anteriores ou consulta posterior a um envio já concluído — decorre
  da regra de processamento transitório, não há o que implementar aqui.
- Definição do contrato formal (rota, payload de sucesso e de erro) do endpoint HTTP — formalizada
  no `openapi.yaml` durante a implementação, conforme a technical-skill `documentacao-de-api`.

## Domain boundary

**This spec implements:**

- Entidade transitória `Áudio recebido`, identificada por formato/contêiner e por duração,
  existente apenas durante o processamento de uma única chamada.
- Canal de entrada CLI: leitura de um arquivo de áudio a partir de um caminho local informado
  pelo usuário.
- Canal de entrada API HTTP: endpoint REST de upload de arquivo de áudio.
- Regras de validação de formato (WAV, MP3, M4A, OGG, FLAC) e de duração (até 10 minutos),
  aplicadas da mesma forma aos dois canais, antes de qualquer encaminhamento à transcrição.
- Fluxo de encaminhamento do áudio validado ao domínio Motor de Transcrição e de retorno síncrono
  do resultado pelo mesmo canal de entrada.
- Reporte do motivo de rejeição (formato não suportado ou duração excedida) pelo mesmo canal de
  entrada, quando a validação falha.
- Infraestrutura transversal criada por esta unidade, por ser a primeira do app a precisar dela:
  estrutura comum aos dois canais de entrada (CLI e API HTTP), capacidade de inspeção de
  metadados do áudio (formato do contêiner e duração) e manipulação do áudio inteiramente em
  memória/arquivo temporário, sem escrita em armazenamento persistente.

**Belongs to other domains (cross-domain, does not become a task here):**

- Detecção de idioma, transcrição do áudio validado e distinção das causas de falha de
  transcrição (silêncio, ruído, falha interna do motor) → domínio `Motor de Transcrição`.
- Manutenção do contrato OpenAPI (`openapi.yaml`) do endpoint HTTP criado por este domínio →
  technical-skill `documentacao-de-api`, aplicada no momento em que o endpoint é implementado.

## User stories

1. Como usuário do app, quero enviar um áudio local pela CLI informando o caminho do arquivo,
   para receber a transcrição na mesma execução.
2. Como cliente integrado via API, quero enviar um áudio por upload em um endpoint REST, para
   receber a transcrição na mesma chamada.
3. Como usuário do app, quero que o áudio enviado seja validado quanto a formato e duração antes
   de ser transcrito, para saber imediatamente o motivo quando o envio é rejeitado, sem gastar
   processamento de transcrição em um arquivo inválido.
4. Como usuário do app, quero que nenhum áudio enviado — aceito ou rejeitado — fique armazenado
   após a resposta, para que dados de voz não permaneçam disponíveis além do necessário para a
   própria chamada.

## Acceptance criteria

**Story 1 — Envio via CLI:**

- Given um caminho de arquivo de áudio local em um dos formatos aceitos (WAV, MP3, M4A, OGG ou
  FLAC) e com duração de até 10 minutos, when o usuário informa esse caminho pela CLI, then a
  execução permanece bloqueada até a transcrição terminar e devolve o texto transcrito na mesma
  execução.
- Given um caminho de arquivo de áudio em formato fora de WAV, MP3, M4A, OGG e FLAC, when o
  usuário informa esse caminho pela CLI, then o áudio não é encaminhado ao Motor de Transcrição e
  a execução informa que o formato não é suportado.
- Given um caminho de arquivo de áudio com duração acima de 10 minutos, when o usuário informa
  esse caminho pela CLI, then o áudio não é encaminhado ao Motor de Transcrição e a execução
  informa que a duração excede o limite.

**Story 2 — Envio via API HTTP:**

- Given o upload de um arquivo de áudio em um dos formatos aceitos e com duração de até 10
  minutos, when o cliente envia o upload ao endpoint de ingestão de áudio, then a chamada
  permanece bloqueada até a transcrição terminar e a resposta devolve o texto transcrito.
- Given o upload de um arquivo de áudio em formato fora de WAV, MP3, M4A, OGG e FLAC, when o
  cliente envia o upload, then o áudio não é encaminhado ao Motor de Transcrição e a resposta
  informa que o formato não é suportado.
- Given o upload de um arquivo de áudio com duração acima de 10 minutos, when o cliente envia o
  upload, then o áudio não é encaminhado ao Motor de Transcrição e a resposta informa que a
  duração excede o limite.

**Story 3 — Validação antes da transcrição:**

- Given um áudio recebido por qualquer um dos dois canais, when a validação de formato e de
  duração é aplicada, then ela ocorre antes de qualquer encaminhamento ao domínio Motor de
  Transcrição, com o mesmo critério de formato e de duração nos dois canais.
- Given um áudio que falha na validação de formato ou de duração, when a falha é detectada, then
  o domínio Motor de Transcrição não é chamado para esse áudio.

**Story 4 — Sem persistência:**

- Given um áudio recebido, validado ou rejeitado, when a resposta da chamada de origem (CLI ou
  API HTTP) é entregue, then nenhum dado desse áudio permanece em banco de dados ou em
  armazenamento de arquivos após essa resposta.
- Given duas chamadas independentes de envio de áudio, when a segunda chamada é processada, then
  ela não tem acesso a nenhum dado da primeira chamada.

## Cross-domain dependencies

- **`motor-de-transcricao`** — recebe o áudio já validado por este domínio, produz o texto
  transcrito ou identifica a causa de falha de transcrição, e devolve o resultado para ser
  repassado pelo mesmo canal de entrada que originou a chamada.
- **`documentacao-de-api`** — o endpoint HTTP de upload criado por este domínio é refletido no
  `openapi.yaml` no mesmo commit/PR de sua implementação.

## Risks and observations

- A biblioteca de inspeção de metadados de áudio, o framework HTTP e a biblioteca de CLI usados
  para atender este domínio são decisões de implementação a resolver em `plan.md`: tanto
  `functional-map.md` quanto a skill de domínio registram essas escolhas como detalhe de
  implementação da Fase 2, não como decisão de negócio deste spec.
- A rota concreta do endpoint HTTP e o formato exato dos payloads de sucesso e de cada motivo de
  rejeição não são fixados aqui; são formalizados no `openapi.yaml` durante a implementação,
  conforme a technical-skill `documentacao-de-api`.
- Por não haver persistência nem histórico, uma falha transitória na leitura do arquivo local ou
  do upload não tem mecanismo de retry automático dentro deste domínio; repetir o envio é
  responsabilidade de quem chamou (usuário da CLI ou cliente da API).
