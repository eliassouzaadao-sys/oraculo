"""
Database de usuarios com SQLAlchemy.
"""
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configuracao do banco de dados
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(DATABASE_DIR, 'users.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """Modelo de usuario."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    active_sector_id = Column(Integer, nullable=True)  # Setor ativo do usuario


# Cria as tabelas
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency para obter sessao do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca usuario por email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Busca usuario por ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, username: str, hashed_password: str) -> User:
    """Cria um novo usuario."""
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """Atualiza dados do usuario."""
    user = get_user_by_id(db, user_id)
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """Remove um usuario."""
    user = get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
