# Loaders module - Document processing
from loaders.documents import (
    carrega_pdf,
    carrega_txt,
    carrega_csv,
    carrega_docx,
    carrega_xlsx,
    carrega_pptx,
    carrega_json,
    carrega_documento,
    LOADERS_DOCUMENTOS
)
from loaders.web import (
    carrega_site,
    carrega_youtube,
    carrega_url,
    detecta_tipo_url
)
from loaders.images import (
    carrega_imagem,
    verificar_tesseract,
    eh_imagem,
    EXTENSOES_IMAGEM
)
