import asyncio
import io
import os
import struct
import wave
from pathlib import Path

import pytest
import yaml
from fastapi import HTTPException, UploadFile
from openapi_spec_validator import validate

from app.captura_ingestao import api, cli
from app.captura_ingestao.api import processar_upload
from app.captura_ingestao.validacao import (
    DURACAO_MAXIMA_SEGUNDOS,
    MOTIVO_DURACAO_EXCEDIDA,
    MOTIVO_FORMATO_NAO_SUPORTADO,
)

RAIZ_DO_REPOSITORIO = Path(__file__).resolve().parents[2]


class _MotorDeTranscricaoFalso:
    """Dublê de teste do domínio Motor de Transcrição (mesmo papel de `test_cli.py`)."""

    def __init__(self, texto_transcrito="texto transcrito de teste"):
        self.texto_transcrito = texto_transcrito
        self.chamadas = []

    def __call__(self, caminho_arquivo):
        self.chamadas.append(caminho_arquivo)
        return self.texto_transcrito


def _wav_em_memoria(duracao_segundos: float) -> bytes:
    frequencia_amostragem = 8000
    n_amostras = int(duracao_segundos * frequencia_amostragem)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(frequencia_amostragem)
        w.writeframes(struct.pack(f"<{n_amostras}h", *([0] * n_amostras)))
    return buf.getvalue()


def _upload(conteudo: bytes, nome_arquivo: str) -> UploadFile:
    return UploadFile(file=io.BytesIO(conteudo), filename=nome_arquivo)


def _processar(upload: UploadFile, transcrever_audio) -> str:
    return asyncio.run(processar_upload(upload, transcrever_audio=transcrever_audio))


# TC-4 — Envio bem-sucedido via API HTTP
def test_processar_upload_aceito_devolve_texto_transcrito():
    upload = _upload(_wav_em_memoria(1.0), "audio.wav")
    motor_falso = _MotorDeTranscricaoFalso("olá, este é o texto transcrito")

    resultado = _processar(upload, motor_falso)

    assert resultado == "olá, este é o texto transcrito"
    assert len(motor_falso.chamadas) == 1


# TC-5 — Rejeição por formato não suportado via API HTTP
def test_processar_upload_rejeita_formato_nao_suportado():
    upload = _upload(b"conteudo que nao e um audio valido", "audio.aac")
    motor_falso = _MotorDeTranscricaoFalso()

    with pytest.raises(HTTPException) as excecao:
        _processar(upload, motor_falso)

    assert excecao.value.status_code == 400
    assert excecao.value.detail == MOTIVO_FORMATO_NAO_SUPORTADO
    # TC-8: a rejeição não encaminha o áudio ao Motor de Transcrição.
    assert motor_falso.chamadas == []


# TC-6 — Rejeição por duração acima do limite via API HTTP
def test_processar_upload_rejeita_duracao_acima_do_limite():
    upload = _upload(_wav_em_memoria(DURACAO_MAXIMA_SEGUNDOS + 1), "audio.wav")
    motor_falso = _MotorDeTranscricaoFalso()

    with pytest.raises(HTTPException) as excecao:
        _processar(upload, motor_falso)

    assert excecao.value.status_code == 422
    assert excecao.value.detail == MOTIVO_DURACAO_EXCEDIDA
    # TC-8: a rejeição não encaminha o áudio ao Motor de Transcrição.
    assert motor_falso.chamadas == []


# TC-9 — Mesmo critério de validação nos dois canais (CLI e API HTTP)
def test_mesmo_audio_e_aceito_com_o_mesmo_resultado_nos_dois_canais(tmp_path):
    conteudo_wav = _wav_em_memoria(30.0)
    motor_falso_http = _MotorDeTranscricaoFalso("texto transcrito")
    motor_falso_cli = _MotorDeTranscricaoFalso("texto transcrito")

    resultado_http = _processar(_upload(conteudo_wav, "audio.wav"), motor_falso_http)

    caminho_local = tmp_path / "audio.wav"
    caminho_local.write_bytes(conteudo_wav)
    resultado_cli = cli.processar_audio(str(caminho_local), transcrever_audio=motor_falso_cli)

    assert resultado_http == resultado_cli == "texto transcrito"


