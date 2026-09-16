---
name: documentacao-de-api
description: >
  Como manter a especificação OpenAPI/Swagger (openapi.yaml) da API HTTP de envio
  e transcrição de áudio sincronizada com o código a cada endpoint REST criado,
  alterado ou removido. Use ao criar ou alterar uma rota HTTP, ao mudar
  request/response de um endpoint, ao adicionar um caso de erro, ao versionar o
  contrato ou ao revisar um pull request que toca a camada HTTP da API.
metadata:
  author: clovis-cli
  type: technical-skill
---

# Documentação de API

> **Manutenção desta skill**
>
> Atualize este documento sempre que o mecanismo de manutenção da especificação
> OpenAPI mudar (por exemplo, o arquivo deixar de ser mantido à mão, ou a
> ferramenta de validação mudar). Uma refatoração que preserva o padrão não
> exige alteração.

## Visão geral do padrão e do problema que resolve

O app expõe um canal de API HTTP para envio de áudio e recebimento da
transcrição, ao lado do canal CLI (domínio `Captura e Ingestão de Áudio`). O
contrato desse canal REST é documentado em uma especificação OpenAPI 3.x
escrita e mantida à mão — não gerada automaticamente a partir do framework HTTP
—, o que a torna suscetível a divergir do código real caso a atualização da
especificação não acompanhe cada mudança de rota. Este padrão existe para
fixar a disciplina que evita essa divergência: nenhuma criação, alteração ou
remoção de endpoint REST é considerada concluída sem a atualização
correspondente da especificação.

## Como aplicar

- **Arquivo único de especificação:** `openapi.yaml`, na raiz do repositório,
  em OpenAPI 3.x/YAML. É a única fonte formal do contrato REST do app,
  independente de qual framework HTTP venha a ser escolhido para o canal de
  API do domínio `Captura e Ingestão de Áudio`.
- **Atualização no mesmo commit/PR:** qualquer mudança que toque uma rota REST
  — endpoint novo, schema de request/response alterado, código de status ou
  caso de erro novo, endpoint removido — atualiza o `openapi.yaml` na mesma
  mudança que altera o código, nunca em um commit posterior.
- **Estrutura do arquivo:** seções padrão do OpenAPI 3.x — `info` (título,
  versão, descrição), `paths` (uma entrada por endpoint, com parâmetros,
  `requestBody` e `responses`, incluindo os casos de erro) e
  `components/schemas` (modelos reutilizáveis, por exemplo os payloads de
  requisição de transcrição e de resposta com o texto transcrito, e o payload
  de erro). Schemas reutilizados entre endpoints ficam em
  `components/schemas` e são referenciados via `$ref`, nunca duplicados
  inline em cada endpoint.
- **Versão do contrato:** o campo `info.version` reflete o estado atual do
  contrato — incrementa sempre que um endpoint documentado muda de forma
  incompatível (campo removido, tipo alterado, endpoint removido). O projeto
  ainda não registrou um esquema fixo de versionamento (semver ou outro); até
  que isso seja decidido, o campo apenas precisa continuar coerente com o que
  o contrato descreve no momento da mudança.
- **Validação automatizada:** um teste unitário — a estratégia de testes do
  projeto é testes unitários apenas — carrega o `openapi.yaml` e o valida
  estruturalmente com a biblioteca `openapi-spec-validator`. Esse teste falha
  a suíte quando o arquivo fica malformado ou incompleto, sem precisar subir
  um servidor real nem de um framework de contract testing.
- **Checklist de revisão:** ao revisar um pull request que toca um endpoint
  REST, confirmar que o `openapi.yaml` foi atualizado e que os
  parâmetros, tipos, códigos de status e payloads de erro descritos batem com
  o código.

## Ferramentas e artefatos envolvidos

- `openapi.yaml` — especificação OpenAPI 3.x mantida à mão, na raiz do
  repositório; fonte única do contrato REST do app.
- `openapi-spec-validator` — pacote Python usado a partir de um teste unitário
  para validar estruturalmente o `openapi.yaml` a cada execução da suíte.
- Um visualizador de Swagger UI/Redoc para renderizar o `openapi.yaml` para
  humanos é opcional e, quando adotado, é servido pelo framework HTTP
  escolhido para o canal de API do domínio `Captura e Ingestão de Áudio` — a
  escolha desse framework é detalhe de implementação definido durante o
  planejamento desse domínio, não por esta skill.

## Restrições e armadilhas conhecidas

- Não substituir o `openapi.yaml` mantido à mão por uma especificação gerada
  automaticamente pelo framework HTTP escolhido (por exemplo, a partir de
  type hints de rotas): manter as duas fontes ao mesmo tempo cria dois
  contratos que podem divergir entre si.
- Não documentar apenas o caminho feliz: cada endpoint documentado inclui
  também os seus casos de erro (formato de áudio não suportado, áudio fora do
  limite de tamanho/duração, falha interna de transcrição), já que o domínio
  `Captura e Ingestão de Áudio` valida o áudio antes de encaminhá-lo à
  transcrição.
- O `openapi.yaml` documenta exclusivamente o canal de API HTTP; o canal CLI
  do mesmo domínio não faz parte deste contrato.
- Como o processamento é síncrono, a especificação não descreve endpoints de
  status/polling: a resposta de cada endpoint documentado devolve o texto
  transcrito diretamente na mesma chamada.
