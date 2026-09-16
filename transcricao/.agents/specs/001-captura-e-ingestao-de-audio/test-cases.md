# Test cases: Captura e Ingestão de Áudio

## Preconditions

- Ambiente do projeto com as dependências declaradas em `plan.md` instaladas (FastAPI, Uvicorn,
  `mutagen`; `argparse` já faz parte da biblioteca padrão do Python).
- Arquivos de áudio de amostra: um por formato aceito (WAV, MP3, M4A, OGG, FLAC) com duração
  dentro do limite, um com duração acima de 10 minutos e um em um formato fora dos cinco aceitos
  (por exemplo, `.aac`), para os casos de rejeição.
- Nos casos de envio bem-sucedido, a chamada ao domínio Motor de Transcrição substituída por um
  dublê de teste que devolve um texto transcrito — esse domínio ainda não está implementado neste
  repositório e é uma dependência cross-domain declarada no `spec.md`, não algo que esta unidade
  entrega.

## Story 1 — Envio via CLI

### TC-1 (mandatory) — Envio bem-sucedido via CLI

1. Invocar o comando CLI do domínio (`app/captura_ingestao/cli.py`, conforme `plan.md`),
   informando como argumento o caminho de um arquivo de áudio local em um dos formatos aceitos
   (WAV, MP3, M4A, OGG ou FLAC) com duração de até 10 minutos.
2. Aguardar o término da execução.

**Expected:** a execução permanece bloqueada até o dublê de teste do Motor de Transcrição
devolver o texto transcrito, e esse texto é devolvido na mesma execução; nenhum arquivo do áudio
enviado permanece após o término, conforme a Story 1 do `spec.md`.

### TC-2 (mandatory) — Rejeição por formato não suportado via CLI

1. Invocar o comando CLI informando o caminho de um arquivo de áudio em um formato fora de WAV,
   MP3, M4A, OGG e FLAC.

**Expected:** a execução não encaminha o áudio ao domínio Motor de Transcrição (o dublê de teste
não é chamado) e informa, na mesma execução, que o formato não é suportado, conforme a Story 1
do `spec.md`.

### TC-3 (mandatory) — Rejeição por duração acima do limite via CLI

1. Invocar o comando CLI informando o caminho de um arquivo de áudio em um formato aceito com
   duração acima de 10 minutos.

**Expected:** a execução não encaminha o áudio ao domínio Motor de Transcrição e informa, na
mesma execução, que a duração excede o limite, conforme a Story 1 do `spec.md`.

## Story 2 — Envio via API HTTP

### TC-4 (mandatory) — Envio bem-sucedido via API HTTP

1. Com a aplicação FastAPI em execução, enviar ao endpoint HTTP de ingestão de áudio deste
   domínio o upload de um arquivo de áudio em um dos formatos aceitos (WAV, MP3, M4A, OGG ou
   FLAC) com duração de até 10 minutos.

**Expected:** a chamada permanece bloqueada até o dublê de teste do Motor de Transcrição devolver
o texto transcrito, e a resposta devolve esse texto na mesma chamada; nenhum arquivo do áudio
enviado permanece após a resposta, conforme a Story 2 do `spec.md`.

### TC-5 (mandatory) — Rejeição por formato não suportado via API HTTP

1. Enviar ao endpoint HTTP de ingestão de áudio o upload de um arquivo em um formato fora de WAV,
   MP3, M4A, OGG e FLAC.

**Expected:** o áudio não é encaminhado ao domínio Motor de Transcrição e a resposta informa que
o formato não é suportado, conforme a Story 2 do `spec.md`.

### TC-6 (mandatory) — Rejeição por duração acima do limite via API HTTP

1. Enviar ao endpoint HTTP de ingestão de áudio o upload de um arquivo em um formato aceito com
   duração acima de 10 minutos.

**Expected:** o áudio não é encaminhado ao domínio Motor de Transcrição e a resposta informa que
a duração excede o limite, conforme a Story 2 do `spec.md`.

## Story 3 — Validação antes da transcrição

### TC-7 (mandatory) — A rejeição por formato ou duração via CLI não chama o Motor de Transcrição

1. Repetir o envio de TC-2 ou de TC-3 pela CLI.
2. Verificar se o dublê de teste do Motor de Transcrição registrou alguma chamada.

**Expected:** o dublê de teste do Motor de Transcrição não registra nenhuma chamada, confirmando
que a validação de formato e de duração ocorre antes de qualquer encaminhamento à transcrição,
conforme a Story 3 do `spec.md`. Relacionado a TC-2 e TC-3.

### TC-8 (mandatory) — A rejeição por formato ou duração via API HTTP não chama o Motor de Transcrição

1. Repetir o envio de TC-5 ou de TC-6 pelo endpoint HTTP.
2. Verificar se o dublê de teste do Motor de Transcrição registrou alguma chamada.

**Expected:** o dublê de teste do Motor de Transcrição não registra nenhuma chamada, conforme a
Story 3 do `spec.md`. Relacionado a TC-5 e TC-6.

### TC-9 (recommended) — Mesmo critério de validação nos dois canais

1. Enviar o mesmo arquivo de áudio (formato aceito, duração dentro do limite) pela CLI (como em
   TC-1) e, em uma execução separada, pelo endpoint HTTP (como em TC-4).
2. Comparar o resultado dos dois envios.

**Expected:** os dois canais aceitam o mesmo arquivo e produzem o mesmo resultado de sucesso,
confirmando que o critério de formato e de duração é idêntico nos dois canais, conforme a Story 3
do `spec.md`.

### TC-13 (recommended) — Duração exatamente no limite de 10 minutos é aceita

1. Enviar, pela CLI ou pelo endpoint HTTP, um arquivo de áudio em um formato aceito com duração
   de exatamente 10 minutos.

**Expected:** o áudio é aceito e encaminhado ao domínio Motor de Transcrição, pois as Stories 1 e
2 do `spec.md` aceitam duração "de até 10 minutos" (limite inclusive).

## Story 4 — Sem persistência

### TC-10 (mandatory) — Nenhum dado do áudio recebido é persistido após um envio aceito

1. Executar o envio bem-sucedido de TC-1 (via CLI) ou de TC-4 (via API HTTP).
2. Inspecionar o sistema de arquivos e o ambiente de execução da aplicação em busca de qualquer
   arquivo ou registro em banco de dados criado a partir desse envio.

**Expected:** nenhum arquivo de áudio nem registro em banco de dados relativo ao envio permanece
após a resposta, conforme a Story 4 do `spec.md` — o domínio não usa banco de dados nem
armazenamento de arquivos (`spec.md`, Domain boundary).

### TC-11 (mandatory) — Uma chamada não tem acesso a dados de uma chamada anterior

1. Executar um envio de áudio, via CLI ou via API HTTP, e observar o resultado.
2. Executar, em seguida, um segundo envio independente de um áudio diferente.

**Expected:** o segundo envio é processado sem nenhuma referência ao primeiro envio, conforme a
Story 4 do `spec.md`.

### TC-12 (mandatory) — Nenhum dado é persistido mesmo quando o áudio é rejeitado

1. Executar o envio de TC-2, TC-3, TC-5 ou TC-6 (rejeição por formato ou por duração).
2. Inspecionar o sistema de arquivos e o ambiente de execução da aplicação em busca de qualquer
   arquivo ou registro criado a partir desse envio.

**Expected:** nenhum dado do áudio rejeitado permanece armazenado após a resposta, conforme a
regra de processamento transitório do `spec.md` ("nenhum áudio recebido — validado ou rejeitado —
é persistido").
