---
name: discovery-answers
description: Objetivo, escopo, restrições declaradas e decisões transversais validadas (canal de envio, motor de transcrição, processamento síncrono, sem persistência, apenas pt-BR, testes unitários, logging simples, documentação via OpenAPI/Swagger) do app de envio e transcrição de áudio em Python; nenhum gap permanece aberto.
metadata:
  author: clovis-cli
  responsibility: "Durable memory of the functional-discovery context and decisions: objective, scope, declared restrictions, validated cross-cutting decisions (with destination), documentation forms to maintain and the log of human decisions resolved in the gap loop. Source re-read by the following stages; its restrictions take precedence over later inferences."
---

## Objetivo e escopo

- **Objetivo:** construir um app em Python que recebe um áudio enviado pelo usuário e produz a sua transcrição em texto, desenvolvido de forma incremental ("passo a passo") e seguindo boas práticas de engenharia.
- **Escopo desta rodada:** projeto greenfield, sistema do tipo backend, escopo declarado "whole project" sobre o diretório-alvo `/home/almir`.
- **Estado do diretório-alvo:** raiz de um repositório git pessoal, sem nenhum scaffold, código ou dependência relacionados a este app antes desta rodada (ver `business-input.md`, seção 1 e 4).

## Restrições declaradas pelo usuário

- **Linguagem de implementação: Python** — restrição explícita ("usando python"). Regra curta e estável → convenção a ser registrada no `AGENTS.md` na Fase 2 (linguagem obrigatória do backend).
- **Abordagem de entrega: passo a passo** — o usuário pediu explicitamente que a implementação seja conduzida em etapas incrementais. Regra curta e estável → convenção de processo a ser registrada no `AGENTS.md` na Fase 2 (guiar a geração de specs/tasks em incrementos pequenos e verificáveis).
- **Uso de boas práticas** — pedido explícito e genérico; detalhado pelas decisões transversais validadas abaixo (testes, observabilidade, documentação).
- Nenhuma outra restrição (stack alvo, áreas críticas, requisito regulatório, contrato a preservar) foi declarada pelo usuário.

## Formas de documentação a manter

- **OpenAPI/Swagger** — validado (`gap-8-documentacao`). Não havia convenção de documentação já adotada no diretório-alvo antes desta decisão (ver `business-input.md`, seção 1). Destino: technical-skill `documentacao-de-api` (Fase 2 mantém a especificação OpenAPI/Swagger da API HTTP).

## Decisões transversais validadas

| Decisão | Resposta validada | Destino |
|---|---|---|
| Canal de envio do áudio | CLI e API HTTP (ambos) | Domínio `Captura e Ingestão de Áudio` (functional-map.md) |
| Motor de transcrição | Whisper local (biblioteca `openai-whisper` ou `faster-whisper`, execução na própria máquina) | Domínio `Motor de Transcrição` (functional-map.md) |
| Modelo de processamento | Síncrono (resposta imediata com o texto transcrito) | Domínio `Motor de Transcrição` (functional-map.md) |
| Persistência | Processamento transitório, sem persistência de áudio ou transcrição | Domínio `Captura e Ingestão de Áudio` (functional-map.md) |
| Idiomas suportados | Apenas português (pt-BR) | Domínio `Motor de Transcrição` (functional-map.md) |
| Estratégia de testes | Testes unitários apenas | Regra curta e estável → convenção no `AGENTS.md` (Fase 2) |
| Estratégia de observabilidade | Logging simples (console/arquivo) | Regra curta e estável → convenção no `AGENTS.md` (Fase 2) |
| Documentação adicional | OpenAPI/Swagger | Technical-skill `documentacao-de-api` (Fase 2) |

## Framework spec-driven concorrente

Nenhuma evidência de framework spec-driven concorrente (ex.: Spec Kit, OpenSpec) foi encontrada na raiz do diretório-alvo `/home/almir` (ver `business-input.md`, seção 5). Nenhuma ação necessária.

## Log de decisões humanas (gaps resolvidos)

- **gap-1-interface-envio** — Pergunta: como o áudio seria "enviado" ao app (API HTTP, CLI ou ambos). Decisão: **ambos** — o app aceita áudio tanto por CLI (caminho de arquivo local) quanto por API HTTP (upload via endpoint REST).
- **gap-2-motor-transcricao** — Pergunta: qual motor/biblioteca de transcrição usar (Whisper local vs. API em nuvem). Decisão: **Whisper local**, via `openai-whisper` ou `faster-whisper`, executado na própria máquina.
- **gap-3-processamento-sincrono-assincrono** — Pergunta: processamento síncrono ou assíncrono. Decisão: **síncrono** — o app responde com o texto transcrito na mesma chamada, sem mecanismo de status/job em background.
- **gap-4-persistencia** — Pergunta: persistir áudio/transcrição para histórico ou processamento transitório. Decisão: **transitório, sem persistência** — nenhum áudio ou transcrição é armazenado após a resposta.
- **gap-5-idiomas** — Pergunta: suportar apenas português ou multilíngue. Decisão: **apenas português (pt-BR)**.
- **gap-6-estrategia-testes** — Pergunta: qual estratégia de testes adotar. Decisão: **testes unitários apenas**.
- **gap-7-observabilidade** — Pergunta: observabilidade simples ou estruturada (métricas/tracing). Decisão: **logging simples (console/arquivo)**.
- **gap-8-documentacao** — Pergunta: manter alguma forma extra de documentação. Decisão: **OpenAPI/Swagger**.

Todos os gaps identificados na rodada anterior foram resolvidos nesta rodada; não há gaps abertos.
