# Dependências técnicas — Motor de Transcrição

> **Manutenção deste documento**
>
> Atualize-o sempre que uma dependência técnica do domínio for adicionada, deixar de ser
> necessária ou mudar de natureza. Uma troca da biblioteca específica usada para atender a uma
> dependência (por exemplo, a escolha entre `openai-whisper` e `faster-whisper`, ou a ferramenta
> concreta de decodificação de áudio) não exige alteração aqui, pois este documento descreve a
> necessidade técnica, não a escolha de implementação que a atende.

Cada item abaixo descreve uma dependência técnica do domínio e o que fica comprometido no
domínio caso ela esteja ausente. A biblioteca/framework concreto que atende cada dependência é
detalhe de implementação, decidido durante o planejamento incremental do domínio — citado aqui
apenas quando já há evidência disso nas fontes investigadas.

## Whisper local (`openai-whisper` ou `faster-whisper`)

Motor de transcrição executado na própria máquina, sem chamada a API remota. Sem essa
biblioteca, o domínio não tem como converter áudio em texto. A escolha entre `openai-whisper` e
`faster-whisper` é detalhe de implementação a ser definido na Fase 2 (plan/tasks), não altera a
fronteira deste domínio.

## Recursos de CPU/GPU da própria máquina para inferência do modelo

A execução local do motor Whisper depende de capacidade de processamento (CPU ou GPU) da própria
máquina para realizar a inferência do modelo a cada transcrição — e não de credenciais ou
conectividade com serviços externos de nuvem em tempo de execução. Sem capacidade de
processamento suficiente, a transcrição de cada áudio fica mais lenta ou pode não ser viável
dentro do modelo de processamento síncrono do domínio.

## Decodificação dos formatos de áudio aceitos na ingestão

O domínio Captura e Ingestão de Áudio aceita e entrega a este domínio áudio nos formatos WAV,
MP3, M4A, OGG e FLAC. O motor Whisper não lê diretamente contêineres de áudio comprimidos como
MP3, M4A, OGG ou FLAC sem uma camada de decodificação de áudio (tipicamente um binário externo
como o FFmpeg) instalada no ambiente de execução. Sem essa capacidade de decodificação
disponível no ambiente, o domínio só conseguiria transcrever áudio já em formato decodificado
(essencialmente WAV/PCM), falhando para os demais formatos que o domínio anterior aceita e
entrega normalmente.

## Disponibilidade local dos pesos do modelo Whisper

O motor Whisper precisa dos pesos de um modelo pré-treinado disponíveis no ambiente de execução
para realizar a inferência. Ainda que a inferência em si não dependa de conectividade com
serviços externos (ver dependência de CPU/GPU acima), a obtenção inicial desses pesos —
tipicamente por download na primeira execução ou por pré-provisionamento no ambiente — exige, em
algum momento anterior à primeira transcrição, acesso para trazê-los ao ambiente onde o domínio
roda. Sem os pesos do modelo disponíveis localmente, nenhuma transcrição pode ser realizada,
mesmo com o motor Whisper e a capacidade de processamento presentes.
