import mutagen
import pytest

from app.captura_ingestao.metadados import Metadados, ler_metadados


class _InfoFalso:
    def __init__(self, duracao_segundos):
        self.length = duracao_segundos


def _arquivo_mutagen_falso(nome_classe, duracao_segundos):
    """Objeto com o mesmo nome de classe de um formato do mutagen e `.info.length`.

    Um dublê mais simples do que instanciar a classe real do mutagen, cujo
    `__init__`/`info` esperam um arquivo de verdade no disco.
    """
    classe_falsa = type(nome_classe, (), {})
    arquivo_falso = classe_falsa()
    arquivo_falso.info = _InfoFalso(duracao_segundos)
    return arquivo_falso


@pytest.mark.parametrize(
    ("nome_classe_mutagen", "formato_esperado"),
    [
        ("WAVE", "wav"),
        ("MP3", "mp3"),
        ("MP4", "m4a"),
        ("OggVorbis", "ogg"),
        ("OggOpus", "ogg"),
        ("FLAC", "flac"),
    ],
)
def test_ler_metadados_reconhece_formato_de_cada_classe_do_mutagen(
    monkeypatch, nome_classe_mutagen, formato_esperado
):
    arquivo_falso = _arquivo_mutagen_falso(nome_classe_mutagen, duracao_segundos=90.0)
    monkeypatch.setattr(mutagen, "File", lambda caminho: arquivo_falso)

    metadados = ler_metadados("qualquer-caminho")

    assert metadados == Metadados(formato=formato_esperado, duracao_segundos=90.0)


def test_ler_metadados_preserva_duracao_exatamente_no_limite(monkeypatch):
    arquivo_falso = _arquivo_mutagen_falso("WAVE", duracao_segundos=600.0)
    monkeypatch.setattr(mutagen, "File", lambda caminho: arquivo_falso)

    metadados = ler_metadados("audio.wav")

    assert metadados.duracao_segundos == 600.0


def test_ler_metadados_formato_nao_reconhecido_pelo_mutagen(monkeypatch):
    # `mutagen.File` devolve `None` quando não reconhece o contêiner do arquivo.
    monkeypatch.setattr(mutagen, "File", lambda caminho: None)

    metadados = ler_metadados("audio.aac")

    assert metadados.formato == "aac"
    # Duração não importa aqui: a rejeição por formato ocorre antes da checagem
    # de duração em `validacao.validar`.


def test_ler_metadados_formato_nao_reconhecido_sem_extensao(monkeypatch):
    monkeypatch.setattr(mutagen, "File", lambda caminho: None)

    metadados = ler_metadados("audio-sem-extensao")

    assert metadados.formato == "desconhecido"


def test_ler_metadados_formato_cuja_extensao_falha_ao_ser_interpretada(monkeypatch):
    # Para algumas extensões (ex.: .aac), o mutagen tenta interpretar o
    # conteúdo pelo formato sugerido pelo nome do arquivo e levanta
    # `MutagenError` em vez de devolver `None` quando o conteúdo não bate.
    def _file_com_erro(caminho):
        raise mutagen.MutagenError("sync not found")

    monkeypatch.setattr(mutagen, "File", _file_com_erro)

    metadados = ler_metadados("audio.aac")

    assert metadados.formato == "aac"
