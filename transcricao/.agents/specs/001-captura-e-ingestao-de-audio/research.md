# Research: Captura e Ingestão de Áudio

## Framework HTTP do endpoint de upload

**Contexto.** O canal de API HTTP precisa de um framework que exponha o endpoint de upload de
áudio e devolva a resposta síncrona (texto transcrito ou motivo de rejeição). O repositório é
greenfield: não há framework HTTP em uso no código.

**Alternativas:**

- **FastAPI** — tipagem nativa (Pydantic) para validação de request/response e geração
  automática de esquema compatível com OpenAPI, útil para manter o `openapi.yaml` alinhado ao
  código.
- **Flask** — minimalista, sem geração automática de esquema; a validação de payload e a
  documentação OpenAPI seriam inteiramente manuais.
- **Servidor HTTP da biblioteca padrão (`http.server`)** — sem dependência externa, mas exige
  implementar manualmente roteamento, parsing de upload multipart e serialização de resposta.

**Decisão:** FastAPI, executado sobre Uvicorn como servidor ASGI — a combinação padrão
recomendada pela própria documentação do FastAPI para servir a aplicação; não há alternativa de
servidor ASGI em aberto, pois essa é uma consequência direta da escolha do framework, e não uma
decisão independente com paradigmas concorrentes.

**Base de confirmação:** confirmado pelo usuário (resposta ao gap `gap-9-framework-http`).

**Consequências:** `fastapi` e `uvicorn` entram como dependências do projeto; a validação de
request/response do endpoint de upload usa os modelos do FastAPI (Pydantic), e o esquema gerado
pelo framework serve de apoio à redação manual do `openapi.yaml` (que continua sendo a fonte
formal do contrato, conforme a technical-skill `documentacao-de-api`).

## Biblioteca do canal CLI

**Contexto.** O canal CLI precisa ler um caminho de arquivo informado pelo usuário e aplicar o
mesmo fluxo de validação e encaminhamento do canal HTTP.

**Alternativas:**

- **`argparse`** — biblioteca padrão do Python, sem dependência nova; suficiente para um único
  argumento posicional (caminho do arquivo).
- **Click** — biblioteca dedicada de CLI, com decoradores e utilitários de teste; adiciona uma
  dependência para um comando de superfície pequena.
- **Typer** — biblioteca dedicada baseada em type hints; mesma observação de Click.

**Decisão:** `argparse`.

**Base de confirmação:** confirmado pelo usuário (resposta ao gap `gap-10-biblioteca-cli`).

**Consequências:** nenhuma dependência nova para o canal CLI; o comando é definido diretamente
com `argparse.ArgumentParser` em `cli.py`.

## Inspeção de formato e duração do áudio

**Contexto.** A validação de formato e de duração (regras 3 e 4 da skill do domínio) depende de
ler, a partir do arquivo recebido por qualquer um dos dois canais, qual é o seu
formato/contêiner e qual é a sua duração.

**Alternativas:**

- **`mutagen`** — biblioteca pura Python, sem dependência de binário externo; lê metadados dos
  cinco formatos aceitos pelo domínio (WAV, MP3, M4A, OGG, FLAC).
- **`pydub`** — requer o binário externo FFmpeg instalado no ambiente para decodificar a maioria
  dos formatos, além da dependência Python.
- **`ffprobe` via `subprocess`** — usa o FFmpeg diretamente pela linha de comando, sem biblioteca
  Python dedicada; acopla a validação a um binário externo e ao parsing da sua saída.

**Decisão:** `mutagen`.

**Base de confirmação:** confirmado pelo usuário (resposta ao gap `gap-11-inspecao-metadados-audio`).

**Consequências:** `mutagen` entra como dependência do projeto; a validação de formato e de
duração não depende de nenhum binário externo instalado no ambiente de execução.

## Executor de testes

**Contexto.** `discovery-answers.md` valida testes unitários como única estratégia de testes do
projeto, sem nomear o executor. O `venv` do repositório ainda não tem nenhuma dependência de
teste instalada.

**Alternativas:**

- **`pytest`** — executor dedicado, com fixtures e plugins do ecossistema Python.
- **`unittest`** — biblioteca padrão do Python, sem dependência nova.

**Decisão:** `pytest`.

**Base de confirmação:** confirmado pelo usuário (resposta ao gap `gap-12-runner-testes`).

**Consequências:** `pytest` entra como dependência de desenvolvimento do projeto; vale para os
testes desta e das demais unidades, não apenas para este domínio.
