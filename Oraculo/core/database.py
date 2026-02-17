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

    def adicionar_documento(self, texto: str, fonte: str, tipo: str) -> int:
        """
        Adiciona um documento a base de conhecimento.

        Args:
            texto: Conteudo do documento
            fonte: Nome/URL da fonte
            tipo: Tipo do arquivo (pdf, docx, site, etc)

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
                total_chunks=len(chunks)
            )
            novos_docs.append(doc)

        self._documentos.extend(novos_docs)
        self._salvar_db()

        return len(novos_docs)

    def buscar(self, pergunta: str, k: Optional[int] = None) -> List[dict]:
        """
        Busca documentos relevantes para a pergunta.

        Args:
            pergunta: Pergunta do usuario
            k: Numero de resultados (padrao: TOP_K_RESULTS)

        Returns:
            Lista de documentos relevantes
        """
        if k is None:
            k = Config.TOP_K_RESULTS

        if not self._documentos:
            return []

        # Gera embedding da pergunta
        query_embedding = self.embeddings.embed_query(pergunta)

        # Calcula similaridade com todos os documentos
        resultados = []
        for doc in self._documentos:
            score = self._cosine_similarity(query_embedding, doc.embedding)
            resultados.append((doc, score))

        # Ordena por similaridade (maior primeiro)
        resultados.sort(key=lambda x: x[1], reverse=True)

        # Retorna top k
        return [
            {
                "content": doc.content,
                "source": doc.source,
                "type": doc.type,
                "score": score
            }
            for doc, score in resultados[:k]
        ]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similaridade de cosseno entre dois vetores."""
        a = np.array(vec1)
        b = np.array(vec2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def get_estatisticas(self) -> dict:
        """
        Retorna estatisticas da base de conhecimento.

        Returns:
            Dicionario com estatisticas
        """
        if not self._documentos:
            return {
                "total_chunks": 0,
                "total_documentos": 0,
                "fontes": [],
                "tipos": {}
            }

        fontes = set(d.source for d in self._documentos)
        tipos = {}
        for d in self._documentos:
            tipos[d.type] = tipos.get(d.type, 0) + 1

        return {
            "total_chunks": len(self._documentos),
            "total_documentos": len(fontes),
            "fontes": list(fontes),
            "tipos": tipos
        }

    def limpar_base(self) -> bool:
        """
        Remove todos os documentos da base.

        Returns:
            True se sucesso
        """
        try:
            self._documentos = []
            self._salvar_db()
            return True
        except Exception:
            return False

    def remover_documento(self, fonte: str) -> bool:
        """
        Remove um documento especifico da base.

        Args:
            fonte: Nome/URL da fonte a remover

        Returns:
            True se sucesso
        """
        try:
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
