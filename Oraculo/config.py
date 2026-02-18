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
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1500"))       # Preserva paragrafos completos
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))  # ~13% sobreposicao semantica
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "8"))    # Mais contexto disponivel
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))  # Filtro de qualidade

    # LLM Settings
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))    # Mais preciso e consistente
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))       # Respostas mais completas

    # Paths
    CHROMA_PERSIST_DIR = str(BASE_DIR / "data" / "chroma_db")
    UPLOAD_DIR = str(BASE_DIR / "data" / "uploads")

    # Upload limits
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

    # Proxy para YouTube (para contornar bloqueio de IP de cloud)
    YOUTUBE_PROXY = os.getenv("YOUTUBE_PROXY", "")

    # Supadata API Key (alternativa para transcrição do YouTube)
    SUPADATA_API_KEY = os.getenv("SUPADATA_API_KEY", "")

    # Audio Settings (Whisper)
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
    MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "25"))

    # Tipos de arquivo suportados
    SUPPORTED_EXTENSIONS = {
        'documents': ['.pdf', '.docx', '.txt', '.json'],
        'spreadsheets': ['.xlsx', '.csv'],
        'presentations': ['.pptx'],
        'images': ['.png', '.jpg', '.jpeg'],
        'audio': ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg'],
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
