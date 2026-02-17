"""
Loaders para conteudo web: Sites e YouTube.
"""
import os
from time import sleep
from typing import Optional
from langchain_community.document_loaders import WebBaseLoader, YoutubeLoader
from fake_useragent import UserAgent


def carrega_site(url: str, max_tentativas: int = 5) -> str:
    """
    Carrega conteudo de um site.

    Args:
        url: URL do site
        max_tentativas: Numero maximo de tentativas

    Returns:
        Texto extraido do site

    Raises:
        Exception: Se nao conseguir carregar apos todas tentativas
    """
    documento = ''
    ultimo_erro = None

    for i in range(max_tentativas):
        try:
            # Define user agent aleatorio para evitar bloqueios
            os.environ['USER_AGENT'] = UserAgent().random

            loader = WebBaseLoader(url, raise_for_status=True)
            lista_documentos = loader.load()
            documento = '\n\n'.join([doc.page_content for doc in lista_documentos])

            # Verifica se o conteudo e valido
            if documento and len(documento.strip()) > 100:
                return documento

        except Exception as e:
            ultimo_erro = e
            print(f'Tentativa {i + 1} falhou: {str(e)[:100]}')
            sleep(3)

    if documento:
        return documento

    raise Exception(f"Nao foi possivel carregar o site apos {max_tentativas} tentativas. Erro: {ultimo_erro}")


def carrega_youtube(url_ou_id: str, idioma: str = 'pt') -> str:
    """
    Carrega transcricao de um video do YouTube.

    Args:
        url_ou_id: URL completa ou ID do video
        idioma: Codigo do idioma para legendas (padrao: pt)

    Returns:
        Transcricao do video

    Raises:
        Exception: Se nao conseguir carregar a transcricao
    """
    # Extrai o video ID se for URL completa
    video_id = _extrair_video_id(url_ou_id)

    # Tenta usar youtube-transcript-api diretamente (mais confiavel)
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, FetchedTranscript

        # Tenta diferentes idiomas
        idiomas_tentativa = [idioma, 'pt-BR', 'pt', 'en', 'en-US']

        transcript = None

        # Nova API (v1.x): usa fetch() diretamente
        try:
            ytt_api = YouTubeTranscriptApi()
            transcript = ytt_api.fetch(video_id, languages=idiomas_tentativa)
        except Exception as e1:
            # Tenta sem especificar idioma
            try:
                transcript = ytt_api.fetch(video_id)
            except Exception as e2:
                # Fallback para API antiga (v0.x)
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=idiomas_tentativa)
                except:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id)

        if not transcript:
            raise Exception("Nenhuma transcricao encontrada para este video")

        # Concatena o texto da transcricao
        # A nova API retorna FetchedTranscriptSnippet com .text, a antiga retorna lista de dicts
        textos = []
        for entry in transcript:
            if hasattr(entry, 'text'):
                textos.append(entry.text)
            elif isinstance(entry, dict):
                textos.append(entry.get('text', ''))
            else:
                textos.append(str(entry))
        documento = ' '.join(textos)

        return documento

    except ImportError:
        # Fallback para YoutubeLoader do LangChain
        try:
            loader = YoutubeLoader(
                video_id,
                add_video_info=False,
                language=[idioma, 'pt-BR', 'en']
            )
            lista_documentos = loader.load()

            if not lista_documentos:
                raise Exception("Nenhuma transcricao encontrada para este video")

            documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
            return documento
        except Exception as e:
            raise Exception(f"Erro ao carregar video do YouTube: {str(e)}")

    except Exception as e:
        error_msg = str(e)
        if "TranscriptsDisabled" in error_msg or "disabled" in error_msg.lower():
            raise Exception("Este video nao possui legendas/transcricao disponivel")
        elif "NoTranscriptFound" in error_msg or "not find" in error_msg.lower():
            raise Exception("Nenhuma transcricao encontrada para este video")
        elif "VideoUnavailable" in error_msg or "unavailable" in error_msg.lower():
            raise Exception("Video indisponivel ou privado")
        else:
            raise Exception(f"Erro ao carregar video do YouTube: {error_msg}")


def _extrair_video_id(url_ou_id: str) -> str:
    """
    Extrai o ID do video de uma URL do YouTube.

    Args:
        url_ou_id: URL ou ID do video

    Returns:
        ID do video
    """
    # Se ja for apenas o ID
    if len(url_ou_id) == 11 and '/' not in url_ou_id:
        return url_ou_id

    # Padroes de URL do YouTube
    import re

    padroes = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]

    for padrao in padroes:
        match = re.search(padrao, url_ou_id)
        if match:
            return match.group(1)

    # Se nenhum padrao encontrado, assume que e o proprio ID
    return url_ou_id


def detecta_tipo_url(url: str) -> Optional[str]:
    """
    Detecta o tipo de conteudo baseado na URL.

    Args:
        url: URL a analisar

    Returns:
        'youtube', 'site' ou None se invalido
    """
    url_lower = url.lower()

    # YouTube
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'

    # Site generico
    if url_lower.startswith(('http://', 'https://')):
        return 'site'

    return None


def carrega_url(url: str) -> tuple[str, str]:
    """
    Carrega conteudo de uma URL, detectando automaticamente o tipo.

    Args:
        url: URL do conteudo

    Returns:
        Tupla (conteudo, tipo)

    Raises:
        ValueError: Se URL invalida
    """
    tipo = detecta_tipo_url(url)

    if tipo == 'youtube':
        return carrega_youtube(url), 'youtube'
    elif tipo == 'site':
        return carrega_site(url), 'site'
    else:
        raise ValueError(f"URL invalida ou tipo nao suportado: {url}")
