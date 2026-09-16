# Plan: Motor de Transcrição

## Stack e estrutura

Backend em Python (`AGENTS.md`), segundo domínio implementado no repositório. Reutiliza o
esqueleto de aplicação criado pela unidade `captura-e-ingestao-de-audio`
([`../001-captura-e-ingestao-de-audio/plan.md`](../001-captura-e-ingestao-de-audio/plan.md)):
mesmo `pyproject.toml` na raiz e mesma organização de pacotes sob `app/`.

```
pyproject.toml                    # acrescenta dependência: openai-whisper (traz torch, numpy,
                                   # tiktoken, numba e tqdm como dependências transitivas)
app/
  captura_ingestao/                # já descrito no plan.md da unidade 001
  motor_transcricao/
    __init__.py
    transcricao.py                 # ponto de entrada do domínio: decodifica o áudio, detecta o
                                    # idioma, transcreve e monta o resultado (texto ou erro)
    classificacao_falha.py         # heurística de energia do áudio combinada aos sinais nativos
                                    # do Whisper para distinguir silêncio de ruído
tests/
  motor_transcricao/
    test_transcricao.py
    test_classificacao_falha.py
```

`transcricao.py` expõe uma única função de orquestração, chamada em processo pelo domínio
Captura e Ingestão de Áudio (`cli.py` e `api.py`, decisão registrada no `plan.md` da unidade
001) logo após a validação de formato e duração ser concluída com sucesso.

## Decisões técnicas

- **Biblioteca de transcrição: `openai-whisper`.** Executada localmente, sem chamada a serviço
  remoto. A biblioteca decodifica o áudio recebido (WAV, MP3, M4A, OGG, FLAC) internamente via
  `whisper.load_audio()`, que invoca o binário externo `ffmpeg` — presente no `PATH` do ambiente
  de execução —, satisfazendo a infraestrutura de decodificação de áudio para inferência
  registrada como fronteira deste domínio no `spec.md`. Contexto e alternativas em
  [`research.md`](./research.md).
- **Modelo Whisper: `base`.** Carregado via `whisper.load_model("base")`; os pesos do modelo são
  baixados automaticamente para o cache local na primeira execução — comportamento padrão da
  biblioteca —, o que satisfaz a dependência de disponibilidade local dos pesos sem exigir uma
  etapa de provisionamento própria desta unidade. Contexto e alternativas em
  [`research.md`](./research.md).
- **Detecção de idioma: mecanismo nativo do `openai-whisper`.** A partir do espectrograma mel do
  áudio decodificado, `model.detect_language()` retorna a distribuição de probabilidade entre
  idiomas; o domínio transcreve apenas quando `pt` é o idioma de maior probabilidade e rejeita o
  áudio, sem transcrever, em qualquer outro resultado — reflete a regra 2 da skill do domínio.
- **Classificação da falha de transcrição: sinais nativos do Whisper combinados com energia do
  áudio bruto.** Quando o idioma detectado é português mas a transcrição não produz texto, a
  causa é determinada por:
  - energia (RMS) do áudio decodificado abaixo de um limiar mínimo → causa **silêncio**;
  - energia acima desse limiar, mas `no_speech_prob` alto e confiança média baixa em todos os
    segmentos retornados pela transcrição → causa **ruído**;
  - qualquer exceção não coberta pelos dois casos acima, levantada pela biblioteca durante a
    chamada de inferência → causa **falha interna do motor**.

  Os limiares de energia e de `no_speech_prob`/confiança são calibrados durante a implementação
  com áudios de amostra representativos de cada causa (ver "Riscos e observações"). Contexto e
  alternativas em [`research.md`](./research.md).
- **Contrato de retorno interno.** `transcricao.py` devolve um resultado com exatamente um de
  dois formatos: o texto transcrito, ou uma causa de erro entre `idioma_nao_suportado`,
  `silencio`, `ruido` e `falha_interna_motor` — as quatro causas distinguíveis exigidas pela
  skill do domínio. O domínio Captura e Ingestão de Áudio traduz esse resultado para a resposta
  do canal de entrada que originou a chamada (CLI ou API HTTP); o formato exato de cada payload
  de resposta é decisão do `openapi.yaml` (technical-skill `documentacao-de-api`), não deste
  módulo.

## Modelo de dados

Não aplicável: sem entidade persistente nem tabela de banco de dados — decorre diretamente da
regra de não persistência do texto transcrito, já registrada no `spec.md`. A única saída deste
domínio (texto transcrito ou causa do erro) é transitória e está descrita no "Contrato de
retorno interno" acima, sem atributos, relações, índices ou constraints que justifiquem um
`data-model.md` próprio. Artefato dispensado.

