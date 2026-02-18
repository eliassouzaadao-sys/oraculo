"""
Database de setores com SQLAlchemy.
Gerencia setores da empresa e associacao com usuarios.
"""
from datetime import datetime
from typing import Optional, List
import re

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship, Session

from core.users_db import Base, engine


# Tabela de associacao User-Sector (muitos para muitos)
user_sectors = Table(
    'user_sectors',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('sector_id', Integer, ForeignKey('sectors.id', ondelete='CASCADE'), primary_key=True),
    Column('role', String(20), default='member'),  # 'admin' ou 'member'
    Column('joined_at', DateTime, default=datetime.utcnow)
)


class Sector(Base):
    """Modelo de setor da empresa."""
    __tablename__ = "sectors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#6366f1")  # Cor hex para UI
    icon = Column(String(50), default="folder")   # Nome do icone Lucide
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relacionamentos
    members = relationship(
        "User",
        secondary=user_sectors,
        backref="sectors"
    )


def generate_slug(name: str) -> str:
    """Gera slug URL-friendly a partir do nome."""
    # Remove acentos e caracteres especiais
    slug = name.lower().strip()
    slug = re.sub(r'[àáâãäå]', 'a', slug)
    slug = re.sub(r'[èéêë]', 'e', slug)
    slug = re.sub(r'[ìíîï]', 'i', slug)
    slug = re.sub(r'[òóôõö]', 'o', slug)
    slug = re.sub(r'[ùúûü]', 'u', slug)
    slug = re.sub(r'[ç]', 'c', slug)
    slug = re.sub(r'[ñ]', 'n', slug)
    # Substitui espacos e caracteres nao alfanumericos por hifens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Remove hifens no inicio e fim
    slug = slug.strip('-')
    return slug


# =====================
# CRUD DE SETORES
# =====================

def get_sector_by_id(db: Session, sector_id: int) -> Optional[Sector]:
    """Busca setor por ID."""
    return db.query(Sector).filter(Sector.id == sector_id).first()


def get_sector_by_slug(db: Session, slug: str) -> Optional[Sector]:
    """Busca setor por slug."""
    return db.query(Sector).filter(Sector.slug == slug).first()


def get_sector_by_name(db: Session, name: str) -> Optional[Sector]:
    """Busca setor por nome."""
    return db.query(Sector).filter(Sector.name == name).first()


def get_all_sectors(db: Session, only_active: bool = True) -> List[Sector]:
    """Lista todos os setores."""
    query = db.query(Sector)
    if only_active:
        query = query.filter(Sector.is_active == True)
    return query.order_by(Sector.name).all()


def create_sector(
    db: Session,
    name: str,
    description: Optional[str] = None,
    color: str = "#6366f1",
    icon: str = "folder",
    created_by_id: Optional[int] = None
) -> Sector:
    """Cria um novo setor."""
    slug = generate_slug(name)

    # Garante slug unico
    base_slug = slug
    counter = 1
    while get_sector_by_slug(db, slug):
        slug = f"{base_slug}-{counter}"
        counter += 1

    sector = Sector(
        name=name,
        slug=slug,
        description=description,
        color=color,
        icon=icon,
        created_by_id=created_by_id
    )
    db.add(sector)
    db.commit()
    db.refresh(sector)
    return sector


def update_sector(
    db: Session,
    sector_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[str] = None,
    icon: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Optional[Sector]:
    """Atualiza dados do setor."""
    sector = get_sector_by_id(db, sector_id)
    if not sector:
        return None

    if name is not None:
        sector.name = name
        sector.slug = generate_slug(name)
    if description is not None:
        sector.description = description
    if color is not None:
        sector.color = color
    if icon is not None:
        sector.icon = icon
    if is_active is not None:
        sector.is_active = is_active

    sector.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(sector)
    return sector


def delete_sector(db: Session, sector_id: int) -> bool:
    """Remove um setor (soft delete - desativa)."""
    sector = get_sector_by_id(db, sector_id)
    if sector:
        sector.is_active = False
        sector.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False


def hard_delete_sector(db: Session, sector_id: int) -> bool:
    """Remove permanentemente um setor."""
    sector = get_sector_by_id(db, sector_id)
    if sector:
        db.delete(sector)
        db.commit()
        return True
    return False


# =====================
# MEMBROS DO SETOR
# =====================

def add_user_to_sector(
    db: Session,
    user_id: int,
    sector_id: int,
    role: str = "member"
) -> bool:
    """Adiciona usuario a um setor."""
    from core.users_db import get_user_by_id

    user = get_user_by_id(db, user_id)
    sector = get_sector_by_id(db, sector_id)

    if not user or not sector:
        return False

    # Verifica se ja e membro
    if sector in user.sectors:
        return True

    # Insere na tabela de associacao
    stmt = user_sectors.insert().values(
        user_id=user_id,
        sector_id=sector_id,
        role=role,
        joined_at=datetime.utcnow()
    )
    db.execute(stmt)
    db.commit()
    return True


def remove_user_from_sector(db: Session, user_id: int, sector_id: int) -> bool:
    """Remove usuario de um setor."""
    stmt = user_sectors.delete().where(
        (user_sectors.c.user_id == user_id) &
        (user_sectors.c.sector_id == sector_id)
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount > 0


def get_user_role_in_sector(db: Session, user_id: int, sector_id: int) -> Optional[str]:
    """Retorna o role do usuario no setor."""
    result = db.execute(
        user_sectors.select().where(
            (user_sectors.c.user_id == user_id) &
            (user_sectors.c.sector_id == sector_id)
        )
    ).first()
    return result.role if result else None


def is_sector_admin(db: Session, user_id: int, sector_id: int) -> bool:
    """Verifica se usuario e admin do setor."""
    role = get_user_role_in_sector(db, user_id, sector_id)
    return role == "admin"


def get_sector_members(db: Session, sector_id: int) -> List[dict]:
    """Lista membros de um setor com seus roles."""
    from core.users_db import User

    results = db.execute(
        user_sectors.select().where(user_sectors.c.sector_id == sector_id)
    ).fetchall()

    members = []
    for row in results:
        user = db.query(User).filter(User.id == row.user_id).first()
        if user:
            members.append({
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "role": row.role,
                "joined_at": row.joined_at.isoformat() if row.joined_at else None
            })

    return members


def get_user_sectors(db: Session, user_id: int) -> List[Sector]:
    """Lista setores que o usuario pertence."""
    from core.users_db import get_user_by_id

    user = get_user_by_id(db, user_id)
    if not user:
        return []

    return [s for s in user.sectors if s.is_active]


def get_sector_document_count(db: Session, sector_id: int) -> int:
    """Retorna quantidade de documentos no setor."""
    from core.database import get_knowledge_base

    kb = get_knowledge_base()
    docs = [d for d in kb._documentos if str(d.sector_id) == str(sector_id)]
    sources = set(d.source for d in docs)
    return len(sources)


def get_sector_stats(db: Session, sector_id: int) -> dict:
    """Retorna estatisticas completas do setor."""
    sector = get_sector_by_id(db, sector_id)
    if not sector:
        return {}

    members = get_sector_members(db, sector_id)
    doc_count = get_sector_document_count(db, sector_id)

    return {
        "id": sector.id,
        "name": sector.name,
        "slug": sector.slug,
        "description": sector.description,
        "color": sector.color,
        "icon": sector.icon,
        "member_count": len(members),
        "document_count": doc_count,
        "created_at": sector.created_at.isoformat() if sector.created_at else None,
        "is_active": sector.is_active
    }


# Cria as tabelas
Base.metadata.create_all(bind=engine)
