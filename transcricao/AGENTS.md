# AGENTS.md

## Visão geral

Este repositório contém um app em Python que recebe um áudio enviado pelo usuário e devolve a
sua transcrição em texto, em português (pt-BR). O áudio pode ser enviado por dois canais de
entrada — CLI (caminho de um arquivo local) e API HTTP (upload via endpoint REST) —, ambos
alimentando o mesmo fluxo de validação, ingestão e transcrição. O processamento é síncrono (a
chamada só retorna quando o texto transcrito estiver pronto) e transitório: nenhum áudio ou
transcrição é persistido após a resposta. A transcrição usa um motor Whisper local (biblioteca
`openai-whisper` ou `faster-whisper`, executado na própria máquina, sem chamada a API remota de
nuvem).

O domínio está mapeado em dois blocos, com dependência de um sobre o outro:

```
Captura e Ingestão de Áudio  →  Motor de Transcrição
```

Detalhes de cada domínio (regras inferidas, evidências, confiança) estão em
`.agents/maps/functional-map.md`; não os repita aqui.

## Stack e estado atual do projeto

Este é um projeto greenfield: no momento a raiz do repositório contém apenas este `AGENTS.md`,
os artefatos de descoberta funcional em `.agents/` e um `venv/` (Python 3.10.12) ainda vazio, sem
nenhum pacote de áudio, transcrição ou framework web instalado. Não há `pyproject.toml`,
`requirements.txt`, código-fonte ou estrutura de diretórios de aplicação ainda.

- **Linguagem obrigatória: Python** — restrição explícita do usuário; nenhuma outra linguagem deve
  ser introduzida no backend.
- A escolha do framework HTTP, da biblioteca de CLI e da biblioteca Whisper específica
  (`openai-whisper` vs. `faster-whisper`) é detalhe de implementação, decidido durante o
  planejamento incremental de cada domínio — não há evidência no repositório para fixá-los aqui.
- Não existem ainda comandos de build, lint ou teste: eles nascem junto com o scaffold da
  aplicação e devem ser registrados neste arquivo (ou em documento referenciado a partir dele)
  quando existirem.
- Não há arquivo de variáveis de ambiente (`.env.example` ou equivalente) no repositório.

## Estrutura do repositório

- `README.md` — identificação mínima do repositório.
- `venv/` — virtualenv Python local, não versionado como parte da aplicação.
- `.agents/context/` — artefatos canônicos da descoberta funcional: `business-input.md` (pedido
  original do usuário e proveniência das evidências) e `discovery-answers.md` (objetivo, escopo,
  restrições e decisões transversais validadas).
- `.agents/maps/` — `functional-map.md`, o mapa dos domínios de negócio (fronteiras, regras
  inferidas, dependências e ordem de implementação sugerida).
- `.agents/skills/` — guarda as *skills* carregadas sob demanda pelo agente, tanto de domínio
  (negócio) quanto técnicas (transversais). O carregamento é dirigido pelo campo `description` do
  frontmatter de cada skill; este arquivo não lista nem indexa skills individualmente.

A estrutura de código da aplicação (módulos, camadas, pacotes) ainda não existe e deve ser
definida ao longo da implementação incremental dos domínios acima.

## Convenções e restrições globais

- **Entrega incremental ("passo a passo")** — a implementação é conduzida em etapas pequenas e
  verificáveis, uma decisão por vez, em vez de um scaffold completo de uma só tacada.
- **Escopo de idioma da transcrição: apenas português (pt-BR)** — nenhum outro idioma é suportado.
- **Sem persistência** — áudio recebido e texto transcrito não são armazenados; o processamento é
  inteiramente transitório.
- **Processamento síncrono** — não há job em background nem consulta de status; a resposta contém
  o texto transcrito.
- **Motor de transcrição local** — Whisper roda na própria máquina; o domínio depende de recursos
  de CPU/GPU locais, não de credenciais ou conectividade com serviços externos.
- **Estratégia de testes: apenas testes unitários.**
- **Observabilidade: logging simples (console/arquivo)** — sem métricas ou tracing estruturado.

## Precedência de fonte de verdade do domínio

- As *skills* locais em `.agents/skills/` são a fonte de verdade autoritativa da documentação de
  domínio deste projeto.
- Antes de implementar qualquer regra de negócio, consulte e leia essa fonte.
- As skills em `.agents/skills/` têm precedência sobre padrões inferidos a partir do código já
  existente.
- Antes de criar ou editar arquivos, ou implementar qualquer funcionalidade, verifique se existe
  uma skill que rege o caso — pela tecnologia, padrão de código ou arquitetura envolvidos, ou pelo
  domínio de negócio, funcionalidade ou módulo em questão — e siga-a antes de agir.

## Writing comments and documentation

Every text that lives in this repository — code comment, docstring, skill, `AGENTS.md`, README,
spec — describes the current state, written for whoever opens the file today knowing neither the
history of the file nor the conversation that produced it.

- **Describe what is, never the transition.** When editing an existing text, rewrite the
  passage from the final result, as if it had always read that way. A sentence that only makes
  sense to someone who saw the previous version — or your own diff — does not belong in the
  file: what changed belongs to the commit message and the pull request description.
- **Negate only to prevent a plausible mistake.** A negation earns its place when a competent
  reader would actually try the alternative and the sentence says why it fails, so it guards a
  future change. Contrast with the previous version, with an alternative nobody would try, or
  with what the code already shows, is noise that costs the reader attention.
- **Prune before finishing the task.** Re-read the texts you created or altered and cut whatever
  fails the two rules above. Wordings such as "no longer", "used to", "is now", "instead of",
  "rather than", "unlike" and "without needing to" are the usual symptoms — keep only the ones
  that survive the second rule.

One exception: when the subject of the text **is** a change — a commit message, a pull request
description, the spec of a maintenance unit, a changelog — the transition is the content. The rule
forbids narrating the *edit of the text*, never the change the text is about.