## Contratos externos

Não aplicável a este domínio diretamente: o contrato HTTP é formalizado no `openapi.yaml`
mantido pelo domínio Captura e Ingestão de Áudio, conforme a technical-skill
[`documentacao-de-api`](../../skills/documentacao-de-api/SKILL.md). Este domínio contribui para
esse contrato apenas com as causas de erro que precisam ser distinguíveis nos payloads de
resposta (idioma não suportado, silêncio, ruído, falha interna do motor); não cria um contrato
duplicado dentro da pasta desta unidade. Artefato `contracts/` dispensado.

## Interface

Não aplicável: domínio sem interface gráfica nem canal de entrada próprio — recebe o áudio já
validado por chamada de função em processo, sem tela, formulário ou fluxo a descrever no
vocabulário de `ui/`. Artefato `ui/` dispensado.

## Estratégia de testes

Apenas testes unitários (`discovery-answers.md`), com `pytest` como executor — decisão já
tomada para o projeto como um todo em
[`../001-captura-e-ingestao-de-audio/research.md`](../001-captura-e-ingestao-de-audio/research.md),
reaproveitada aqui sem reabrir a escolha.

Cada task que entrega código testável inclui o teste no mesmo commit:

- `classificacao_falha.py` — função pura que recebe a energia do áudio e os sinais de
  `no_speech_prob`/confiança e devolve uma das quatro causas de erro; testada com entradas
  sintéticas que cobrem cada causa e os limiares de decisão, sem depender do modelo Whisper
  carregado.
- `transcricao.py` — orquestração (decodificação → detecção de idioma → transcrição →
  classificação de resultado), testada com a chamada ao modelo Whisper substituída por um dublê
  de teste (mock) que devolve idioma, texto e sinais de confiança controlados; cobre os cinco
  cenários do `spec.md` (sucesso em português, idioma não suportado, silêncio, ruído, falha
  interna do motor) sem carregar o modelo real, o que tornaria a suíte lenta e dependente de
  hardware.
- A decodificação de áudio via `whisper.load_audio()` (FFmpeg) é exercida indiretamente pelos
  testes de `transcricao.py` com arquivos de amostra (fixtures) nos formatos aceitos, sem subir
  nenhum serviço — mantém a suíte inteiramente de testes unitários, sem introduzir teste de
  integração ou e2e.

## Impacto na documentação autoritativa

Nenhum. A skill do domínio já descreve o comportamento esperado (detecção de idioma, motor local,
processamento síncrono, quatro causas distinguíveis de erro, sem persistência) e as decisões
técnicas registradas aqui (`openai-whisper`, modelo `base`, heurística de classificação de
silêncio/ruído) são detalhe de implementação que não contradiz nem estende a skill — não há
drift deliberado a registrar nem task de atualização de documentação autoritativa nascendo desta
unidade.

## Artefatos opcionais

- `data-model.md` — dispensado (ver "Modelo de dados" acima).
- `research.md` — gerado: as três decisões técnicas desta unidade (biblioteca de transcrição,
  modelo Whisper, heurística de classificação de silêncio/ruído) não tinham base firme em
  nenhuma fonte do projeto e exigiram confirmação humana.
- `contracts/` — dispensado (ver "Contratos externos" acima).
- `ui/` — dispensado (ver "Interface" acima).

## Riscos e observações

- Os limiares de energia (RMS) e de `no_speech_prob`/confiança que separam silêncio de ruído são
  calibrados durante a implementação, com áudios de amostra representativos de cada causa; casos-
  limite (fala muito baixa, parcialmente coberta por ruído) podem exigir ajuste desses limiares
  após os primeiros testes com áudio real.
- `ffmpeg` é uma dependência de sistema (binário externo), não uma dependência Python instalável
  via `pyproject.toml`; sua ausência no ambiente de execução impede a decodificação de qualquer
  formato além de WAV/PCM já decodificado, mesmo com `openai-whisper` instalado.
- O modelo `base` equilibra velocidade e acurácia para o processamento síncrono deste domínio;
  uma necessidade futura de maior acurácia ou de menor latência é uma troca de modelo
  (`tiny`/`small`/`medium`/`large`), não uma mudança de arquitetura.
- O download automático dos pesos do modelo na primeira execução exige conectividade de rede
  disponível nesse momento específico; ambientes sem acesso à internet precisam pré-provisionar
  o cache local do Whisper antes da primeira transcrição — preocupação operacional de
  implantação, fora do código deste domínio.
