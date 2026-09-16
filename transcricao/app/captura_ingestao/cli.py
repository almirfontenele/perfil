"""Canal de entrada via linha de comando do domínio Captura e Ingestão de Áudio.

O usuário informa o caminho de um arquivo de áudio local; a execução permanece
bloqueada até a transcrição terminar e devolve o texto transcrito na mesma
execução, ou informa o motivo da rejeição quando a validação falha.
"""

import argparse
import sys
from typing import Optional

from .metadados import ler_metadados
from .motor import FalhaTranscricao, TranscreverAudio, transcrever as transcrever_audio_padrao
from .validacao import validar


def processar_audio(
    caminho_arquivo: str,
    transcrever_audio: TranscreverAudio = transcrever_audio_padrao,
) -> str:
    """Valida o áudio informado e, se aceito, encaminha ao Motor de Transcrição.

    Levanta `ValueError` com o motivo da rejeição quando o áudio não passa na
    validação de formato ou de duração; nesse caso, `transcrever_audio` não é
    chamado. Quando a validação passa mas a transcrição não produz texto,
    `transcrever_audio` levanta `motor.FalhaTranscricao` com a causa
    específica (idioma não suportado, silêncio, ruído ou falha interna do
    motor).
    """
    metadados = ler_metadados(caminho_arquivo)
    motivo_rejeicao = validar(metadados.formato, metadados.duracao_segundos)
    if motivo_rejeicao is not None:
        raise ValueError(motivo_rejeicao)

    return transcrever_audio(caminho_arquivo)


def main(
    argv: Optional[list] = None,
    transcrever_audio: TranscreverAudio = transcrever_audio_padrao,
) -> int:
    """Ponto de entrada da CLI: parseia o argumento e imprime o resultado."""
    parser = argparse.ArgumentParser(
        description="Transcreve, em português (pt-BR), um áudio local informado por caminho."
    )
    parser.add_argument("caminho", help="Caminho do arquivo de áudio local a transcrever.")
    args = parser.parse_args(argv)

    try:
        texto_transcrito = processar_audio(args.caminho, transcrever_audio=transcrever_audio)
    except ValueError as motivo_rejeicao:
        print(str(motivo_rejeicao), file=sys.stderr)
        return 1
    except FalhaTranscricao as falha:
        print(str(falha), file=sys.stderr)
        return 1

    print(texto_transcrito)
    return 0


if __name__ == "__main__":
    sys.exit(main())
