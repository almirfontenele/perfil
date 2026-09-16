import numpy as np
import pytest

from app.motor_transcricao.classificacao_falha import (
    CAUSA_RUIDO,
    CAUSA_SILENCIO,
    LIMIAR_ENERGIA_SILENCIO,
)
from app.motor_transcricao.transcricao import (
    CAUSA_FALHA_INTERNA_MOTOR,
    CAUSA_IDIOMA_NAO_SUPORTADO,
    SaidaTranscricao,
    transcrever,
)


class _MotorWhisperFalso:
    """Dublê de teste do motor Whisper: idioma, texto e sinais de confiança controlados.

    Substitui, nos testes deste módulo, a chamada ao modelo Whisper real —
    que não é carregado nesses casos —, conforme a estratégia de testes do
    `plan.md`.
    """

    def __init__(self, idioma_detectado, saida_transcricao=None, excecao_ao_transcrever=None):
        self.idioma_detectado = idioma_detectado
        self._saida_transcricao = saida_transcricao
        self._excecao_ao_transcrever = excecao_ao_transcrever
        self.chamadas_transcrever = 0

    def detectar_idioma(self, audio):
        return self.idioma_detectado

    def transcrever(self, audio):
        self.chamadas_transcrever += 1
        if self._excecao_ao_transcrever is not None:
            raise self._excecao_ao_transcrever
        return self._saida_transcricao


def _decodificar_audio_falso(energia_rms: float):
    """Dublê de `decodificar_audio`: devolve um áudio sintético com a energia (RMS) dada.

    Um array constante de valor `v` tem RMS igual a `abs(v)`, o que torna a
    energia resultante determinística e fácil de controlar nos testes.
    """

    def _decodificar(caminho_arquivo):
        return np.full(1000, energia_rms, dtype=np.float32)

    return _decodificar


# TC-1 — Transcrição concluída para áudio em português
def test_transcrever_devolve_texto_quando_idioma_e_portugues_e_ha_texto():
    motor_falso = _MotorWhisperFalso(
        idioma_detectado="pt",
        saida_transcricao=SaidaTranscricao(
            texto="olá, este é um texto de amostra", no_speech_prob=0.1, confianca_media=-0.2
        ),
    )

    resultado = transcrever(
        "audio.wav", motor=motor_falso, decodificar_audio=_decodificar_audio_falso(0.5)
    )

    assert resultado.texto == "olá, este é um texto de amostra"
    assert resultado.causa_erro is None


# TC-2 — Rejeição quando o idioma detectado não é português
def test_transcrever_rejeita_idioma_diferente_de_portugues_sem_transcrever():
    motor_falso = _MotorWhisperFalso(idioma_detectado="en")

    resultado = transcrever(
        "audio.wav", motor=motor_falso, decodificar_audio=_decodificar_audio_falso(0.5)
    )

    assert resultado.causa_erro == CAUSA_IDIOMA_NAO_SUPORTADO
    assert resultado.texto is None
    # A detecção de idioma ocorre antes de qualquer tentativa de transcrever.
    assert motor_falso.chamadas_transcrever == 0


# TC-4 — Falha por silêncio propagada pela orquestração
def test_transcrever_classifica_silencio_quando_transcricao_vazia_com_energia_baixa():
    motor_falso = _MotorWhisperFalso(
        idioma_detectado="pt",
        saida_transcricao=SaidaTranscricao(texto="", no_speech_prob=0.9, confianca_media=-3.0),
    )

    resultado = transcrever(
        "audio.wav",
        motor=motor_falso,
        decodificar_audio=_decodificar_audio_falso(LIMIAR_ENERGIA_SILENCIO / 2),
    )

    assert resultado.causa_erro == CAUSA_SILENCIO
    assert resultado.texto is None


# TC-6 — Falha por ruído propagada pela orquestração
def test_transcrever_classifica_ruido_quando_transcricao_vazia_com_energia_alta():
    motor_falso = _MotorWhisperFalso(
        idioma_detectado="pt",
        saida_transcricao=SaidaTranscricao(texto="", no_speech_prob=0.9, confianca_media=-3.0),
    )

    resultado = transcrever(
        "audio.wav",
        motor=motor_falso,
        decodificar_audio=_decodificar_audio_falso(LIMIAR_ENERGIA_SILENCIO * 10),
    )

    assert resultado.causa_erro == CAUSA_RUIDO
    assert resultado.texto is None


# TC-7 — Falha interna do motor durante a inferência
def test_transcrever_classifica_falha_interna_quando_motor_levanta_excecao():
    motor_falso = _MotorWhisperFalso(
        idioma_detectado="pt", excecao_ao_transcrever=RuntimeError("falha simulada de inferência")
    )

    resultado = transcrever(
        "audio.wav", motor=motor_falso, decodificar_audio=_decodificar_audio_falso(0.5)
    )

    assert resultado.causa_erro == CAUSA_FALHA_INTERNA_MOTOR
    assert resultado.texto is None


def test_transcrever_classifica_falha_interna_quando_decodificacao_levanta_excecao():
    # Ex.: `ffmpeg` ausente do PATH ao chamar `whisper.load_audio` de verdade.
    def _decodificar_com_erro(caminho_arquivo):
        raise RuntimeError("ffmpeg não encontrado")

    motor_falso = _MotorWhisperFalso(idioma_detectado="pt")

    resultado = transcrever(
        "audio.wav", motor=motor_falso, decodificar_audio=_decodificar_com_erro
    )

    assert resultado.causa_erro == CAUSA_FALHA_INTERNA_MOTOR
    assert resultado.texto is None
    assert motor_falso.chamadas_transcrever == 0


# TC-8 / TC-9 — Nenhum dado permanece após sucesso ou falha (função pura, sem I/O)
def test_transcrever_nao_escreve_nenhum_arquivo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    motor_falso = _MotorWhisperFalso(
        idioma_detectado="pt",
        saida_transcricao=SaidaTranscricao(texto="texto", no_speech_prob=0.1, confianca_media=-0.1),
    )

    transcrever("audio.wav", motor=motor_falso, decodificar_audio=_decodificar_audio_falso(0.5))

    assert list(tmp_path.iterdir()) == []


# TC-10 — Chamadas independentes não compartilham estado
def test_chamadas_independentes_nao_compartilham_estado():
    motor_sucesso = _MotorWhisperFalso(
        idioma_detectado="pt",
        saida_transcricao=SaidaTranscricao(
            texto="primeiro texto", no_speech_prob=0.1, confianca_media=-0.1
        ),
    )
    resultado_primeira_chamada = transcrever(
        "primeiro.wav", motor=motor_sucesso, decodificar_audio=_decodificar_audio_falso(0.5)
    )

    motor_idioma_nao_suportado = _MotorWhisperFalso(idioma_detectado="en")
    resultado_segunda_chamada = transcrever(
        "segundo.wav",
        motor=motor_idioma_nao_suportado,
        decodificar_audio=_decodificar_audio_falso(0.5),
    )

    assert resultado_primeira_chamada.texto == "primeiro texto"
    assert resultado_segunda_chamada.causa_erro == CAUSA_IDIOMA_NAO_SUPORTADO
    assert resultado_segunda_chamada.texto is None
