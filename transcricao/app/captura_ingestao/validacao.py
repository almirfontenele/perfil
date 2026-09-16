"""Regras de validação de formato e de duração do áudio recebido.

Aplicadas da mesma forma aos dois canais de entrada (CLI e API HTTP), antes de
qualquer encaminhamento ao domínio Motor de Transcrição.
"""

from typing import Optional

FORMATOS_ACEITOS = frozenset({"wav", "mp3", "m4a", "ogg", "flac"})
DURACAO_MAXIMA_SEGUNDOS = 10 * 60

MOTIVO_FORMATO_NAO_SUPORTADO = "Formato de áudio não suportado."
MOTIVO_DURACAO_EXCEDIDA = "Duração do áudio excede o limite de 10 minutos."


def validar_formato(formato: str) -> bool:
    """Indica se `formato` está entre os aceitos (WAV, MP3, M4A, OGG, FLAC)."""
    return formato.lower() in FORMATOS_ACEITOS


def validar_duracao(duracao_segundos: float) -> bool:
    """Indica se `duracao_segundos` respeita o limite de 10 minutos (limite inclusive)."""
    return duracao_segundos <= DURACAO_MAXIMA_SEGUNDOS


def validar(formato: str, duracao_segundos: float) -> Optional[str]:
    """Aplica a validação de formato e, em seguida, a de duração.

    Devolve `None` quando o áudio é aceito, ou o motivo da rejeição (formato
    não suportado ou duração excedida) caso contrário.
    """
    if not validar_formato(formato):
        return MOTIVO_FORMATO_NAO_SUPORTADO
    if not validar_duracao(duracao_segundos):
        return MOTIVO_DURACAO_EXCEDIDA
    return None
