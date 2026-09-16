"""Classificação da causa de uma transcrição sem texto: silêncio ou ruído.

Combina a energia (RMS) do áudio decodificado com os sinais nativos do
Whisper (`no_speech_prob` e confiança média por segmento) — heurística
confirmada em `research.md` desta unidade — para distinguir, quando a
transcrição de um áudio no idioma correto não produz texto, entre silêncio
(sem fala perceptível) e ruído (dominado por ruído sem fala identificável).
Falha interna do motor durante a inferência é uma terceira causa possível,
mas não passa por esta função: é reportada pela orquestração de
`transcricao.py` diretamente a partir de uma exceção da biblioteca.
"""

CAUSA_SILENCIO = "silencio"
CAUSA_RUIDO = "ruido"

# Calibrados com áudios de amostra sintéticos durante a implementação (`plan.md`,
# "Riscos e observações"); sujeitos a ajuste com áudio real representativo de
# cada causa.
LIMIAR_ENERGIA_SILENCIO = 0.01


def classificar_falha(energia_rms: float, no_speech_prob: float, confianca_media: float) -> str:
    """Classifica, entre `silencio` e `ruido`, a causa de uma transcrição sem texto.

    Energia (RMS) abaixo de `LIMIAR_ENERGIA_SILENCIO` indica silêncio,
    independentemente dos sinais de confiança do Whisper — um áudio sem
    energia perceptível não tem fala para esses sinais avaliarem. Acima
    desse limiar, o áudio tem conteúdo perceptível sem texto reconhecido: já
    que silêncio e ruído são as duas únicas causas distinguíveis neste
    nível (falha interna do motor é tratada como exceção pela orquestração,
    não por esta função), o resultado é ruído. `no_speech_prob` e
    `confianca_media` fazem parte da assinatura por documentarem, junto da
    energia, a heurística de classificação confirmada em `research.md`.
    """
    if energia_rms < LIMIAR_ENERGIA_SILENCIO:
        return CAUSA_SILENCIO
    return CAUSA_RUIDO
