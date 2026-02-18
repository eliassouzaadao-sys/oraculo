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
    Carrega conteudo de um site preservando estrutura.
    Tenta extrair com estrutura (headings, listas), com fallback para WebBaseLoader.

    Args:
        url: URL do site
        max_tentativas: Numero maximo de tentativas

    Returns:
        Texto extraido do site com estrutura preservada

    Raises:
        Exception: Se nao conseguir carregar apos todas tentativas
    """
    documento = ''
    ultimo_erro = None

    for i in range(max_tentativas):
        try:
            # Define user agent aleatorio para evitar bloqueios
            os.environ['USER_AGENT'] = UserAgent().random

            # Tenta extrair com estrutura preservada
            documento = _carrega_site_estruturado(url)

            # Verifica se o conteudo e valido
            if documento and len(documento.strip()) > 100:
                return documento

            # Fallback para WebBaseLoader basico
            loader = WebBaseLoader(url, raise_for_status=True)
            lista_documentos = loader.load()
            documento = '\n\n'.join([doc.page_content for doc in lista_documentos])

            if documento and len(documento.strip()) > 100:
                return documento

        except Exception as e:
            ultimo_erro = e
            print(f'Tentativa {i + 1} falhou: {str(e)[:100]}')
            sleep(3)

    if documento:
        return documento

    raise Exception(f"Nao foi possivel carregar o site apos {max_tentativas} tentativas. Erro: {ultimo_erro}")


def _carrega_site_estruturado(url: str) -> str:
    """
    Carrega site preservando estrutura de headings, listas e paragrafos.

    Args:
        url: URL do site

    Returns:
        Texto estruturado em Markdown
    """
    import requests
    from bs4 import BeautifulSoup

    headers = {'User-Agent': UserAgent().random}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Remove elementos que nao sao conteudo
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'noscript']):
        tag.decompose()

    partes = []

    # Processa elementos na ordem que aparecem
    for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'pre', 'code', 'blockquote']):
        tag_name = elem.name
        text = elem.get_text(strip=True)

        if not text or len(text) < 3:
            continue

        # Headings viram markdown
        if tag_name.startswith('h'):
            level = int(tag_name[1])
            partes.append(f"\n{'#' * level} {text}\n")

        # Listas
        elif tag_name == 'li':
            partes.append(f"- {text}")

        # Codigo
        elif tag_name in ['pre', 'code']:
            partes.append(f"\n```\n{text}\n```\n")

        # Citacoes
        elif tag_name == 'blockquote':
            partes.append(f"> {text}")

        # Paragrafos normais
        else:
            partes.append(text)

    return '\n'.join(partes)


def _formata_transcricao_com_timestamps(segmentos: list) -> str:
    """
    Formata transcricao incluindo timestamps para referencia.
    Agrupa segmentos em blocos de ~30 segundos para nao poluir muito.

    Args:
        segmentos: Lista de dicts com 'text' e 'start' (segundos)

    Returns:
        Transcricao formatada com timestamps [MM:SS]
    """
    if not segmentos:
        return ""

    partes = []
    ultimo_timestamp_marcado = -30  # Marca timestamp a cada ~30 segundos

    for seg in segmentos:
        texto = seg.get("text", "").strip()
        start = seg.get("start", 0)

        if not texto:
            continue

        # Adiciona timestamp se passou 30 segundos desde o ultimo
        if start - ultimo_timestamp_marcado >= 30:
            minutos = int(start // 60)
            segundos = int(start % 60)
            partes.append(f"\n[{minutos:02d}:{segundos:02d}] {texto}")
            ultimo_timestamp_marcado = start
        else:
            partes.append(texto)

    return " ".join(partes)


def carrega_youtube(url_ou_id: str, idioma: str = 'pt') -> str:
    """
    Carrega transcricao de um video do YouTube.
    Preserva timestamps para referencia temporal.
    Usa Supadata API como metodo principal, youtube-transcript-api como fallback.
    """
    import requests
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import Config

    video_id = _extrair_video_id(url_ou_id)
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    # Metodo 1: Supadata API (funciona de servidores cloud)
    supadata_key = Config.SUPADATA_API_KEY
    if supadata_key:
        try:
            response = requests.get(
                "https://api.supadata.ai/v1/youtube/transcript",
                headers={"x-api-key": supadata_key},
                params={"url": video_url, "lang": idioma},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if "content" in data:
                    # Formato novo: lista de segmentos com timestamps
                    if isinstance(data["content"], list):
                        return _formata_transcricao_com_timestamps(data["content"])
                    else:
                        return data["content"]
                elif "transcript" in data:
                    return data["transcript"]
            else:
                print(f"[Supadata] Erro {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"[Supadata] Falhou: {str(e)[:100]}")

    # Metodo 2: youtube-transcript-api com proxy (fallback)
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig

        idiomas_tentativa = [idioma, 'pt-BR', 'pt', 'en', 'en-US']
        transcript = None

        proxy_url = Config.YOUTUBE_PROXY
        if proxy_url:
            if proxy_url.startswith("webshare:"):
                parts = proxy_url.split(":")
                if len(parts) >= 3:
                    ytt_api = YouTubeTranscriptApi(proxy_config=WebshareProxyConfig(parts[1], parts[2]))
                else:
                    ytt_api = YouTubeTranscriptApi()
            else:
                ytt_api = YouTubeTranscriptApi(proxy_config=GenericProxyConfig(https_url=proxy_url))
        else:
            ytt_api = YouTubeTranscriptApi()

        try:
            transcript = ytt_api.fetch(video_id, languages=idiomas_tentativa)
        except:
            transcript = ytt_api.fetch(video_id)

        if not transcript:
            raise Exception("Nenhuma transcricao encontrada para este video")

        # Concatena o texto da transcricao preservando timestamps
        # A nova API retorna FetchedTranscriptSnippet, a antiga retorna lista de dicts
        segmentos = []
        for entry in transcript:
            if hasattr(entry, 'text') and hasattr(entry, 'start'):
                segmentos.append({"text": entry.text, "start": entry.start})
            elif isinstance(entry, dict):
                segmentos.append({
                    "text": entry.get('text', ''),
                    "start": entry.get('start', 0)
                })
            else:
                segmentos.append({"text": str(entry), "start": 0})

        documento = _formata_transcricao_com_timestamps(segmentos)
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
    """
    # Se ja for apenas o ID (sem barras e tamanho razoavel)
    if '/' not in url_ou_id and len(url_ou_id) <= 15:
        return url_ou_id

    import re
    # Padroes de URL do YouTube (aceita IDs de 8-15 caracteres)
    padroes = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{8,15})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{8,15})',
        r'[?&]v=([a-zA-Z0-9_-]{8,15})',
    ]

    for padrao in padroes:
        match = re.search(padrao, url_ou_id)
        if match:
            return match.group(1)

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
