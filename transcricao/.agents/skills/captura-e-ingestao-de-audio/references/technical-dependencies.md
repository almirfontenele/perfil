# Dependências técnicas — Captura e Ingestão de Áudio

> **Manutenção deste documento**
>
> Atualize-o sempre que uma dependência técnica do domínio for adicionada, deixar de ser
> necessária ou mudar de natureza. Uma troca da biblioteca específica usada para atender a uma
> dependência (por exemplo, a biblioteca concreta de inspeção de metadados de áudio) não exige
> alteração aqui, pois este documento descreve a necessidade técnica, não a escolha de
> implementação que a atende.

Cada item abaixo descreve uma dependência técnica do domínio e o que fica comprometido no
domínio caso ela esteja ausente. A biblioteca/framework concreto que atende cada dependência é
detalhe de implementação, decidido durante o planejamento incremental do domínio — citado aqui
apenas quando já há evidência disso nas fontes investigadas.

## Canal duplo de entrada (CLI + API HTTP)

Sem ele, o app só atenderia a um tipo de cliente (ou só linha de comando, ou só integrações via
rede); a biblioteca/framework específico de cada canal é detalhe de implementação a ser definido
na Fase 2 (plan/tasks), não altera a fronteira deste domínio.

## Ausência de banco de dados/armazenamento de arquivos

Decisão validada (`gap-4-persistencia`); o domínio não precisa de infraestrutura de persistência
para operar.

## Capacidade de inspeção de metadados do áudio (formato do contêiner e duração)

Sem ela, o domínio não tem como aplicar a regra de validação de formato e de limite de duração
antes de encaminhar o áudio à transcrição — a validação depende de conseguir ler, a partir do
próprio arquivo/upload recebido, qual é o seu formato e qual é a sua duração. A
biblioteca específica usada para essa inspeção é detalhe de implementação a ser definido na Fase
2, não altera a fronteira deste domínio.

## Manipulação do áudio inteiramente em memória/arquivo temporário, sem escrita em armazenamento persistente

Sem ela, o domínio não tem como receber e validar o áudio dos dois canais de entrada (caminho de
arquivo local via CLI, upload via API HTTP) de forma consistente entre os dois canais antes de
encaminhá-lo à transcrição, respeitando a decisão de processamento transitório (nenhum áudio é
persistido após a resposta).
