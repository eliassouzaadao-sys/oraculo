"""
Oraculo Backend API
FastAPI server para o sistema RAG.
"""
import os
import sys
import json
import tempfile
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Adiciona o diretorio pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from core.database import get_knowledge_base
from core.rag import get_oracle_rag
from core.users_db import get_db
from core.auth import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    authenticate_user, register_user, create_access_token,
    get_current_user, get_current_user_optional
)
from loaders.documents import carrega_documento, LOADERS_DOCUMENTOS
from loaders.web import carrega_url, detecta_tipo_url
from loaders.images import carrega_imagem, verificar_tesseract, eh_imagem


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Oraculo Backend iniciado!")
    yield
    # Shutdown
    print("Oraculo Backend encerrado!")


app = FastAPI(
    title="Oraculo API",
    description="API do Assistente de Conhecimento",
    version="2.0.0",
    lifespan=lifespan
)

# CORS para o frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class ChatRequest(BaseModel):
    message: str


class UrlRequest(BaseModel):
    url: str


class ChatResponse(BaseModel):
    response: str


class StatsResponse(BaseModel):
    total_documentos: int
    total_chunks: int
    fontes: list[str]


class MessageResponse(BaseModel):
    success: bool
    message: str


class DocumentInfo(BaseModel):
    source: str
    type: str
    chunks: int


# Endpoints
@app.get("/")
async def root():
    return {"status": "ok", "service": "Oraculo API"}


@app.get("/health")
async def health():
    configured = Config.is_configured()
    return {
        "status": "healthy" if configured else "not_configured",
        "api_configured": configured
    }


# =====================
# AUTH ENDPOINTS
# =====================

@app.post("/auth/register", response_model=TokenResponse)
async def auth_register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registra um novo usuario."""
    user = register_user(db, user_data)
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@app.post("/auth/login", response_model=TokenResponse)
async def auth_login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Autentica usuario e retorna token."""
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Email ou senha incorretos"
        )
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@app.get("/auth/me", response_model=UserResponse)
async def auth_me(current_user = Depends(get_current_user)):
    """Retorna dados do usuario autenticado."""
    return UserResponse.model_validate(current_user)


# =====================
# KNOWLEDGE BASE ENDPOINTS
# =====================

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Retorna estatisticas da base de conhecimento."""
    kb = get_knowledge_base()
    stats = kb.get_estatisticas()
    return StatsResponse(
        total_documentos=stats["total_documentos"],
        total_chunks=stats["total_chunks"],
        fontes=stats["fontes"]
    )


@app.post("/chat")
async def chat(request: ChatRequest):
    """Envia mensagem e recebe resposta com streaming."""
    if not Config.is_configured():
        raise HTTPException(status_code=500, detail="API Key nao configurada")

    kb = get_knowledge_base()
    stats = kb.get_estatisticas()

    if stats["total_documentos"] == 0:
        raise HTTPException(status_code=400, detail="Adicione documentos primeiro")

    oracle = get_oracle_rag()

    async def generate():
        try:
            # Primeiro envia as fontes
            sources = []
            first_token = True

            for token in oracle.responder(request.message):
                # Envia as fontes junto com o primeiro token
                if first_token:
                    sources = oracle.last_sources
                    if sources:
                        sources_json = json.dumps(sources, ensure_ascii=False)
                        yield f"data: [SOURCES]{sources_json}\n\n"
                    first_token = False

                yield f"data: {token}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: Erro: {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/upload", response_model=MessageResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload de arquivo para a base de conhecimento."""
    if not Config.is_configured():
        raise HTTPException(status_code=500, detail="API Key nao configurada")

    # Obtem extensao
    nome = file.filename
    extensao = os.path.splitext(nome)[1].lower()

    # Verifica se e suportado
    extensoes_validas = list(LOADERS_DOCUMENTOS.keys()) + ['.png', '.jpg', '.jpeg']
    if extensao not in extensoes_validas:
        raise HTTPException(status_code=400, detail=f"Formato nao suportado: {extensao}")

    # Salva temporariamente
    with tempfile.NamedTemporaryFile(suffix=extensao, delete=False) as temp:
        content = await file.read()
        temp.write(content)
        caminho_temp = temp.name

    try:
        # Processa
        if eh_imagem(caminho_temp):
            if not verificar_tesseract():
                raise HTTPException(status_code=500, detail="Tesseract nao instalado")
            texto = carrega_imagem(caminho_temp)
            tipo = 'imagem'
        else:
            texto = carrega_documento(caminho_temp, extensao)
            tipo = extensao.replace('.', '')

        if not texto:
            raise HTTPException(status_code=400, detail="Nao foi possivel extrair texto")

        # Adiciona a base
        kb = get_knowledge_base()
        num_chunks = kb.adicionar_documento(texto, nome, tipo)

        if num_chunks > 0:
            return MessageResponse(success=True, message=f"Documento adicionado ({num_chunks} trechos)")
        else:
            raise HTTPException(status_code=400, detail="Erro ao adicionar documento")

    finally:
        try:
            os.unlink(caminho_temp)
        except:
            pass