# TC-11 — Uma chamada não tem acesso a dados de uma chamada anterior
def test_chamadas_independentes_nao_compartilham_estado():
    motor_falso = _MotorDeTranscricaoFalso()
    with pytest.raises(HTTPException):
        _processar(_upload(b"conteudo invalido", "primeiro.aac"), motor_falso)

    resultado = _processar(_upload(_wav_em_memoria(1.0), "segundo.wav"), motor_falso)

    # O segundo envio é aceito e processado sem nenhuma referência à rejeição
    # do primeiro; o dublê só registra a chamada do envio aceito.
    assert resultado == motor_falso.texto_transcrito
    assert len(motor_falso.chamadas) == 1


# TC-10 — Nenhum dado do áudio recebido é persistido após um envio aceito
def test_processar_upload_apaga_arquivo_temporario_apos_sucesso(monkeypatch):
    caminhos_vistos = []
    ler_metadados_original = api.ler_metadados

    def _espiao_ler_metadados(caminho_arquivo):
        caminhos_vistos.append(caminho_arquivo)
        return ler_metadados_original(caminho_arquivo)

    monkeypatch.setattr(api, "ler_metadados", _espiao_ler_metadados)

    _processar(_upload(_wav_em_memoria(1.0), "audio.wav"), _MotorDeTranscricaoFalso())

    assert len(caminhos_vistos) == 1
    assert not os.path.exists(caminhos_vistos[0])


# TC-12 — Nenhum dado é persistido mesmo quando o áudio é rejeitado
def test_processar_upload_apaga_arquivo_temporario_mesmo_quando_rejeitado(monkeypatch):
    caminhos_vistos = []
    ler_metadados_original = api.ler_metadados

    def _espiao_ler_metadados(caminho_arquivo):
        caminhos_vistos.append(caminho_arquivo)
        return ler_metadados_original(caminho_arquivo)

    monkeypatch.setattr(api, "ler_metadados", _espiao_ler_metadados)

    with pytest.raises(HTTPException):
        _processar(_upload(b"conteudo invalido", "audio.aac"), _MotorDeTranscricaoFalso())

    assert len(caminhos_vistos) == 1
    assert not os.path.exists(caminhos_vistos[0])


@pytest.mark.parametrize(
    ("causa", "status_esperado"),
    [
        ("idioma_nao_suportado", 422),
        ("silencio", 422),
        ("ruido", 422),
        ("falha_interna_motor", 500),
    ],
)
def test_processar_upload_traduz_falha_transcricao_no_status_e_detail_corretos(
    causa, status_esperado
):
    from app.captura_ingestao.motor import FalhaTranscricao, MENSAGENS_POR_CAUSA

    def _motor_com_falha(caminho_arquivo):
        raise FalhaTranscricao(causa)

    with pytest.raises(HTTPException) as excecao:
        _processar(_upload(_wav_em_memoria(1.0), "audio.wav"), _motor_com_falha)

    assert excecao.value.status_code == status_esperado
    assert excecao.value.detail == MENSAGENS_POR_CAUSA[causa]


def test_openapi_yaml_e_estruturalmente_valido():
    caminho_openapi = RAIZ_DO_REPOSITORIO / "openapi.yaml"
    especificacao = yaml.safe_load(caminho_openapi.read_text())

    validate(especificacao)


def test_openapi_yaml_documenta_a_rota_de_upload_com_todos_os_casos_de_resposta():
    caminho_openapi = RAIZ_DO_REPOSITORIO / "openapi.yaml"
    especificacao = yaml.safe_load(caminho_openapi.read_text())

    respostas = especificacao["paths"]["/transcricoes"]["post"]["responses"]
    assert set(respostas.keys()) == {"200", "400", "422", "500"}
