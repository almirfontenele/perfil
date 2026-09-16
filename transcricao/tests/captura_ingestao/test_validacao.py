import pytest

from app.captura_ingestao.validacao import (
    DURACAO_MAXIMA_SEGUNDOS,
    MOTIVO_DURACAO_EXCEDIDA,
    MOTIVO_FORMATO_NAO_SUPORTADO,
    validar,
    validar_duracao,
    validar_formato,
)


@pytest.mark.parametrize("formato", ["wav", "mp3", "m4a", "ogg", "flac", "WAV", "Mp3"])
def test_validar_formato_aceita_formatos_suportados(formato):
    assert validar_formato(formato) is True


@pytest.mark.parametrize("formato", ["aac", "wma", "txt", ""])
def test_validar_formato_rejeita_formatos_nao_suportados(formato):
    assert validar_formato(formato) is False


def test_validar_duracao_aceita_ate_o_limite_inclusive():
    assert validar_duracao(DURACAO_MAXIMA_SEGUNDOS) is True


def test_validar_duracao_aceita_abaixo_do_limite():
    assert validar_duracao(DURACAO_MAXIMA_SEGUNDOS - 1) is True


def test_validar_duracao_rejeita_acima_do_limite():
    assert validar_duracao(DURACAO_MAXIMA_SEGUNDOS + 1) is False


def test_validar_aceita_formato_suportado_e_duracao_dentro_do_limite():
    assert validar("wav", DURACAO_MAXIMA_SEGUNDOS) is None


def test_validar_rejeita_por_formato_nao_suportado():
    assert validar("aac", 60) == MOTIVO_FORMATO_NAO_SUPORTADO


def test_validar_rejeita_por_duracao_excedida():
    assert validar("wav", DURACAO_MAXIMA_SEGUNDOS + 1) == MOTIVO_DURACAO_EXCEDIDA


def test_validar_formato_tem_precedencia_sobre_duracao():
    # Um áudio com formato não suportado e duração também acima do limite é
    # rejeitado pelo motivo de formato, não pelo de duração.
    assert validar("aac", DURACAO_MAXIMA_SEGUNDOS + 1) == MOTIVO_FORMATO_NAO_SUPORTADO
