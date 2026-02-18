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

from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
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
    get_current_user, get_current_user_optional,
    SectorCreate, SectorUpdate, SectorResponse, SectorMemberAdd, SectorMemberResponse
)
from core.sectors_db import (
    get_all_sectors, get_sector_by_id, create_sector, update_sector,
    delete_sector, hard_delete_sector, add_user_to_sector, remove_user_from_sector,
    get_sector_members, get_user_sectors, get_sector_stats, is_sector_admin
)
from core.users_db import update_user
from loaders.documents import carrega_documento, LOADERS_DOCUMENTOS
from loaders.web import carrega_url, detecta_tipo_url
from loaders.images import carrega_imagem, verificar_tesseract, eh_imagem
from loaders.audio import transcreve_audio, eh_audio, EXTENSOES_AUDIO


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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://oraculo.fyness.com.br"],
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
# SECTOR ENDPOINTS
# =====================

@app.get("/sectors", response_model=List[SectorResponse])
async def list_sectors(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos os setores disponiveis."""
    sectors = get_all_sectors(db)
    result = []
    for sector in sectors:
        stats = get_sector_stats(db, sector.id)
        result.append(SectorResponse(
            id=sector.id,
            name=sector.name,
            slug=sector.slug,
            description=sector.description,
            color=sector.color,
            icon=sector.icon,
            created_at=sector.created_at,
            is_active=sector.is_active,
            member_count=stats.get("member_count", 0),
            document_count=stats.get("document_count", 0)
        ))
    return result


@app.post("/sectors", response_model=SectorResponse)
async def create_new_sector(
    sector_data: SectorCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria um novo setor."""
    sector = create_sector(
        db,
        name=sector_data.name,
        description=sector_data.description,
        color=sector_data.color,
        icon=sector_data.icon,
        created_by_id=current_user.id
    )
    # Adiciona criador como admin do setor
    add_user_to_sector(db, current_user.id, sector.id, role="admin")

    stats = get_sector_stats(db, sector.id)
    return SectorResponse(
        id=sector.id,
        name=sector.name,
        slug=sector.slug,
        description=sector.description,
        color=sector.color,
        icon=sector.icon,
        created_at=sector.created_at,
        is_active=sector.is_active,
        member_count=stats.get("member_count", 0),
        document_count=stats.get("document_count", 0)
    )


@app.get("/sectors/{sector_id}", response_model=SectorResponse)
async def get_sector(
    sector_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna detalhes de um setor."""
    sector = get_sector_by_id(db, sector_id)
    if not sector:
        raise HTTPException(status_code=404, detail="Setor nao encontrado")

    stats = get_sector_stats(db, sector.id)
    return SectorResponse(
        id=sector.id,
        name=sector.name,
        slug=sector.slug,
        description=sector.description,
        color=sector.color,
        icon=sector.icon,
        created_at=sector.created_at,
        is_active=sector.is_active,
        member_count=stats.get("member_count", 0),
        document_count=stats.get("document_count", 0)
    )


@app.put("/sectors/{sector_id}", response_model=SectorResponse)
async def update_sector_endpoint(
    sector_id: int,
    sector_data: SectorUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza um setor."""
    sector = update_sector(
        db, sector_id,
        name=sector_data.name,
        description=sector_data.description,
        color=sector_data.color,
        icon=sector_data.icon,
        is_active=sector_data.is_active
    )
    if not sector:
        raise HTTPException(status_code=404, detail="Setor nao encontrado")

    stats = get_sector_stats(db, sector.id)
    return SectorResponse(
        id=sector.id,
        name=sector.name,
        slug=sector.slug,
        description=sector.description,
        color=sector.color,
        icon=sector.icon,
        created_at=sector.created_at,
        is_active=sector.is_active,
        member_count=stats.get("member_count", 0),
        document_count=stats.get("document_count", 0)
    )


@app.delete("/sectors/{sector_id}")
async def delete_sector_endpoint(
    sector_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove um setor."""
    # Remove documentos do setor
    kb = get_knowledge_base()
    kb.limpar_base(sector_id=str(sector_id))

    # Remove setor permanentemente
    if not hard_delete_sector(db, sector_id):
        raise HTTPException(status_code=404, detail="Setor nao encontrado")

    return MessageResponse(success=True, message="Setor removido")


@app.get("/sectors/{sector_id}/members", response_model=List[SectorMemberResponse])
async def list_sector_members(
    sector_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista membros de um setor."""
    sector = get_sector_by_id(db, sector_id)
    if not sector:
        raise HTTPException(status_code=404, detail="Setor nao encontrado")

    members = get_sector_members(db, sector_id)
    return [SectorMemberResponse(**m) for m in members]


@app.post("/sectors/{sector_id}/members")
async def add_member_to_sector(
    sector_id: int,
    member_data: SectorMemberAdd,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adiciona membro ao setor."""
    if not add_user_to_sector(db, member_data.user_id, sector_id, member_data.role):
        raise HTTPException(status_code=400, detail="Erro ao adicionar membro")

    return MessageResponse(success=True, message="Membro adicionado")


@app.delete("/sectors/{sector_id}/members/{user_id}")
async def remove_member_from_sector(
    sector_id: int,
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove membro do setor."""
    if not remove_user_from_sector(db, user_id, sector_id):
        raise HTTPException(status_code=400, detail="Erro ao remover membro")

    return MessageResponse(success=True, message="Membro removido")


@app.post("/sectors/{sector_id}/join")
async def join_sector(
    sector_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Entra em um setor (qualquer usuario pode entrar)."""
    sector = get_sector_by_id(db, sector_id)
    if not sector:
        raise HTTPException(status_code=404, detail="Setor nao encontrado")

    if not sector.is_active:
        raise HTTPException(status_code=400, detail="Setor inativo")

    if not add_user_to_sector(db, current_user.id, sector_id, role="member"):
        raise HTTPException(status_code=400, detail="Erro ao entrar no setor")

    return MessageResponse(success=True, message="Voce entrou no setor")


@app.put("/users/me/active-sector")
async def set_active_sector(
    sector_id: int = Query(..., description="ID do setor"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Define o setor ativo do usuario."""
    sector = get_sector_by_id(db, sector_id)
    if not sector:
        raise HTTPException(status_code=404, detail="Setor nao encontrado")

    update_user(db, current_user.id, active_sector_id=sector_id)
    return MessageResponse(success=True, message="Setor ativo atualizado")


# =====================
# KNOWLEDGE BASE ENDPOINTS
# =====================

@app.get("/stats", response_model=StatsResponse)
async def get_stats(
    sector_id: int = Query(None, description="ID do setor (opcional)")
):
    """Retorna estatisticas da base de conhecimento do setor."""
    kb = get_knowledge_base()
    stats = kb.get_estatisticas(sector_id=str(sector_id) if sector_id else None)
    return StatsResponse(
        total_documentos=stats["total_documentos"],
        total_chunks=stats["total_chunks"],
        fontes=stats["fontes"]
    )


@app.post("/chat")
async def chat(
    request: ChatRequest,
    sector_id: int = Query(None, description="ID do setor")
):
    """Envia mensagem e recebe resposta com streaming."""
    if not Config.is_configured():
        raise HTTPException(status_code=500, detail="API Key nao configurada")

    kb = get_knowledge_base()
    stats = kb.get_estatisticas(sector_id=str(sector_id) if sector_id else None)

    if stats["total_documentos"] == 0:
        raise HTTPException(status_code=400, detail="Adicione documentos primeiro")

    oracle = get_oracle_rag(sector_id=str(sector_id) if sector_id else None)

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

                # Codifica newlines para preservar quebras de linha no SSE
                # O frontend decodifica de volta
                encoded_token = token.replace('\n', '\\n')
                yield f"data: {encoded_token}\n\n"

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
async def upload_file(
    file: UploadFile = File(...),
    sector_id: int = Query(None, description="ID do setor")
):
    """Upload de arquivo para a base de conhecimento do setor."""
    if not Config.is_configured():
        raise HTTPException(status_code=500, detail="API Key nao configurada")

    # Obtem extensao
    nome = file.filename
    extensao = os.path.splitext(nome)[1].lower()

    # Verifica se e suportado (documentos, imagens ou audio)
    extensoes_validas = list(LOADERS_DOCUMENTOS.keys()) + ['.png', '.jpg', '.jpeg'] + EXTENSOES_AUDIO
    if extensao not in extensoes_validas:
        raise HTTPException(status_code=400, detail=f"Formato nao suportado: {extensao}")

    # Salva temporariamente
    with tempfile.NamedTemporaryFile(suffix=extensao, delete=False) as temp:
        content = await file.read()
        temp.write(content)
        caminho_temp = temp.name

    try:
        # Processa baseado no tipo
        if eh_audio(caminho_temp):
            # Audio: transcreve com Whisper
            print(f"[DEBUG] Processando audio: {nome}")
            texto = transcreve_audio(caminho_temp)
            tipo = 'audio'
        elif eh_imagem(caminho_temp):
            # Imagem: OCR com Tesseract
            if not verificar_tesseract():
                raise HTTPException(status_code=500, detail="Tesseract nao instalado")
            texto = carrega_imagem(caminho_temp)
            tipo = 'imagem'
        else:
            # Documento: loader especifico
            texto = carrega_documento(caminho_temp, extensao)
            tipo = extensao.replace('.', '')

        if not texto:
            raise HTTPException(status_code=400, detail="Nao foi possivel extrair texto")

        # Adiciona a base
        kb = get_knowledge_base()
        num_chunks = kb.adicionar_documento(texto, nome, tipo, sector_id=str(sector_id) if sector_id else "default")

        if num_chunks > 0:
            return MessageResponse(success=True, message=f"Documento adicionado ({num_chunks} trechos)")
        else:
            raise HTTPException(status_code=400, detail="Erro ao adicionar documento")

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erro ao processar arquivo: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        try:
            os.unlink(caminho_temp)
        except:
            pass


@app.post("/add-url", response_model=MessageResponse)
async def add_url(
    request: UrlRequest,
    sector_id: int = Query(None, description="ID do setor")
):
    """Adiciona conteudo de uma URL a base do setor."""
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
        num_chunks = kb.adicionar_documento(texto, url, tipo, sector_id=str(sector_id) if sector_id else "default")

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
async def list_documents(
    sector_id: int = Query(None, description="ID do setor")
):
    """Lista todos os documentos na base de conhecimento do setor."""
    kb = get_knowledge_base()

    # Filtra por setor
    documentos = kb._documentos
    if sector_id is not None:
        documentos = [d for d in documentos if str(getattr(d, 'sector_id', 'default')) == str(sector_id)]

    # Agrupa chunks por fonte
    documents = []
    source_counts = {}

    for doc in documentos:
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
async def delete_document(
    source: str,
    sector_id: int = Query(None, description="ID do setor")
):
    """Remove um documento especifico da base do setor."""
    from urllib.parse import unquote
    import re

    # Decodifica multiplas vezes (nginx pode decodificar parcialmente)
    prev = None
    while prev != source:
        prev = source
        source = unquote(source)

    # Normaliza URL (nginx pode remover uma barra de https://)
    source = re.sub(r"^(https?:)/([^/])", r"\1//\2", source)

    kb = get_knowledge_base()

    # Remove todos os chunks deste documento do setor
    initial_count = len(kb._documentos)
    if sector_id is not None:
        kb._documentos = [
            doc for doc in kb._documentos
            if not (doc.source == source and str(getattr(doc, 'sector_id', 'default')) == str(sector_id))
        ]
    else:
        kb._documentos = [doc for doc in kb._documentos if doc.source != source]
    removed = initial_count - len(kb._documentos)

    if removed > 0:
        kb._salvar_db()
        return MessageResponse(success=True, message=f"Documento removido ({removed} trechos)")
    else:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")


@app.post("/clear", response_model=MessageResponse)
async def clear_database(
    sector_id: int = Query(None, description="ID do setor")
):
    """Limpa a base de conhecimento do setor."""
    kb = get_knowledge_base()
    oracle = get_oracle_rag(sector_id=str(sector_id) if sector_id else None)

    kb.limpar_base(sector_id=str(sector_id) if sector_id else None)
    oracle.limpar_memoria()

    return MessageResponse(success=True, message="Base do setor limpa" if sector_id else "Base limpa")


@app.post("/clear-chat", response_model=MessageResponse)
async def clear_chat(
    sector_id: int = Query(None, description="ID do setor")
):
    """Limpa apenas o historico de conversa do setor."""
    oracle = get_oracle_rag(sector_id=str(sector_id) if sector_id else None)
    oracle.limpar_memoria()
    return MessageResponse(success=True, message="Conversa limpa")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