@app.post("/add-url", response_model=MessageResponse)
async def add_url(request: UrlRequest):
    """Adiciona conteudo de uma URL a base."""
    if not Config.is_configured():
        raise HTTPException(status_code=500, detail="API Key nao configurada")

    url = request.url.strip()

    # Adiciona https:// se nao tiver protocolo
    if url and not url.lower().startswith(('http://', 'https://')):
        url = 'https://' + url

    tipo = detecta_tipo_url(url)

    if tipo is None:
        raise HTTPException(status_code=400, detail="URL invalida")

    try:
        print(f"[DEBUG] Carregando URL: {url} (tipo: {tipo})")
        texto, tipo = carrega_url(url)

        if not texto:
            raise HTTPException(status_code=400, detail="Nao foi possivel carregar conteudo")

        print(f"[DEBUG] Conteudo carregado: {len(texto)} caracteres")
        kb = get_knowledge_base()
        num_chunks = kb.adicionar_documento(texto, url, tipo)

        if num_chunks > 0:
            return MessageResponse(success=True, message=f"Conteudo adicionado ({num_chunks} trechos)")
        else:
            raise HTTPException(status_code=400, detail="Erro ao adicionar")

    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Erro: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/documents")
async def list_documents():
    """Lista todos os documentos na base de conhecimento."""
    kb = get_knowledge_base()
    stats = kb.get_estatisticas()

    # Agrupa chunks por fonte
    documents = []
    source_counts = {}

    for doc in kb._documentos:
        source = doc.source if hasattr(doc, 'source') else "Desconhecido"
        doc_type = doc.type if hasattr(doc, 'type') else "unknown"

        if source not in source_counts:
            source_counts[source] = {"type": doc_type, "chunks": 0}
        source_counts[source]["chunks"] += 1

    for source, info in source_counts.items():
        documents.append({
            "source": source,
            "type": info["type"],
            "chunks": info["chunks"]
        })

    return {"documents": documents, "total": len(documents)}


@app.delete("/documents/{source:path}")
async def delete_document(source: str):
    """Remove um documento especifico da base."""
    kb = get_knowledge_base()

    # Remove todos os chunks deste documento
    initial_count = len(kb._documentos)
    kb._documentos = [doc for doc in kb._documentos if doc.source != source]
    removed = initial_count - len(kb._documentos)

    if removed > 0:
        kb._salvar_db()
        return MessageResponse(success=True, message=f"Documento removido ({removed} trechos)")
    else:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")


@app.post("/clear", response_model=MessageResponse)
async def clear_database():
    """Limpa toda a base de conhecimento."""
    kb = get_knowledge_base()
    oracle = get_oracle_rag()

    kb.limpar_base()
    oracle.limpar_memoria()

    return MessageResponse(success=True, message="Base limpa")


@app.post("/clear-chat", response_model=MessageResponse)
async def clear_chat():
    """Limpa apenas o historico de conversa."""
    oracle = get_oracle_rag()
    oracle.limpar_memoria()
    return MessageResponse(success=True, message="Conversa limpa")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
