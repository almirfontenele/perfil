"""Interface de encaminhamento ao domínio Motor de Transcrição.

Reaproveitada pelos dois canais de entrada (CLI e API HTTP) para a mesma
chamada de função em processo, conforme decisão registrada no `plan.md`
desta unidade.
"""

from typing import Callable

from app.motor_transcricao.transcricao import transcrever as _transcrever_audio

TranscreverAudio = Callable[[str], str]

MENSAGENS_POR_CAUSA = {
    "idioma_nao_suportado": (
        "Idioma detectado no áudio não é suportado (apenas português/pt-BR)."
    ),
    "silencio": "Áudio sem fala perceptível (silêncio).",
    "ruido": "Áudio dominado por ruído, sem fala identificável.",
    "falha_interna_motor": "Falha interna do motor de transcrição.",
}


class FalhaTranscricao(Exception):
    """Levantada quando o Motor de Transcrição não produz texto para o áudio recebido.

    `causa` é uma das causas distinguíveis do domínio Motor de Transcrição
    (`idioma_nao_suportado`, `silencio`, `ruido` ou `falha_interna_motor`) —
    cada uma reportada de forma distinta pelo canal de entrada que originou a
    chamada, nunca como um erro genérico (regra 6 da skill do domínio Motor
    de Transcrição).
    """

    def __init__(self, causa: str):
        self.causa = causa
        super().__init__(MENSAGENS_POR_CAUSA.get(causa, causa))


def transcrever(caminho_arquivo: str) -> str:
    """Chamada real ao domínio Motor de Transcrição (função em processo).

    Levanta `FalhaTranscricao` quando o áudio não é transcrito com sucesso.
    """
    resultado = _transcrever_audio(caminho_arquivo)
    if resultado.texto is not None:
        return resultado.texto
    raise FalhaTranscricao(resultado.causa_erro)
