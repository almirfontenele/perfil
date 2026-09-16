import pytest

from app.captura_ingestao import cli
from app.captura_ingestao.metadados import Metadados
from app.captura_ingestao.validacao import (
    DURACAO_MAXIMA_SEGUNDOS,
    MOTIVO_DURACAO_EXCEDIDA,
    MOTIVO_FORMATO_NAO_SUPORTADO,
)


class _MotorDeTranscricaoFalso:
    """Dublê de teste do domínio Motor de Transcrição.

    Substitui, nos testes deste domínio, a chamada de função em processo ao
    domínio Motor de Transcrição, injetada via `transcrever_audio`.
    """

    def __init__(self, texto_transcrito="texto transcrito de teste"):
        self.texto_transcrito = texto_transcrito
        self.chamadas = []

    def __call__(self, caminho_arquivo):
        self.chamadas.append(caminho_arquivo)
        return self.texto_transcrito


def _finge_metadados(monkeypatch, formato, duracao_segundos):
    monkeypatch.setattr(
        cli,
        "ler_metadados",
        lambda caminho_arquivo: Metadados(formato=formato, duracao_segundos=duracao_segundos),
    )


# TC-1 — Envio bem-sucedido via CLI
def test_processar_audio_aceito_devolve_texto_transcrito(monkeypatch):
    _finge_metadados(monkeypatch, formato="wav", duracao_segundos=120.0)
    motor_falso = _MotorDeTranscricaoFalso("olá, este é o texto transcrito")

    resultado = cli.processar_audio("audio.wav", transcrever_audio=motor_falso)

    assert resultado == "olá, este é o texto transcrito"
    assert motor_falso.chamadas == ["audio.wav"]


# TC-2 — Rejeição por formato não suportado via CLI
def test_processar_audio_rejeita_formato_nao_suportado(monkeypatch):
    _finge_metadados(monkeypatch, formato="aac", duracao_segundos=60.0)
    motor_falso = _MotorDeTranscricaoFalso()

    with pytest.raises(ValueError, match=MOTIVO_FORMATO_NAO_SUPORTADO):
        cli.processar_audio("audio.aac", transcrever_audio=motor_falso)

    # TC-7: a rejeição não encaminha o áudio ao Motor de Transcrição.
    assert motor_falso.chamadas == []


# TC-3 — Rejeição por duração acima do limite via CLI
def test_processar_audio_rejeita_duracao_acima_do_limite(monkeypatch):
    _finge_metadados(monkeypatch, formato="wav", duracao_segundos=DURACAO_MAXIMA_SEGUNDOS + 1)
    motor_falso = _MotorDeTranscricaoFalso()

    with pytest.raises(ValueError, match=MOTIVO_DURACAO_EXCEDIDA):
        cli.processar_audio("audio.wav", transcrever_audio=motor_falso)

    # TC-7: a rejeição não encaminha o áudio ao Motor de Transcrição.
    assert motor_falso.chamadas == []


# TC-13 — Duração exatamente no limite de 10 minutos é aceita
def test_processar_audio_aceita_duracao_exatamente_no_limite(monkeypatch):
    _finge_metadados(monkeypatch, formato="flac", duracao_segundos=DURACAO_MAXIMA_SEGUNDOS)
    motor_falso = _MotorDeTranscricaoFalso("texto")

    resultado = cli.processar_audio("audio.flac", transcrever_audio=motor_falso)

    assert resultado == "texto"
    assert motor_falso.chamadas == ["audio.flac"]


# TC-11 — Uma chamada não tem acesso a dados de uma chamada anterior
def test_chamadas_independentes_nao_compartilham_estado(monkeypatch):
    _finge_metadados(monkeypatch, formato="aac", duracao_segundos=60.0)
    motor_falso = _MotorDeTranscricaoFalso()
    with pytest.raises(ValueError):
        cli.processar_audio("primeiro.aac", transcrever_audio=motor_falso)

    _finge_metadados(monkeypatch, formato="mp3", duracao_segundos=30.0)
    resultado = cli.processar_audio("segundo.mp3", transcrever_audio=motor_falso)

    # O segundo envio é aceito e processado sem nenhuma referência à rejeição
    # do primeiro; o dublê só registra a chamada do envio aceito.
    assert resultado == motor_falso.texto_transcrito
    assert motor_falso.chamadas == ["segundo.mp3"]


# TC-10 / TC-12 — Nenhum dado do áudio (aceito ou rejeitado) é persistido
def test_processar_audio_nao_escreve_nenhum_arquivo(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _finge_metadados(monkeypatch, formato="wav", duracao_segundos=120.0)
    cli.processar_audio("audio.wav", transcrever_audio=_MotorDeTranscricaoFalso())

    _finge_metadados(monkeypatch, formato="aac", duracao_segundos=60.0)
    with pytest.raises(ValueError):
        cli.processar_audio("audio.aac", transcrever_audio=_MotorDeTranscricaoFalso())

    assert list(tmp_path.iterdir()) == []


def test_main_imprime_texto_transcrito_e_devolve_zero(monkeypatch, capsys):
    _finge_metadados(monkeypatch, formato="wav", duracao_segundos=120.0)
    motor_falso = _MotorDeTranscricaoFalso("texto transcrito")

    codigo_saida = cli.main(["audio.wav"], transcrever_audio=motor_falso)

    saida = capsys.readouterr()
    assert codigo_saida == 0
    assert saida.out.strip() == "texto transcrito"


def test_main_informa_motivo_da_rejeicao_e_devolve_um(monkeypatch, capsys):
    _finge_metadados(monkeypatch, formato="aac", duracao_segundos=60.0)
    motor_falso = _MotorDeTranscricaoFalso()

    codigo_saida = cli.main(["audio.aac"], transcrever_audio=motor_falso)

    saida = capsys.readouterr()
    assert codigo_saida == 1
    assert MOTIVO_FORMATO_NAO_SUPORTADO in saida.err
    assert motor_falso.chamadas == []


def test_main_informa_causa_especifica_quando_motor_de_transcricao_falha(monkeypatch, capsys):
    from app.captura_ingestao.motor import FalhaTranscricao

    _finge_metadados(monkeypatch, formato="wav", duracao_segundos=120.0)

    def _motor_com_falha(caminho_arquivo):
        raise FalhaTranscricao("silencio")

    codigo_saida = cli.main(["audio.wav"], transcrever_audio=_motor_com_falha)

    saida = capsys.readouterr()
    assert codigo_saida == 1
    assert "silêncio" in saida.err.lower()
