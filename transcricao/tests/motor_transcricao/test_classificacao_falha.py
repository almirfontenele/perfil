import pytest

from app.motor_transcricao.classificacao_falha import (
    CAUSA_RUIDO,
    CAUSA_SILENCIO,
    LIMIAR_ENERGIA_SILENCIO,
    classificar_falha,
)


# TC-3 — Causa `silencio` classificada a partir da energia do áudio
@pytest.mark.parametrize(
    ("no_speech_prob", "confianca_media"),
    [
        (0.0, 0.0),  # sinais de confiança "de fala" não mudam o resultado
        (0.99, -5.0),  # sinais de confiança "de ruído" também não mudam o resultado
    ],
)
def test_classificar_falha_energia_abaixo_do_limiar_e_sempre_silencio(
    no_speech_prob, confianca_media
):
    causa = classificar_falha(
        energia_rms=LIMIAR_ENERGIA_SILENCIO / 2,
        no_speech_prob=no_speech_prob,
        confianca_media=confianca_media,
    )

    assert causa == CAUSA_SILENCIO


# TC-5 — Causa `ruido` classificada a partir da energia e da confiança do áudio
def test_classificar_falha_energia_acima_do_limiar_com_baixa_confianca_e_ruido():
    causa = classificar_falha(
        energia_rms=LIMIAR_ENERGIA_SILENCIO * 10,
        no_speech_prob=0.95,
        confianca_media=-2.5,
    )

    assert causa == CAUSA_RUIDO
    assert causa != CAUSA_SILENCIO


def test_classificar_falha_energia_exatamente_no_limiar_nao_e_silencio():
    # O limiar é estritamente "abaixo de" (`<`), não "até".
    causa = classificar_falha(
        energia_rms=LIMIAR_ENERGIA_SILENCIO,
        no_speech_prob=0.5,
        confianca_media=-1.0,
    )

    assert causa == CAUSA_RUIDO
