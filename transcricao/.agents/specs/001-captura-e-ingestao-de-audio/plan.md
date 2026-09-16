# Plan: Captura e Ingestão de Áudio

## Stack e estrutura

Backend em Python, único domínio implementado até agora no repositório — esta unidade cria o
esqueleto inicial da aplicação (empacotamento e organização de módulos) que as próximas unidades
do projeto (a começar pelo domínio Motor de Transcrição) reutilizam.

```
pyproject.toml                    # dependências: fastapi, uvicorn, mutagen, pytest
app/
  captura_ingestao/
    __init__.py
    cli.py                        # comando de linha de comando (argparse) que recebe o caminho do arquivo de áudio
    api.py                        # rota FastAPI de upload de áudio
    validacao.py                  # regras de formato aceito e de limite de duração
    metadados.py                  # leitura de formato e duração do arquivo via mutagen
tests/
  captura_ingestao/
    test_validacao.py
    test_metadados.py
    test_cli.py
    test_api.py
openapi.yaml                      # contrato HTTP mantido conforme a technical-skill `documentacao-de-api`
```

Os dois canais de entrada (`cli.py`, `api.py`) chamam as mesmas funções de `validacao.py` e
`metadados.py`, para que a regra de formato e de duração seja aplicada de forma idêntica aos dois
canais. Ao validar o áudio com sucesso, o canal chama o domínio Motor de Transcrição por uma
chamada de função em processo — os dois domínios compõem um único app Python (`AGENTS.md`), sem
indício de arquitetura distribuída entre serviços —, e devolve o resultado (texto transcrito ou
motivo de rejeição/falha) na mesma resposta, de forma síncrona.

## Decisões técnicas

- **Framework HTTP do endpoint de upload: FastAPI.** Roda sobre Uvicorn como servidor ASGI, a
  combinação de referência documentada pelo próprio FastAPI para execução da aplicação; não há
  alternativa de servidor ASGI em debate, pois essa combinação é consequência direta da escolha
  do framework, não uma decisão independente. Contexto e alternativas consideradas em
  [`research.md`](./research.md).
- **Biblioteca do canal CLI: `argparse`**, da biblioteca padrão do Python, sem dependência nova.
- **Inspeção de formato e duração do áudio: `mutagen`**, biblioteca pura Python (sem binário
  externo como o FFmpeg), com suporte aos cinco formatos aceitos pelo domínio (WAV, MP3, M4A, OGG
  e FLAC).
- **Encaminhamento ao domínio Motor de Transcrição: chamada de função em processo**, e não uma
  chamada de rede — decorre de os dois domínios formarem um único app Python, sem persistência
  nem processamento assíncrono (`AGENTS.md`, `discovery-answers.md`).

## Modelo de dados

Não aplicável: o domínio não tem entidade persistente nem tabela de banco de dados — a única
entidade, `Áudio recebido`, é transitória e já está descrita no `spec.md`, sem atributos
adicionais, relações, índices ou constraints que justifiquem um `data-model.md` próprio. Artefato
dispensado.

## Contratos externos

O contrato do canal HTTP é formalizado no `openapi.yaml` mantido na raiz do repositório, conforme
a technical-skill [`documentacao-de-api`](../../skills/documentacao-de-api/SKILL.md) — esse
arquivo ainda não existe no repositório e é criado pela primeira task de implementação do
endpoint, com a rota de upload de áudio e os três casos de resposta (transcrição concluída,
formato não suportado, duração excedida). Não é criado um contrato duplicado dentro da pasta
desta unidade (`contracts/`), pois o `openapi.yaml` da raiz já é a única fonte formal do contrato
REST do app; artefato `contracts/` dispensado.

## Interface

Não aplicável: domínio sem interface gráfica. O canal CLI é um canal de entrada de linha de
comando, não uma interface visual — não há tela, formulário ou fluxo a descrever no vocabulário
de `ui/`. Artefato `ui/` dispensado.

## Estratégia de testes

Apenas testes unitários (`discovery-answers.md`); não há teste de integração ou e2e nesta
unidade nem no projeto. `pytest` é o executor adotado — nenhuma dependência de teste existe hoje
no `venv` do repositório, então esta unidade introduz o `pytest` como dependência de
desenvolvimento e a estrutura `tests/captura_ingestao/`.

Cada task que entrega código testável inclui o teste no mesmo commit:

- `validacao.py` — funções puras de validação de formato e de limite de duração, testadas com
  entradas que cobrem os cinco formatos aceitos, formatos rejeitados e duração no limite/acima
  do limite.
- `metadados.py` — leitura de formato e duração via `mutagen`, testada contra arquivos de áudio
  de amostra (fixtures) para cada formato aceito.
- `cli.py` — parsing do argumento de caminho do arquivo e orquestração do fluxo (validação →
  encaminhamento ao Motor de Transcrição), testada com a chamada ao Motor de Transcrição
  substituída por um dublê de teste (mock).
- `api.py` — lógica do handler da rota de upload (validação → encaminhamento), testada como
  função isolada com a chamada ao Motor de Transcrição substituída por um dublê de teste — sem
  subir um servidor HTTP real, o que caracterizaria um teste de integração fora do escopo
  validado para o projeto.

## Impacto na documentação autoritativa

Nenhum. A skill do domínio já descreve o comportamento esperado (dois canais, validação de
formato e duração, encaminhamento síncrono, sem persistência) e as decisões técnicas registradas
aqui (FastAPI, argparse, mutagen, chamada em processo) são detalhe de implementação que não
contradiz nem estende a skill — não há drift deliberado a registrar nem task de atualização de
documentação autoritativa nascendo desta unidade.
