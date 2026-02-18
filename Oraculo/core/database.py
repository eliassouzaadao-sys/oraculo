"""
Gerenciamento do banco de dados de conhecimento.
Usa armazenamento em arquivo JSON com embeddings da OpenAI.
"""
import os
import json
import numpy as np
from datetime import datetime
from typing import List, Optional, Tuple
from dataclasses import dataclass, asdict
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config


@dataclass
class Documento:
    """Representa um chunk de documento."""
    id: str
    content: str
    embedding: List[float]
    source: str
    type: str
    upload_date: str
    chunk_index: int
    total_chunks: int
    # Metadados opcionais para preservar contexto
    page_number: Optional[int] = None           # Para PDFs
    timestamp_start: Optional[float] = None     # Para audio/video (segundos)
    timestamp_end: Optional[float] = None       # Para audio/video (segundos)
    heading_context: Optional[str] = None       # Titulo/secao do chunk
    content_type: str = "text"                  # text, table, code, list
    sector_id: str = "default"                  # ID do setor (isolamento por setor)


class KnowledgeBase:
    """Gerencia a base de conhecimento com armazenamento em arquivo."""

    def __init__(self):
        self._embeddings = None
        self._documentos: List[Documento] = []
        self._db_path = os.path.join(Config.CHROMA_PERSIST_DIR, "knowledge_base.json")
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self._carregar_db()

    @property
    def embeddings(self):
        """Lazy loading dos embeddings."""
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                model=Config.EMBEDDING_MODEL,
                api_key=Config.OPENAI_API_KEY
            )
        return self._embeddings

    def _carregar_db(self):
        """Carrega o banco de dados do arquivo."""
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

        if os.path.exists(self._db_path):
            try:
                with open(self._db_path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    self._documentos = [Documento(**d) for d in dados]
            except Exception as e:
                print(f"Erro ao carregar DB: {e}")
                self._documentos = []
        else:
            self._documentos = []

    def _salvar_db(self):
        """Salva o banco de dados no arquivo."""
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

        with open(self._db_path, 'w', encoding='utf-8') as f:
            dados = [asdict(d) for d in self._documentos]
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def adicionar_documento(self, texto: str, fonte: str, tipo: str, sector_id: str = "default") -> int:
        """
        Adiciona um documento a base de conhecimento.

        Args:
            texto: Conteudo do documento
            fonte: Nome/URL da fonte
            tipo: Tipo do arquivo (pdf, docx, site, etc)
            sector_id: ID do setor para isolamento

        Returns:
            Numero de chunks adicionados
        """
        # Divide o texto em chunks
        chunks = self._splitter.split_text(texto)

        if not chunks:
            return 0

        # Gera embeddings para todos os chunks
        embeddings = self.embeddings.embed_documents(chunks)

        # Cria documentos
        timestamp = datetime.now().isoformat()
        base_id = f"{fonte}_{timestamp}"

        novos_docs = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            doc = Documento(
                id=f"{base_id}_{i}",
                content=chunk,
                embedding=emb,
                source=fonte,
                type=tipo,
                upload_date=timestamp,
                chunk_index=i,
                total_chunks=len(chunks),
                sector_id=str(sector_id)
            )
            novos_docs.append(doc)

        self._documentos.extend(novos_docs)
        self._salvar_db()

        return len(novos_docs)

    def buscar(self, pergunta: str, sector_id: str = None, k: Optional[int] = None, threshold: Optional[float] = None) -> List[dict]:
        """
        Busca documentos relevantes para a pergunta.
        Filtra resultados por threshold de similaridade para garantir qualidade.

        Args:
            pergunta: Pergunta do usuario
            sector_id: ID do setor para filtrar (None = todos)
            k: Numero de resultados (padrao: TOP_K_RESULTS)
            threshold: Similaridade minima (padrao: SIMILARITY_THRESHOLD)

        Returns:
            Lista de documentos relevantes ordenados por score
        """
        if k is None:
            k = Config.TOP_K_RESULTS
        if threshold is None:
            threshold = Config.SIMILARITY_THRESHOLD

        # Filtra por setor se especificado
        documentos = self._documentos
        if sector_id is not None:
            documentos = [d for d in documentos if str(getattr(d, 'sector_id', 'default')) == str(sector_id)]

        if not documentos:
            return []

        # Gera embedding da pergunta
        query_embedding = self.embeddings.embed_query(pergunta)

        # Calcula similaridade com todos os documentos
        resultados = []
        for doc in documentos:
            score = self._cosine_similarity(query_embedding, doc.embedding)
            resultados.append((doc, score))

        # Ordena por similaridade (maior primeiro)
        resultados.sort(key=lambda x: x[1], reverse=True)

        # Filtra por threshold de qualidade
        resultados_filtrados = [(doc, score) for doc, score in resultados if score >= threshold]

        # Se poucos resultados passaram no threshold, relaxa o filtro
        # para garantir que sempre haja algum contexto
        if len(resultados_filtrados) < 3 and len(resultados) >= 3:
            resultados_filtrados = resultados[:k]
        else:
            resultados_filtrados = resultados_filtrados[:k]

        # Retorna com metadados expandidos
        return [
            {
                "content": doc.content,
                "source": doc.source,
                "type": doc.type,
                "score": score,
                "page_number": doc.page_number,
                "timestamp_start": doc.timestamp_start,
                "heading_context": doc.heading_context,
                "content_type": doc.content_type
            }
            for doc, score in resultados_filtrados
        ]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similaridade de cosseno entre dois vetores."""
        a = np.array(vec1)
        b = np.array(vec2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def get_estatisticas(self, sector_id: str = None) -> dict:
        """
        Retorna estatisticas da base de conhecimento.

        Args:
            sector_id: ID do setor para filtrar (None = todos)

        Returns:
            Dicionario com estatisticas
        """
        # Filtra por setor se especificado
        documentos = self._documentos
        if sector_id is not None:
            documentos = [d for d in documentos if str(getattr(d, 'sector_id', 'default')) == str(sector_id)]

        if not documentos:
            return {
                "total_chunks": 0,
                "total_documentos": 0,
                "fontes": [],
                "tipos": {}
            }

        fontes = set(d.source for d in documentos)
        tipos = {}
        for d in documentos:
            tipos[d.type] = tipos.get(d.type, 0) + 1

        return {
            "total_chunks": len(documentos),
            "total_documentos": len(fontes),
            "fontes": list(fontes),
            "tipos": tipos
        }

    def limpar_base(self, sector_id: str = None) -> bool:
        """
        Remove documentos da base.

        Args:
            sector_id: ID do setor para limpar (None = limpa todos)

        Returns:
            True se sucesso
        """
        try:
            if sector_id is not None:
                # Remove apenas documentos do setor
                self._documentos = [
                    d for d in self._documentos
                    if str(getattr(d, 'sector_id', 'default')) != str(sector_id)
                ]
            else:
                # Remove todos
                self._documentos = []
            self._salvar_db()
            return True
        except Exception:
            return False

    def remover_documento(self, fonte: str, sector_id: str = None) -> bool:
        """
        Remove um documento especifico da base.

        Args:
            fonte: Nome/URL da fonte a remover
            sector_id: ID do setor (None = remove de todos os setores)

        Returns:
            True se sucesso
        """
        try:
            if sector_id is not None:
                # Remove apenas do setor especificado
                self._documentos = [
                    d for d in self._documentos
                    if not (d.source == fonte and str(getattr(d, 'sector_id', 'default')) == str(sector_id))
                ]
            else:
                # Remove de todos os setores
                self._documentos = [d for d in self._documentos if d.source != fonte]
            self._salvar_db()
            return True
        except Exception:
            return False


# Instancia global (singleton)
_knowledge_base = None


def get_knowledge_base() -> KnowledgeBase:
    """Retorna instancia singleton da base de conhecimento."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base
