import pytest

from app.captura_ingestao import motor
from app.motor_transcricao.transcricao import ResultadoTranscricao


def test_transcrever_devolve_texto_quando_motor_de_transcricao_produz_texto(monkeypatch):
    monkeypatch.setattr(
        motor, "_transcrever_audio", lambda caminho: ResultadoTranscricao(texto="texto transcrito")
    )

    assert motor.transcrever("audio.wav") == "texto transcrito"


@pytest.mark.parametrize(
    "causa", ["idioma_nao_suportado", "silencio", "ruido", "falha_interna_motor"]
)
def test_transcrever_levanta_falha_transcricao_com_a_causa_especifica(monkeypatch, causa):
    monkeypatch.setattr(
        motor, "_transcrever_audio", lambda caminho: ResultadoTranscricao(causa_erro=causa)
    )

    with pytest.raises(motor.FalhaTranscricao) as excecao:
        motor.transcrever("audio.wav")

    assert excecao.value.causa == causa
    assert str(excecao.value) == motor.MENSAGENS_POR_CAUSA[causa]
