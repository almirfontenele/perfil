---
name: motor-de-transcricao
description: >
  Esta é a documentação autoritativa do domínio Motor de Transcrição: como o app converte, de
  forma síncrona, o áudio já validado pelo domínio Captura e Ingestão de Áudio em texto
  transcrito em português (pt-BR), usando o motor Whisper local (sem chamada a API remota) e
  sem persistir o texto resultante. Use ao implementar a conversão de áudio em texto, o motor
  Whisper, a transcrição em pt-BR, ou o retorno síncrono do texto transcrito na resposta da
  chamada.
metadata:
  author: clovis-cli
  type: domain-skill
---

# Motor de Transcrição

> **Manutenção desta skill**
>
> Atualize este documento sempre que o comportamento deste domínio mudar de propósito, mantendo
> a skill fiel ao comportamento implementado. Uma mudança deliberada no código, com decisão
> registrada, atualiza a skill. Uma divergência semântica entre esta skill e o código, sem
> decisão registrada que a resolva, é escalada para decisão humana — nunca ajustada aqui de
> forma unilateral.

## Visão geral do domínio

Este domínio converte em texto o áudio que o domínio Captura e Ingestão de Áudio já validou e
entregou a ele. É o segundo e último passo do fluxo do app: não recebe áudio diretamente do
usuário (nem por CLI, nem por API HTTP) e não realiza validação própria de formato ou de
duração — essa validação já foi concluída pelo domínio anterior antes de o áudio chegar aqui. A
transcrição é feita localmente, na própria máquina, por um motor Whisper, exclusivamente para
português (pt-BR), de forma síncrona: a chamada que originou o envio do áudio permanece
bloqueada até o texto transcrito estar pronto, e esse texto é devolvido na mesma resposta, sem
job em background nem consulta de status posterior. Nenhum texto transcrito é persistido depois
da resposta.

## Regras de negócio

1. **Entrada exclusiva: áudio já validado.** Este domínio só recebe áudio que o domínio Captura
   e Ingestão de Áudio já validou quanto a formato e duração. Ele não valida formato nem duração
   por conta própria — essa é uma responsabilidade exclusiva do domínio anterior.
2. **Detecção de idioma e transcrição exclusiva para português (pt-BR).** Antes de transcrever,
   o domínio detecta o idioma falado no áudio recebido. Quando o idioma detectado é português
   (pt-BR), a transcrição é produzida normalmente. Quando o idioma detectado não é português, o
   domínio rejeita o áudio e não o transcreve; o app não suporta transcrição multilíngue nem
   transcrição forçada de áudio falado em outro idioma.
3. **Motor local, sem chamada a serviço remoto.** A transcrição é feita por um motor Whisper
   executado na própria máquina (biblioteca `openai-whisper` ou `faster-whisper`), sem enviar o
   áudio a nenhuma API de transcrição em nuvem.
4. **Processamento síncrono.** A chamada que enviou o áudio (pelo canal CLI ou pela API HTTP)
   permanece bloqueada até a transcrição terminar; o texto transcrito é devolvido na mesma
   resposta. Não existe mecanismo de job em background, fila de processamento nem endpoint de
   consulta de status.
5. **Sem persistência do texto transcrito.** Nenhum texto produzido por este domínio é
   armazenado em banco de dados ou em arquivo após a resposta à chamada de origem. Cada
   transcrição é independente; não há histórico de transcrições anteriores.
6. **Falha de transcrição distinguida por causa.** Quando o áudio recebido está no idioma correto
   mas a transcrição não pode ser concluída normalmente, o domínio distingue a causa entre pelo
   menos três categorias: áudio sem fala perceptível (silêncio), áudio dominado por ruído sem
   fala identificável, e falha interna do motor de transcrição durante a inferência. Cada
   categoria é reportada de forma distinta pelo mesmo canal de entrada que originou a chamada; o
   domínio não reporta um único erro genérico para todas elas.
7. **Fronteira de saída do fluxo.** Este domínio é o ponto final do fluxo do app: ao concluir a
   transcrição (ou falhar em concluí-la), o resultado é devolvido pelo mesmo canal de entrada
   (CLI ou API HTTP) que recebeu o áudio originalmente; este domínio não encaminha o resultado a
   nenhum outro domínio.

