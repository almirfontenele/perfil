"""Canal de entrada via API HTTP do domínio Captura e Ingestão de Áudio.

O cliente faz upload de um arquivo de áudio; a chamada permanece bloqueada até
a transcrição terminar e a resposta devolve o texto transcrito, ou informa o
motivo da rejeição quando a validação falha. A rota é formalizada em
`openapi.yaml`, na raiz do repositório, conforme a technical-skill
`documentacao-de-api`.
"""

import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from .metadados import ler_metadados
from .motor import FalhaTranscricao, MENSAGENS_POR_CAUSA, TranscreverAudio
from .motor import transcrever as transcrever_audio_padrao
from .validacao import MOTIVO_DURACAO_EXCEDIDA, MOTIVO_FORMATO_NAO_SUPORTADO, validar

app = FastAPI(title="Transcrição de Áudio", version="0.1.0")

_STATUS_POR_CAUSA_DE_FALHA = {
    "idioma_nao_suportado": 422,
    "silencio": 422,
    "ruido": 422,
    "falha_interna_motor": 500,
}


class TranscricaoResponse(BaseModel):
    """Payload de sucesso: texto transcrito do áudio enviado."""

    texto_transcrito: str


async def processar_upload(
    arquivo: UploadFile,
    transcrever_audio: TranscreverAudio = transcrever_audio_padrao,
) -> str:
    """Valida o áudio recebido por upload e, se aceito, encaminha ao Motor de Transcrição.

    Grava o conteúdo enviado em um arquivo temporário só pelo tempo da
    validação e da transcrição — apagado ao final, com sucesso ou não —, para
    reaproveitar as mesmas funções de validação de formato/duração e de
    leitura de metadados do canal CLI (`validacao.validar`,
    `metadados.ler_metadados`), que operam sobre um caminho de arquivo em
    disco.

    Levanta `HTTPException` quando o áudio não é transcrito com sucesso: 400
    para formato não suportado; 422 para duração excedida, idioma detectado
    não suportado, silêncio ou ruído; 500 para falha interna do motor de
    transcrição. Nos casos de rejeição por formato ou por duração,
    `transcrever_audio` não é chamado.
    """
    sufixo = os.path.splitext(arquivo.filename or "")[1]
    conteudo = await arquivo.read()

    with tempfile.NamedTemporaryFile(suffix=sufixo) as arquivo_temporario:
        arquivo_temporario.write(conteudo)
        arquivo_temporario.flush()

        metadados = ler_metadados(arquivo_temporario.name)
        motivo_rejeicao = validar(metadados.formato, metadados.duracao_segundos)
        if motivo_rejeicao == MOTIVO_FORMATO_NAO_SUPORTADO:
            raise HTTPException(status_code=400, detail=motivo_rejeicao)
        if motivo_rejeicao == MOTIVO_DURACAO_EXCEDIDA:
            raise HTTPException(status_code=422, detail=motivo_rejeicao)

        try:
            return transcrever_audio(arquivo_temporario.name)
        except FalhaTranscricao as falha:
            status_code = _STATUS_POR_CAUSA_DE_FALHA.get(falha.causa, 500)
            detail = MENSAGENS_POR_CAUSA.get(falha.causa, falha.causa)
            raise HTTPException(status_code=status_code, detail=detail) from falha


@app.post("/transcricoes", response_model=TranscricaoResponse)
async def enviar_audio(arquivo: UploadFile = File(...)) -> TranscricaoResponse:
    """Recebe o upload de um áudio e devolve o texto transcrito na mesma resposta."""
    texto_transcrito = await processar_upload(arquivo)
    return TranscricaoResponse(texto_transcrito=texto_transcrito)
