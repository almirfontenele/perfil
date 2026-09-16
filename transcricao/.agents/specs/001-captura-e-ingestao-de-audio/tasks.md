# Tasks: Captura e Ingestão de Áudio

- [ ] **T1. Canal de entrada via CLI, com validação de formato e de duração**
  - Depends on: none
  - Precondition: o domínio Motor de Transcrição precisa estar disponível para produzir o texto
    transcrito a partir do áudio validado; ainda não tem spec gerada neste repositório (ordem de
    implementação sugerida em `functional-map.md`). Nos testes desta task, a chamada a esse
    domínio é substituída por um dublê de teste, conforme `plan.md`.
  - Introduz `pytest` e `mutagen` como dependências do projeto (nenhuma delas está instalada no
    `venv` do repositório) e a estrutura `tests/captura_ingestao/` — nomeado como pré-requisito
    desta task, por ser a primeira a precisar deles.
  - Comando de linha de comando (`argparse`) que recebe como argumento o caminho de um arquivo de
    áudio local (Story 1 do `spec.md`).
  - Validação de formato (WAV, MP3, M4A, OGG, FLAC) e de duração (até 10 minutos, limite
    inclusive) do arquivo informado, usando `mutagen` para inspecionar o próprio arquivo — regra
    de negócio da skill do domínio, aplicada aqui pela primeira vez no projeto.
  - Ao validar com sucesso, encaminha o áudio à função de transcrição exposta pelo domínio Motor
    de Transcrição e devolve o texto transcrito na mesma execução; ao falhar a validação, informa
    o motivo (formato não suportado ou duração excedida) sem chamar a transcrição.
  - Nenhuma escrita em arquivo ou banco de dados durante o fluxo, nem no caminho de sucesso nem
    no de rejeição (Story 4 do `spec.md`).
  - Testes unitários cobrindo TC-1, TC-2, TC-3, TC-7, TC-10, TC-11, TC-12 e TC-13 do
    `test-cases.md`.

- [ ] **T2. Canal de entrada via API HTTP, reaproveitando a validação do canal CLI**
  - Depends on: T1
  - Precondition: mesma do T1 quanto à disponibilidade do domínio Motor de Transcrição; a chamada
    também é substituída por um dublê de teste nos testes desta task.
  - Introduz `fastapi` e `uvicorn` como dependências do projeto — nomeado como pré-requisito
    desta task, por ser a primeira a precisar deles.
  - Endpoint REST de upload de arquivo de áudio (Story 2 do `spec.md`), reaproveitando as mesmas
    funções de validação de formato e de duração e de inspeção de metadados criadas em T1, para
    que o critério aplicado seja idêntico ao do canal CLI.
  - Ao validar com sucesso, encaminha o áudio à mesma função de transcrição usada pelo canal CLI e
    devolve o texto transcrito na mesma resposta; ao falhar a validação, a resposta informa o
    motivo (formato não suportado ou duração excedida) sem chamar a transcrição.
  - Cria o `openapi.yaml` na raiz do repositório (ainda não existe) com a rota deste endpoint e os
    três casos de resposta (transcrição concluída, formato não suportado, duração excedida),
    conforme a technical-skill `documentacao-de-api`.
  - Nenhuma escrita em arquivo ou banco de dados durante o fluxo, nem no caminho de sucesso nem
    no de rejeição (Story 4 do `spec.md`).
  - Testes unitários cobrindo TC-4, TC-5, TC-6, TC-8, TC-9, TC-10, TC-11 e TC-12 do
    `test-cases.md`, incluindo um teste que valida o `openapi.yaml` gerado com
    `openapi-spec-validator` (technical-skill `documentacao-de-api`).
