"""Leitura de formato e duração do áudio a partir do próprio arquivo, via `mutagen`.

Biblioteca pura Python (sem dependência de binário externo como o FFmpeg), com
suporte aos cinco formatos aceitos pelo domínio (WAV, MP3, M4A, OGG e FLAC).
"""

import os
from dataclasses import dataclass

import mutagen

_FORMATO_POR_CLASSE = {
    "WAVE": "wav",
    "MP3": "mp3",
    "MP4": "m4a",
    "OggVorbis": "ogg",
    "OggOpus": "ogg",
    "FLAC": "flac",
}


@dataclass(frozen=True)
class Metadados:
    """Formato/contêiner e duração (em segundos) de um áudio."""

    formato: str
    duracao_segundos: float


def ler_metadados(caminho_arquivo: str) -> Metadados:
    """Lê formato e duração de `caminho_arquivo` a partir dos seus próprios metadados.

    Quando o `mutagen` não reconhece o arquivo como nenhum dos contêineres que
    sabe ler — devolvendo `None` ou levantando `MutagenError` ao tentar
    interpretar um conteúdo que não corresponde ao formato sugerido pela
    extensão —, o formato retornado não corresponde a nenhum dos aceitos pelo
    domínio, e a rejeição por formato não suportado é então aplicada por
    `validacao.validar`.
    """
    try:
        arquivo = mutagen.File(caminho_arquivo)
    except mutagen.MutagenError:
        arquivo = None

    if arquivo is None:
        extensao = os.path.splitext(caminho_arquivo)[1].lstrip(".").lower()
        return Metadados(formato=extensao or "desconhecido", duracao_segundos=0.0)

    formato = _FORMATO_POR_CLASSE.get(type(arquivo).__name__, type(arquivo).__name__.lower())
    return Metadados(formato=formato, duracao_segundos=arquivo.info.length)
