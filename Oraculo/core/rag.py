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


SYSTEM_PROMPT = """Voce e o Oraculo, um assistente especializado em responder perguntas
baseadas exclusivamente na base de conhecimento fornecida.

## INSTRUCOES

1. **Use APENAS informacoes do contexto** - Nunca invente dados ou informacoes
2. **Cite as fontes** - Referencie [1], [2], etc. ao usar informacoes de cada fonte
3. **Admita limitacoes** - Se nao houver informacao suficiente, diga claramente
4. **Seja estruturado** - Use listas, topicos e markdown quando apropriado

## PROCESSO DE RACIOCINIO

Antes de responder, analise mentalmente:
- Quais documentos sao relevantes para esta pergunta?
- A informacao esta explicita ou preciso inferir?
- Consigo responder completamente ou apenas parcialmente?

## FORMATO DA RESPOSTA

- Seja claro, direto e objetivo
- Use markdown para formatacao (negrito, listas, etc.)
- Para respostas longas, organize em secoes com titulos
- Sempre que houver $ na saida, substitua por S
- Ao final, mencione as fontes usadas quando relevante

## CONTEXTO DISPONIVEL (ordenado por relevancia)

{context}
"""

USER_TEMPLATE = """Pergunta: {input}

Resposta:"""


class OracleRAG:
    """Sistema de perguntas e respostas com RAG."""

    def __init__(self, sector_id: str = None):
        self._llm = None
        self._memory = ConversationBufferMemory(return_messages=True)
        self._kb = get_knowledge_base()
        self._last_sources: List[Dict[str, Any]] = []
        self._sector_id = sector_id  # Setor ativo para filtrar buscas

    def set_sector(self, sector_id: str):
        """Define o setor ativo. Limpa memoria ao trocar."""
        if self._sector_id != sector_id:
            self._sector_id = sector_id
            self.limpar_memoria()

    @property
    def sector_id(self) -> str:
        """Retorna o setor ativo."""
        return self._sector_id

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
        Inclui indicador de relevancia para ajudar o modelo a priorizar.

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
            score = doc.get("score", 0)

            # Indica relevancia para o modelo priorizar
            if score > 0.8:
                relevancia = "ALTA"
            elif score > 0.6:
                relevancia = "MEDIA"
            else:
                relevancia = "BAIXA"

            partes.append(
                f"[{i}] Fonte: {fonte} | Relevancia: {relevancia}\n{conteudo}"
            )

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

    def responder(self, pergunta: str, sector_id: str = None) -> Generator[str, None, None]:
        """
        Responde uma pergunta usando RAG com streaming.

        Args:
            pergunta: Pergunta do usuario
            sector_id: ID do setor para filtrar (usa o setor da instancia se None)

        Yields:
            Tokens da resposta em streaming
        """
        # Usa setor passado ou o setor da instancia
        sector = sector_id or self._sector_id

        # Busca documentos relevantes (filtrado por setor)
        documentos = self._kb.buscar(pergunta, sector_id=sector)

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

    def responder_com_fontes(self, pergunta: str, sector_id: str = None) -> Tuple[Generator[str, None, None], List[Dict[str, Any]]]:
        """
        Responde uma pergunta e retorna as fontes usadas.

        Args:
            pergunta: Pergunta do usuario
            sector_id: ID do setor para filtrar

        Returns:
            Tuple com (gerador de tokens, lista de fontes)
        """
        # Usa setor passado ou o setor da instancia
        sector = sector_id or self._sector_id

        # Busca documentos relevantes primeiro (filtrado por setor)
        documentos = self._kb.buscar(pergunta, sector_id=sector)

        # Extrai fontes para referencia
        self._last_sources = self._extract_sources(documentos)

        # Retorna o gerador e as fontes
        return self.responder(pergunta, sector_id=sector), self._last_sources

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

    def has_knowledge(self, sector_id: str = None) -> bool:
        """
        Verifica se ha documentos na base de conhecimento.

        Args:
            sector_id: ID do setor para verificar (usa o setor da instancia se None)

        Returns:
            True se houver documentos
        """
        sector = sector_id or self._sector_id
        stats = self._kb.get_estatisticas(sector_id=sector)
        return stats.get("total_documentos", 0) > 0


# Dicionario de instancias por setor
_oracle_instances: Dict[str, OracleRAG] = {}


def get_oracle_rag(sector_id: str = None) -> OracleRAG:
    """
    Retorna instancia do Oracle RAG para o setor.

    Args:
        sector_id: ID do setor (None = instancia global)

    Returns:
        Instancia do OracleRAG
    """
    global _oracle_instances

    # Usa "global" como chave para instancia sem setor
    key = str(sector_id) if sector_id else "global"

    if key not in _oracle_instances:
        _oracle_instances[key] = OracleRAG(sector_id=sector_id)

    return _oracle_instances[key]


def reset_oracle_rag(sector_id: str = None):
    """
    Reseta instancia(s) do Oracle RAG.

    Args:
        sector_id: ID do setor para resetar (None = reseta todas)
    """
    global _oracle_instances

    if sector_id is not None:
        key = str(sector_id)
        if key in _oracle_instances:
            del _oracle_instances[key]
    else:
        _oracle_instances = {}
