"""
Loader para imagens com OCR (Tesseract).
"""
import os
from typing import Optional


def verificar_tesseract() -> bool:
    """
    Verifica se o Tesseract esta instalado.

    Returns:
        True se instalado e funcionando
    """
    try:
        import pytesseract
        # Tenta obter a versao para verificar se funciona
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def carrega_imagem(caminho: str, idioma: str = 'por') -> str:
    """
    Extrai texto de uma imagem usando OCR (Tesseract).

    Args:
        caminho: Caminho da imagem
        idioma: Codigo do idioma (padrao: por = portugues)
                Outros: eng (ingles), spa (espanhol)

    Returns:
        Texto extraido da imagem

    Raises:
        ImportError: Se bibliotecas nao instaladas
        Exception: Se Tesseract nao instalado ou erro no processamento
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise ImportError(
            "Instale as bibliotecas necessarias: "
            "pip install pytesseract Pillow"
        ) from e

    # Verifica se Tesseract esta instalado
    if not verificar_tesseract():
        raise Exception(
            "Tesseract nao encontrado. Por favor, instale:\n"
            "Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "Apos instalar, adicione ao PATH do sistema."
        )

    try:
        # Abre a imagem
        imagem = Image.open(caminho)

        # Preprocessamento basico
        # Converte para RGB se necessario
        if imagem.mode != 'RGB':
            imagem = imagem.convert('RGB')

        # Executa OCR
        texto = pytesseract.image_to_string(imagem, lang=idioma)

        # Limpa o texto
        texto = texto.strip()

        if not texto:
            return "Nenhum texto encontrado na imagem."

        return texto

    except Exception as e:
        raise Exception(f"Erro ao processar imagem: {str(e)}")


def carrega_imagem_avancado(
    caminho: str,
    idioma: str = 'por',
    preprocessar: bool = True,
    config: Optional[str] = None
) -> str:
    """
    Extrai texto de uma imagem com opcoes avancadas.

    Args:
        caminho: Caminho da imagem
        idioma: Codigo do idioma
        preprocessar: Se deve aplicar preprocessamento
        config: Configuracao customizada do Tesseract

    Returns:
        Texto extraido
    """
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageFilter
    except ImportError as e:
        raise ImportError(
            "Instale as bibliotecas necessarias: "
            "pip install pytesseract Pillow"
        ) from e

    if not verificar_tesseract():
        raise Exception("Tesseract nao encontrado.")

    # Abre a imagem
    imagem = Image.open(caminho)

    # Converte para RGB
    if imagem.mode != 'RGB':
        imagem = imagem.convert('RGB')

    # Preprocessamento
    if preprocessar:
        # Converte para escala de cinza
        imagem = imagem.convert('L')

        # Aumenta contraste
        enhancer = ImageEnhance.Contrast(imagem)
        imagem = enhancer.enhance(2.0)

        # Remove ruido
        imagem = imagem.filter(ImageFilter.MedianFilter(size=3))

        # Binarizacao
        threshold = 128
        imagem = imagem.point(lambda x: 255 if x > threshold else 0)

    # Configuracao padrao otimizada
    if config is None:
        config = '--oem 3 --psm 6'

    # Executa OCR
    texto = pytesseract.image_to_string(imagem, lang=idioma, config=config)

    return texto.strip() or "Nenhum texto encontrado na imagem."


# Extensoes de imagem suportadas
EXTENSOES_IMAGEM = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']


def eh_imagem(caminho: str) -> bool:
    """
    Verifica se o arquivo e uma imagem suportada.

    Args:
        caminho: Caminho do arquivo

    Returns:
        True se for imagem suportada
    """
    extensao = os.path.splitext(caminho)[1].lower()
    return extensao in EXTENSOES_IMAGEM
