"""
Loader para arquivos de audio com transcricao via OpenAI Whisper.
"""
import os
from openai import OpenAI
from config import Config


# Extensoes de audio suportadas pelo Whisper
EXTENSOES_AUDIO = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg']


def eh_audio(caminho: str) -> bool:
    """
    Verifica se o arquivo e um audio suportado.

    Args:
        caminho: Caminho do arquivo

    Returns:
        True se for audio suportado
    """
    extensao = os.path.splitext(caminho)[1].lower()
    return extensao in EXTENSOES_AUDIO


def transcreve_audio(caminho: str, idioma: str = None) -> str:
    """
    Transcreve audio usando OpenAI Whisper API.

    Args:
        caminho: Caminho do arquivo de audio
        idioma: Codigo ISO-639-1 do idioma (opcional, ex: 'pt', 'en')
                Se nao especificado, Whisper detecta automaticamente

    Returns:
        Texto transcrito do audio

    Raises:
        Exception: Se houver erro na transcricao
    """
    if not Config.is_configured():
        raise Exception("API Key da OpenAI nao configurada")

    # Verifica tamanho do arquivo (limite Whisper: 25MB)
    file_size_mb = os.path.getsize(caminho) / (1024 * 1024)
    max_size = getattr(Config, 'MAX_AUDIO_SIZE_MB', 25)
    if file_size_mb > max_size:
        raise Exception(
            f"Arquivo de audio muito grande ({file_size_mb:.1f}MB). "
            f"Limite: {max_size}MB"
        )

    try:
        client = OpenAI(api_key=Config.OPENAI_API_KEY)

        with open(caminho, "rb") as audio_file:
            # Parametros da transcricao
            params = {
                "model": getattr(Config, 'WHISPER_MODEL', 'whisper-1'),
                "file": audio_file,
                "response_format": "text"
            }

            # Adiciona idioma se especificado
            if idioma:
                params["language"] = idioma

            transcricao = client.audio.transcriptions.create(**params)

        # Whisper retorna string quando response_format="text"
        texto = transcricao.strip() if isinstance(transcricao, str) else transcricao.text.strip()

        if not texto:
            return "Nenhuma fala detectada no audio."

        return texto

    except Exception as e:
        raise Exception(f"Erro ao transcrever audio: {str(e)}")
