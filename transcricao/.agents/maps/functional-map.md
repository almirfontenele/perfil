---
name: functional-map
description: Mapa consolidado dos domínios do app de envio e transcrição de áudio em Python — dois domínios com confiança alta (Captura e Ingestão de Áudio; Motor de Transcrição), sem gaps abertos após a rodada de validação humana.
metadata:
  author: clovis-cli
  responsibility: "Map of identification of the business domains (bounded contexts), their boundaries, dependencies and suggested implementation order. Index of domains for skill generation and the spec-driven flow; it does not detail business rules nor duplicate the cross-cutting decisions, which live in the discovery-answers.md."
---

## Domínios identificados

### 1. Captura e Ingestão de Áudio

**Objetivo de negócio:** receber o áudio enviado pelo usuário — por CLI ou por API HTTP — e validá-lo (formato, tamanho/duração) antes de encaminhá-lo para transcrição.

**Evidência:**
- Evidência no material fornecido: texto do usuário — "enviar um audio" (campo de regras de negócio desta sessão, registrado em `business-input.md`).

**Regras inferidas:**
- O app aceita o áudio por dois canais de entrada: CLI (caminho de um arquivo de áudio local) e API HTTP (upload de arquivo via endpoint REST) — validado: `gap-1-interface-envio`. Os dois canais alimentam o mesmo fluxo de validação e ingestão; não constituem domínios separados, pois não carregam regra de negócio distinta entre si — apenas pontos de entrada diferentes para a mesma captura.
- É necessário validar o áudio recebido (formato e limites) antes de transcrever.
- O processamento é transitório: nenhum áudio recebido é persistido em banco de dados ou armazenamento de arquivos — validado: `gap-4-persistencia`.

**Dependências entre domínios:** nenhuma (ponto de entrada do fluxo).

**Dependências técnicas do domínio:**
- **Canal duplo de entrada (CLI + API HTTP)** — sem ele, o app só atenderia a um tipo de cliente (ou só linha de comando, ou só integrações via rede); a biblioteca/framework específico de cada canal é detalhe de implementação a ser definido na Fase 2 (plan/tasks), não altera a fronteira deste domínio.
- **Ausência de banco de dados/armazenamento de arquivos** — decisão validada (`gap-4-persistencia`); o domínio não precisa de infraestrutura de persistência para operar.

**Confiança:** high — mecanismo de entrada e política de persistência validados pelo usuário.

---

### 2. Motor de Transcrição

**Objetivo de negócio:** converter o áudio recebido em texto transcrito em português (pt-BR), de forma síncrona, usando Python.

**Evidência:**
- Evidência no material fornecido: texto do usuário — "fazer a transcrição usando python" (campo de regras de negócio desta sessão, registrado em `business-input.md`).

**Regras inferidas:**
- Recebe o áudio validado pelo domínio de Captura e Ingestão de Áudio.
- Transcreve exclusivamente para português (pt-BR) — validado: `gap-5-idiomas`.
- Processa de forma síncrona: a chamada que envia o áudio só retorna quando o texto transcrito estiver pronto, sem job em background nem consulta de status posterior — validado: `gap-3-processamento-sincrono-assincrono`.
- Não persiste o texto transcrito — decorre da decisão de processamento transitório (`gap-4-persistencia`, ver domínio 1): o texto é devolvido na resposta e não é armazenado.

**Dependências entre domínios:**
- `Captura e Ingestão de Áudio` (recebe o áudio já validado como entrada).

**Dependências técnicas do domínio:**
- **Whisper local** (biblioteca `openai-whisper` ou `faster-whisper`, executado na própria máquina, sem chamada a API remota) — validado: `gap-2-motor-transcricao`. Sem essa biblioteca, o domínio não tem como converter áudio em texto. A escolha entre `openai-whisper` e `faster-whisper` é detalhe de implementação a ser definido na Fase 2.
- Execução local implica dependência de recursos de CPU/GPU da própria máquina para inferência do modelo Whisper, e não de credenciais ou conectividade com serviços externos de nuvem.

**Confiança:** high — motor de transcrição, idioma e modelo de processamento validados pelo usuário.

---

## Dependências entre domínios

```
Captura e Ingestão de Áudio
        ↓
Motor de Transcrição
```

## Gaps abertos

Nenhum. Todas as decisões arquiteturais identificadas na rodada anterior (canal de envio, motor de transcrição, processamento síncrono/assíncrono, persistência, idiomas suportados) foram validadas pelo usuário e incorporadas nos blocos de domínio acima. As decisões transversais de testes, observabilidade e documentação estão registradas em `discovery-answers.md` e não alteram a fronteira dos domínios.
