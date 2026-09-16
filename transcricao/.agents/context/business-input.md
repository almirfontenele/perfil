---
name: business-input
description: Registro do pedido original do usuário (app em Python para enviar um áudio e obter a transcrição) e índice de proveniência das evidências consultadas no diretório do projeto-alvo.
metadata:
  author: clovis-cli
  responsibility: Faithful record of the business material provided by the user and an index of provenance and re-access of that material, organized by source. Stage 2 reopens the original sources from here; it does not classify domains, boundaries, dependencies or confidence level.
---

## Material de negócio fornecido pelo usuário

Texto informado no campo de regras de negócio desta sessão, preservado como recebido:

> "quero um app para enviar um audio e fazer a transcrição usando python , faça passo a passo, usando as melhores praticas"

Nenhum caminho de arquivo, URL ou espaço de MCP (Jira, Confluence, Figma etc.) foi indicado junto com o texto. Não há, portanto, documentos externos para reabrir além deste próprio texto.

**Origem:** texto fornecido pelo usuário (sessão de descoberta funcional, campo "Business rules provided by the user").

## Índice de evidências consultadas no diretório do projeto-alvo

### 1. Diretório-raiz do projeto-alvo (`/home/almir`)

- **O que foi verificado:** conteúdo do diretório-raiz (`ls -la`), arquivos rastreados pelo git (`git ls-files`), README.md e ausência de artefatos `.agents/` pré-existentes antes desta rodada.
- **Resultado:** o diretório-raiz é um repositório git pessoal contendo apenas `README.md` (conteúdo: "# perfil") como arquivo rastreado; não há nenhum código, scaffold, documento ou dependência relacionados a envio ou transcrição de áudio diretamente na raiz.
- **Reacesso:** `git -C /home/almir ls-files` e `ls -la /home/almir`.

### 2. Subdiretório `projetos/` (não relacionado ao pedido atual)

- **O que foi verificado:** `find projetos -maxdepth 3`, incluindo os subprojetos `projetos/mba-ia-niv-introducao-langchain`, `projetos/mba-ia-greenfield-project` e `projetos/subagentes/claude-subagents`.
- **Resultado:** são repositórios git independentes (cada um com seu próprio `.git`), de outros exercícios/projetos do usuário, sem relação funcional direta com o pedido de "enviar um áudio e fazer a transcrição". Não foram usados como base de domínio para este app.
- **Reacesso:** `find /home/almir/projetos -maxdepth 3`.

### 3. Evidência técnica adjacente: `projetos/subagentes/claude-subagents` (agente `audio-transcription`)

- **O que foi verificado:** `projetos/subagentes/claude-subagents/.claude/agents/audio-transcription.md`, `projetos/subagentes/claude-subagents/requirements.txt` e `projetos/subagentes/claude-subagents/.agents/maps/functional-map.md`.
- **Resultado:** repositório git próprio e já concluído, com discovery funcional independente já resolvida (`.agents/context/discovery-answers.md`, `.agents/maps/functional-map.md` próprios). Implementa um **agente do Claude Code** que captura áudio do microfone do sistema e transcreve para PT-BR usando `PyAudio` + `openai-whisper` local, com uso e propósito distintos do app solicitado agora (ali o "áudio" é capturado ao vivo do microfone dentro de uma sessão do Claude Code; aqui o pedido é um app que recebe/envia um áudio para transcrição). Por ser um sistema de fronteira própria, com objetivo diferente, não foi tratado como código existente deste projeto nem usado para decidir domínios ou motor de transcrição sem confirmação do usuário — apenas registrado aqui como precedente técnico consultado (ver `gap-2-motor-transcricao` em `functional-map.md`).
- **Reacesso:** `cat /home/almir/projetos/subagentes/claude-subagents/.claude/agents/audio-transcription.md`; `cat /home/almir/projetos/subagentes/claude-subagents/requirements.txt`; `cat /home/almir/projetos/subagentes/claude-subagents/.agents/maps/functional-map.md`.

### 4. Ambientes Python já presentes no diretório-alvo

- **O que foi verificado:** `/home/almir/venv` (virtualenv Python 3.10.12 na raiz) e pacotes instalados via `pip list`.
- **Resultado:** virtualenv existe mas está vazio (nenhum pacote de áudio, transcrição ou framework web instalado). Não há `requirements.txt` nem `pyproject.toml` na raiz do projeto-alvo.
- **Reacesso:** `/home/almir/venv/bin/pip list`; `cat /home/almir/venv/pyvenv.cfg`.

### 5. Framework spec-driven concorrente

- **O que foi verificado:** busca por diretórios/arquivos característicos de frameworks concorrentes (`.specify/`, `openspec/`) na raiz do projeto-alvo.
- **Resultado:** nenhuma evidência encontrada na raiz de `/home/almir`.
- **Reacesso:** `find /home/almir -maxdepth 2 -iname "*.specify*" -o -maxdepth 2 -iname "openspec"`.
