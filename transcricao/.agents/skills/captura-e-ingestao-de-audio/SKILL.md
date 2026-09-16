---
name: captura-e-ingestao-de-audio
description: >
  Esta é a documentação autoritativa do domínio Captura e Ingestão de Áudio: como o app recebe
  e valida o áudio enviado pelo usuário antes de encaminhá-lo à transcrição. Cobre os dois canais
  de entrada (CLI e API HTTP), a validação de formato e de limite de duração do áudio, e
  o processamento síncrono e transitório (sem persistência de áudio ou de transcrição). Use ao
  tratar envio, upload, captura, ingestão ou validação de áudio, ou ao implementar o canal CLI ou
  o endpoint HTTP de recebimento de áudio.
metadata:
  author: clovis-cli
  type: domain-skill
---

# Captura e Ingestão de Áudio

> **Manutenção desta skill**
>
> Atualize este documento sempre que o comportamento deste domínio mudar de propósito, mantendo
> a skill fiel ao comportamento implementado. Uma mudança deliberada no código, com decisão
> registrada, atualiza a skill. Uma divergência semântica entre esta skill e o código, sem
> decisão registrada que a resolva, é escalada para decisão humana — nunca ajustada aqui de
> forma unilateral.

## Visão geral do domínio

Este domínio é o ponto de entrada do fluxo do app: recebe o áudio enviado pelo usuário e o
valida antes de encaminhá-lo ao domínio Motor de Transcrição. Não depende de nenhum outro
domínio do app. O processamento é inteiramente transitório — nenhum áudio recebido é persistido
em banco de dados ou em armazenamento de arquivos, independentemente do canal de entrada usado.

## Regras de negócio

1. **Dois canais de entrada, um único fluxo de captura.** O app aceita o áudio por exatamente
   dois canais: CLI (o usuário informa o caminho de um arquivo de áudio local) e API HTTP
   (upload do arquivo via endpoint REST). Os dois canais alimentam o mesmo fluxo de validação e
   ingestão — não constituem regras de negócio distintas entre si, apenas pontos de entrada
   diferentes para a mesma captura.
2. **Validação obrigatória antes da transcrição.** Todo áudio recebido, por qualquer um dos dois
   canais, é validado quanto a formato e quanto ao limite de duração antes de ser encaminhado à
   transcrição. Áudio que falha nessa validação não é encaminhado ao domínio Motor de
   Transcrição.
3. **Formatos aceitos.** O domínio aceita áudio nos formatos WAV, MP3, M4A, OGG e FLAC. Áudio em
   qualquer outro formato é rejeitado na validação.
4. **Limite por duração, não por tamanho de arquivo.** O critério de limite do áudio é a sua
   duração, não o tamanho do arquivo: um envio é aceito quando o áudio dura até 10 minutos.
   Áudio com duração acima desse limite é rejeitado na validação, independentemente do tamanho
   em bytes do arquivo.
5. **Processamento transitório.** Nenhum áudio recebido — validado ou rejeitado — é persistido em
   banco de dados ou em armazenamento de arquivos após a resposta ao usuário. Cada envio é
   independente; não há histórico de envios anteriores.
6. **Processamento síncrono.** A chamada que envia o áudio (pela CLI ou pela API HTTP) só retorna
   depois que a validação — e, em caso de sucesso, a transcrição feita pelo domínio Motor de
   Transcrição — estiver concluída. Não há job em background nem consulta de status posterior.
7. **Ponto de entrada do fluxo.** Este domínio não depende de nenhum outro domínio do app. Ao
   validar o áudio com sucesso, ele o entrega ao domínio Motor de Transcrição; o que esse domínio
   faz com o áudio a partir daí é escopo daquele domínio, não deste.

## Fluxos e ciclo de vida

- **Entrada via CLI:** o usuário informa o caminho de um arquivo de áudio local. O domínio lê o
  arquivo indicado e valida se o formato é um dos aceitos (WAV, MP3, M4A, OGG, FLAC) e se a
  duração do áudio não excede 10 minutos.
- **Entrada via API HTTP:** o cliente faz upload do arquivo de áudio para um endpoint REST. O
  domínio aplica a mesma validação de formato e de duração sobre o arquivo recebido.
- **Validação com sucesso:** o áudio validado é encaminhado ao domínio Motor de Transcrição; a
  chamada de entrada (CLI ou HTTP) permanece bloqueada até a transcrição terminar e retorna o
  texto transcrito na mesma resposta.
- **Validação com falha:** o domínio não encaminha o áudio à transcrição e reporta, pelo mesmo
  canal de entrada, que a validação falhou e por qual motivo — formato não suportado (fora de
  WAV, MP3, M4A, OGG ou FLAC), ou duração acima de 10 minutos.
- Não há estado que sobreviva a uma única chamada: nada do que é recebido, validado ou rejeitado
  fica disponível para consulta posterior.

## Entidades e dados

- **Áudio recebido** — única entidade deste domínio. É transitória: existe apenas durante o
  processamento de uma única chamada (CLI ou HTTP) e não é armazenada em nenhum momento do
  fluxo. É identificada, para fins de validação, pelo seu formato/contêiner (WAV, MP3, M4A, OGG
  ou FLAC) e pela sua duração (até 10 minutos).
- Não há entidade persistente nem tabela de banco de dados neste domínio — decorrência direta da
  regra de processamento transitório.
- O contrato do canal HTTP (rota, payload de requisição, payload de resposta e payloads de erro)
  é formalizado na especificação OpenAPI mantida para a API do app; este domínio não fixa aqui a
  rota nem o formato exato de payload, pois essa definição concreta ainda não existe no projeto
  e é detalhe de implementação da Fase 2.

## Restrições e validações

- **Formato:** apenas WAV, MP3, M4A, OGG e FLAC são aceitos. Qualquer outro formato é rejeitado
  na validação, antes de o áudio seguir para transcrição.
- **Duração:** o limite do áudio é definido pela sua duração, não pelo tamanho do arquivo em
  bytes. Um áudio com duração de até 10 minutos é aceito; acima disso é rejeitado na validação,
  independentemente do formato.
- Nenhum áudio, validado ou rejeitado, é persistido — não há exceção a essa regra.
- O escopo de idioma da transcrição (apenas português/pt-BR) é uma regra do domínio Motor de
  Transcrição, não deste; este domínio não valida idioma do áudio recebido.

## Integrações e dependências externas

Este domínio não integra nenhum serviço externo nomeado (não há gateway de pagamento, provedor de
e-mail, IdP ou serviço de nuvem envolvido na captura e na validação do áudio). Sua única
integração é interna ao app: ao concluir a validação com sucesso, entrega o áudio validado ao
domínio Motor de Transcrição.

As dependências técnicas transversais que este domínio precisa para operar (canal duplo de
entrada, ausência de armazenamento persistente, capacidade de inspecionar metadados do áudio e
manipulação do áudio inteiramente em memória/arquivo temporário) estão detalhadas em
`references/technical-dependencies.md`.
