"""Orquestração do domínio Motor de Transcrição: ponto de entrada consumido em
processo pelo domínio Captura e Ingestão de Áudio, logo após a validação de
formato e duração ser concluída com sucesso.

Decodifica o áudio recebido, detecta o idioma falado e, exclusivamente para
português (pt-BR), produz o texto transcrito pelo modelo Whisper `base`
local — ou classifica a causa da falha entre `idioma_nao_suportado`,
`silencio`, `ruido` e `falha_interna_motor` quando a transcrição não é
concluída com sucesso.
"""

import dataclasses
from typing import Callable, Optional, Protocol

import numpy as np
import whisper

from .classificacao_falha import classificar_falha

IDIOMA_ACEITO = "pt"

CAUSA_IDIOMA_NAO_SUPORTADO = "idioma_nao_suportado"
CAUSA_FALHA_INTERNA_MOTOR = "falha_interna_motor"

DecodificarAudio = Callable[[str], np.ndarray]


@dataclasses.dataclass(frozen=True)
class ResultadoTranscricao:
    """Resultado da transcrição: exatamente um de `texto` ou `causa_erro` é preenchido.

    `causa_erro`, quando preenchido, é um de `CAUSA_IDIOMA_NAO_SUPORTADO`,
    `classificacao_falha.CAUSA_SILENCIO`, `classificacao_falha.CAUSA_RUIDO`
    ou `CAUSA_FALHA_INTERNA_MOTOR` — as quatro causas distinguíveis exigidas
    pela skill do domínio. O domínio Captura e Ingestão de Áudio traduz este
    resultado para a resposta do canal de entrada que originou a chamada.
    """

    texto: Optional[str] = None
    causa_erro: Optional[str] = None


@dataclasses.dataclass(frozen=True)
class SaidaTranscricao:
    """Saída de uma tentativa de transcrição de um áudio já em português."""

    texto: str
    no_speech_prob: float
    confianca_media: float


class MotorWhisper(Protocol):
    """Interface do motor Whisper consumida pela orquestração deste módulo.

    Substituída nos testes por um dublê que devolve, de forma controlada, o
    idioma detectado, o texto transcrito e os sinais de confiança — sem
    carregar o modelo real —, conforme a estratégia de testes do `plan.md`.
    """

    def detectar_idioma(self, audio: np.ndarray) -> str: ...

    def transcrever(self, audio: np.ndarray) -> SaidaTranscricao: ...


class _MotorWhisperReal:
    """Adapta um modelo `openai-whisper` carregado à interface `MotorWhisper`."""

    def __init__(self, modelo):
        self._modelo = modelo

    def detectar_idioma(self, audio: np.ndarray) -> str:
        audio_para_deteccao = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(
            audio_para_deteccao, n_mels=self._modelo.dims.n_mels
        ).to(self._modelo.device)
        _, probabilidades = self._modelo.detect_language(mel)
        return max(probabilidades, key=probabilidades.get)

    def transcrever(self, audio: np.ndarray) -> SaidaTranscricao:
        resultado = self._modelo.transcribe(audio, language=IDIOMA_ACEITO)
        texto = (resultado.get("text") or "").strip()
        segmentos = resultado.get("segments") or []
        no_speech_prob = (
            sum(segmento.get("no_speech_prob", 1.0) for segmento in segmentos) / len(segmentos)
            if segmentos
            else 1.0
        )
        confianca_media = (
            sum(segmento.get("avg_logprob", -1.0) for segmento in segmentos) / len(segmentos)
            if segmentos
            else -1.0
        )
        return SaidaTranscricao(texto, no_speech_prob, confianca_media)


_modelo_carregado = None


def _carregar_motor() -> MotorWhisper:
    """Carrega (uma única vez, em cache no processo) o modelo Whisper `base`."""
    global _modelo_carregado
    if _modelo_carregado is None:
        _modelo_carregado = whisper.load_model("base")
    return _MotorWhisperReal(_modelo_carregado)


def _energia_rms(audio: np.ndarray) -> float:
    if audio.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(audio))))


def transcrever(
    caminho_arquivo: str,
    motor: Optional[MotorWhisper] = None,
    decodificar_audio: DecodificarAudio = whisper.load_audio,
) -> ResultadoTranscricao:
    """Decodifica, detecta o idioma e transcreve o áudio já validado, ou classifica a falha.

    `motor` (por padrão, o modelo Whisper `base` carregado em cache) e
    `decodificar_audio` (por padrão, `whisper.load_audio`, que depende do
    binário `ffmpeg`) são substituíveis nos testes por dublês de teste.

    A detecção de idioma ocorre antes de qualquer tentativa de transcrever:
    quando o idioma detectado não é português, `motor.transcrever` não é
    chamado. Qualquer exceção — na decodificação, na detecção de idioma ou
    na transcrição — é reportada como `CAUSA_FALHA_INTERNA_MOTOR`, sem
    propagar para quem chamou.
    """
    motor = motor if motor is not None else _carregar_motor()

    try:
        audio = decodificar_audio(caminho_arquivo)
        idioma_detectado = motor.detectar_idioma(audio)
    except Exception:
        return ResultadoTranscricao(causa_erro=CAUSA_FALHA_INTERNA_MOTOR)

    if idioma_detectado != IDIOMA_ACEITO:
        return ResultadoTranscricao(causa_erro=CAUSA_IDIOMA_NAO_SUPORTADO)

    try:
        saida = motor.transcrever(audio)
    except Exception:
        return ResultadoTranscricao(causa_erro=CAUSA_FALHA_INTERNA_MOTOR)

    if saida.texto:
        return ResultadoTranscricao(texto=saida.texto)

    causa = classificar_falha(_energia_rms(audio), saida.no_speech_prob, saida.confianca_media)
    return ResultadoTranscricao(causa_erro=causa)
