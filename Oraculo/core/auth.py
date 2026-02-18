"""
Sistema de autenticacao com JWT.
"""
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from core.users_db import get_db, get_user_by_email, get_user_by_id, create_user, User

# Configuracoes JWT
JWT_SECRET = os.getenv("JWT_SECRET", "oraculo-secret-key-change-in-production-2024")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# Security bearer
security = HTTPBearer(auto_error=False)


# Pydantic Models
class UserCreate(BaseModel):
    """Schema para criacao de usuario."""
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    """Schema para login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema de resposta do usuario."""
    id: int
    email: str
    username: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema de resposta do token."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Dados extraidos do token."""
    user_id: Optional[int] = None
    email: Optional[str] = None


# =====================
# SCHEMAS DE SETOR
# =====================

class SectorCreate(BaseModel):
    """Schema para criacao de setor."""
    name: str
    description: Optional[str] = None
    color: str = "#6366f1"
    icon: str = "folder"


class SectorUpdate(BaseModel):
    """Schema para atualizacao de setor."""
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class SectorResponse(BaseModel):
    """Schema de resposta do setor."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    color: str
    icon: str
    created_at: datetime
    is_active: bool
    member_count: int = 0
    document_count: int = 0

    class Config:
        from_attributes = True


class SectorMemberAdd(BaseModel):
    """Schema para adicionar membro ao setor."""
    user_id: int
    role: str = "member"


class SectorMemberResponse(BaseModel):
    """Schema de resposta de membro do setor."""
    user_id: int
    email: str
    username: str
    role: str
    joined_at: Optional[datetime] = None


# Funcoes de senha
def hash_password(password: str) -> str:
    """Gera hash da senha."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha confere com o hash."""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# Funcoes de JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um token JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=JWT_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """Decodifica um token JWT."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id is None:
            return None
        return TokenData(user_id=int(user_id), email=email)
    except JWTError:
        return None


# Funcoes de autenticacao
def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Autentica usuario por email e senha."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def register_user(db: Session, user_data: UserCreate) -> User:
    """Registra um novo usuario."""
    # Verifica se email ja existe
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ja cadastrado"
        )

    # Cria usuario
    hashed_password = hash_password(user_data.password)
    return create_user(db, user_data.email, user_data.username, hashed_password)


# Dependency para obter usuario atual
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency que retorna o usuario autenticado."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token_data = decode_token(credentials.credentials)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception

    user = get_user_by_id(db, token_data.user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inativo"
        )

    return user


# Dependency opcional (nao exige auth, mas retorna user se autenticado)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency que retorna o usuario se autenticado, ou None."""
    if not credentials:
        return None

    token_data = decode_token(credentials.credentials)
    if token_data is None or token_data.user_id is None:
        return None

    user = get_user_by_id(db, token_data.user_id)
    if user is None or not user.is_active:
        return None

    return user
