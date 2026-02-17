"""
Sistema RAG (Retrieval-Augmented Generation).
Responsavel por responder perguntas usando a base de conhecimento.
"""
import os
from typing import Generator, List, Tuple, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from core.database import get_knowledge_base


SYSTEM_PROMPT = """Voce e o Oraculo, um assistente amigavel e prestativo.

Voce tem acesso a uma base de conhecimento com informacoes relevantes.
Use APENAS as informacoes fornecidas no contexto abaixo para responder.

Se a pergunta nao puder ser respondida com as informacoes do contexto,
diga educadamente que nao tem essa informacao na base de conhecimento.

Seja claro, direto e objetivo nas respostas.
Sempre que houver $ na sua saida, substitua por S.

CONTEXTO:
{context}
"""

USER_TEMPLATE = """Pergunta: {input}

Resposta:"""


class OracleRAG:
    """Sistema de perguntas e respostas com RAG."""

    def __init__(self):
        self._llm = None
        self._memory = ConversationBufferMemory(return_messages=True)
        self._kb = get_knowledge_base()
        self._last_sources: List[Dict[str, Any]] = []

    @property
    def llm(self):
        """Lazy loading do modelo LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=Config.DEFAULT_MODEL,
                api_key=Config.OPENAI_API_KEY,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                streaming=True
            )
        return self._llm

    @property
    def memory(self):
        """Retorna a memoria de conversa."""
        return self._memory

    @property
    def last_sources(self) -> List[Dict[str, Any]]:
        """Retorna as fontes usadas na ultima resposta."""
        return self._last_sources

    def _build_context(self, documentos: List[dict]) -> str:
        """
        Constroi o contexto a partir dos documentos recuperados.

        Args:
            documentos: Lista de documentos relevantes

        Returns:
            Texto do contexto formatado
        """
        if not documentos:
            return "Nenhuma informacao encontrada na base de conhecimento."

        partes = []
        for i, doc in enumerate(documentos, 1):
            fonte = doc.get("source", "Desconhecido")
            conteudo = doc.get("content", "")
            partes.append(f"[{i}] Fonte: {fonte}\n{conteudo}")

        return "\n\n---\n\n".join(partes)

    def _extract_sources(self, documentos: List[dict]) -> List[Dict[str, Any]]:
        """
        Extrai informacoes das fontes para exibicao.

        Args:
            documentos: Lista de documentos relevantes

        Returns:
            Lista de fontes formatadas
        """
        sources = []
        seen_sources = set()

        for doc in documentos:
            source_name = doc.get("source", "Desconhecido")

            # Evita duplicatas
            if source_name in seen_sources:
                continue
            seen_sources.add(source_name)

            # Extrai trecho para preview
            content = doc.get("content", "")
            excerpt = content[:150] + "..." if len(content) > 150 else content

            # Pega a similaridade se disponivel
            score = doc.get("similarity", None)

            sources.append({
                "name": source_name,
                "score": score,
                "excerpt": excerpt
            })

        return sources

    def responder(self, pergunta: str) -> Generator[str, None, None]:
        """
        Responde uma pergunta usando RAG com streaming.

        Args:
            pergunta: Pergunta do usuario

        Yields:
            Tokens da resposta em streaming
        """
        # Busca documentos relevantes
        documentos = self._kb.buscar(pergunta)

        # Extrai fontes para referencia
        self._last_sources = self._extract_sources(documentos)

        # Constroi contexto
        contexto = self._build_context(documentos)

        # Cria o prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("placeholder", "{chat_history}"),
            ("human", USER_TEMPLATE)
        ])

        # Cria a chain
        chain = prompt | self.llm

        # Executa com streaming
        resposta_completa = ""
        for chunk in chain.stream({
            "context": contexto,
            "input": pergunta,
            "chat_history": self._memory.buffer_as_messages
        }):
            token = chunk.content
            resposta_completa += token
            yield token

        # Salva na memoria
        self._memory.chat_memory.add_user_message(pergunta)
        self._memory.chat_memory.add_ai_message(resposta_completa)

    def responder_com_fontes(self, pergunta: str) -> Tuple[Generator[str, None, None], List[Dict[str, Any]]]:
        """
        Responde uma pergunta e retorna as fontes usadas.

        Args:
            pergunta: Pergunta do usuario

        Returns:
            Tuple com (gerador de tokens, lista de fontes)
        """
        # Busca documentos relevantes primeiro
        documentos = self._kb.buscar(pergunta)

        # Extrai fontes para referencia
        self._last_sources = self._extract_sources(documentos)

        # Retorna o gerador e as fontes
        return self.responder(pergunta), self._last_sources

    def responder_sincrono(self, pergunta: str) -> str:
        """
        Responde uma pergunta de forma sincrona (sem streaming).

        Args:
            pergunta: Pergunta do usuario

        Returns:
            Resposta completa
        """
        resposta = ""
        for token in self.responder(pergunta):
            resposta += token
        return resposta

    def limpar_memoria(self):
        """Limpa o historico de conversa."""
        self._memory.clear()
        self._last_sources = []

    def get_historico(self) -> list:
        """
        Retorna o historico de mensagens.

        Returns:
            Lista de mensagens
        """
        return self._memory.buffer_as_messages

    def has_knowledge(self) -> bool:
        """
        Verifica se ha documentos na base de conhecimento.

        Returns:
            True se houver documentos
        """
        stats = self._kb.get_estatisticas()
        return stats.get("total_documentos", 0) > 0


# Instancia global (singleton)
_oracle_rag = None


def get_oracle_rag() -> OracleRAG:
    """Retorna instancia singleton do Oracle RAG."""
    global _oracle_rag
    if _oracle_rag is None:
        _oracle_rag = OracleRAG()
    return _oracle_rag


def reset_oracle_rag():
    """Reseta a instancia do Oracle RAG (para testes ou reconfiguracao)."""
    global _oracle_rag
    _oracle_rag = None