## Fluxos e ciclo de vida

- **Recebimento do áudio validado:** o domínio Captura e Ingestão de Áudio entrega a este
  domínio o áudio já validado (formato aceito e duração dentro do limite). A chamada de origem
  (CLI ou HTTP) permanece bloqueada a partir deste ponto.
- **Detecção de idioma:** o domínio detecta o idioma falado no áudio recebido antes de
  transcrever.
- **Idioma detectado diferente de português:** o domínio rejeita o áudio e não o transcreve; a
  chamada de origem retorna informando que o idioma detectado não é suportado, sem produzir texto
  transcrito.
- **Idioma detectado é português — transcrição:** o motor Whisper local processa o áudio e
  produz o texto transcrito em português (pt-BR), sem chamada a serviço externo em tempo de
  execução.
- **Falha ao transcrever um áudio no idioma correto:** quando a transcrição não pode ser
  concluída, o domínio identifica a causa entre silêncio (áudio sem fala perceptível), ruído
  (áudio dominado por ruído sem fala identificável) ou falha interna do motor durante a
  inferência, e retorna pela chamada de origem um erro específico para a causa identificada, sem
  produzir texto transcrito.
- **Retorno do resultado com sucesso:** o texto transcrito é devolvido na mesma resposta da
  chamada de origem (CLI ou API HTTP); a chamada só retorna neste momento.
- **Encerramento sem estado remanescente:** depois de a resposta ser entregue — com texto
  transcrito ou com erro —, nem o áudio recebido nem o texto transcrito continuam disponíveis em
  nenhum lugar; não há consulta posterior ao resultado de uma chamada já concluída.

## Entidades e dados

- **Texto transcrito** — saída deste domínio quando a transcrição é concluída com sucesso. É
  transitória: existe apenas durante o processamento de uma única chamada e não é armazenada em
  nenhum momento do fluxo.
- **Erro de transcrição** — saída deste domínio quando a transcrição não é concluída, com uma
  causa entre: idioma detectado diferente de português, áudio sem fala perceptível (silêncio),
  áudio dominado por ruído sem fala identificável, ou falha interna do motor de transcrição
  durante a inferência. Também é transitório, devolvido apenas na resposta da chamada de origem.
- Não há entidade persistente nem tabela de banco de dados neste domínio — decorre diretamente
  da regra de não persistência do texto transcrito.
- O contrato do canal HTTP (rota, payload de resposta com o texto transcrito e payloads de cada
  causa de erro) é formalizado na especificação OpenAPI mantida para a API do app; este domínio
  não fixa aqui a rota nem o formato exato do payload, pois essa definição concreta ainda não
  existe no projeto e é detalhe de implementação da Fase 2 — a exigência de negócio é que as
  causas de erro listadas acima sejam distinguíveis nesse contrato, não que exista um único
  payload genérico de erro de transcrição.

## Restrições e validações

- Este domínio não aplica validação própria de formato ou de duração do áudio — essa validação
  é responsabilidade exclusiva do domínio Captura e Ingestão de Áudio e já foi concluída antes de
  o áudio chegar aqui.
- A validação de idioma é responsabilidade exclusiva deste domínio: o áudio só é transcrito
  quando o idioma detectado é português (pt-BR); em qualquer outro idioma detectado, o áudio é
  rejeitado sem ser transcrito.
- Nenhum texto transcrito, produzido com sucesso ou não, é persistido — não há exceção a essa
  regra.

## Integrações e dependências externas

Este domínio não integra nenhum serviço externo em nuvem nomeado — a transcrição é feita
inteiramente por um motor Whisper local, sem credenciais nem conectividade com API remota de
transcrição. Sua única integração é interna ao app: recebe o áudio validado entregue pelo
domínio Captura e Ingestão de Áudio.

As dependências técnicas transversais que este domínio precisa para operar (motor Whisper
local, recursos de CPU/GPU da própria máquina, decodificação dos formatos de áudio aceitos e
disponibilidade local dos pesos do modelo) estão detalhadas em
`references/technical-dependencies.md`.
