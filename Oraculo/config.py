import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variaveis de ambiente
load_dotenv()

# Diretorio base do projeto
BASE_DIR = Path(__file__).parent

class Config:
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Modelo LLM
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

    # Embeddings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # RAG Settings
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))

    # LLM Settings
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))

    # Paths
    CHROMA_PERSIST_DIR = str(BASE_DIR / "data" / "chroma_db")
    UPLOAD_DIR = str(BASE_DIR / "data" / "uploads")

    # Upload limits
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

    # Tipos de arquivo suportados
    SUPPORTED_EXTENSIONS = {
        'documents': ['.pdf', '.docx', '.txt', '.json'],
        'spreadsheets': ['.xlsx', '.csv'],
        'presentations': ['.pptx'],
        'images': ['.png', '.jpg', '.jpeg'],
        'web': ['site', 'youtube']
    }

    @classmethod
    def get_all_extensions(cls):
        """Retorna todas as extensoes suportadas"""
        extensions = []
        for ext_list in cls.SUPPORTED_EXTENSIONS.values():
            extensions.extend(ext_list)
        return [e for e in extensions if e.startswith('.')]

    @classmethod
    def is_configured(cls):
        """Verifica se a API key esta configurada"""
        return bool(cls.OPENAI_API_KEY and cls.OPENAI_API_KEY.startswith("sk-"))
