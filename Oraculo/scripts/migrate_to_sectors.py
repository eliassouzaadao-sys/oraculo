"""
Script de migracao para adicionar suporte a setores.
Executa uma vez para migrar dados existentes.

Uso:
    python scripts/migrate_to_sectors.py
"""
import os
import sys

# Adiciona o diretorio pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime


def migrate():
    """Executa a migracao."""
    print("=" * 50)
    print("Migracao para Sistema de Setores - Oraculo")
    print("=" * 50)

    # Importa apos ajustar o path
    from core.users_db import SessionLocal, Base, engine, User
    from core.sectors_db import Sector, user_sectors, create_sector, add_user_to_sector
    from core.database import get_knowledge_base

    # 1. Cria as novas tabelas
    print("\n[1/4] Criando tabelas de setores...")
    try:
        Base.metadata.create_all(bind=engine)
        print("      Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"      Aviso: {e}")

    db = SessionLocal()

    try:
        # 2. Verifica se ja existe setor "Geral"
        existing = db.query(Sector).filter(Sector.slug == "geral").first()
        if existing:
            print("\n[2/4] Setor 'Geral' ja existe (ID: {})".format(existing.id))
            default_sector = existing
        else:
            print("\n[2/4] Criando setor padrao 'Geral'...")
            default_sector = create_sector(
                db,
                name="Geral",
                description="Setor padrao para documentos existentes",
                color="#6366f1",
                icon="folder"
            )
            print(f"      Setor criado com ID: {default_sector.id}")

        # 3. Migra documentos existentes para setor padrao
        print("\n[3/4] Migrando documentos existentes...")
        kb = get_knowledge_base()
        docs_migrados = 0

        for doc in kb._documentos:
            sector_id = getattr(doc, 'sector_id', None)
            if not sector_id or sector_id == "default" or sector_id == "":
                doc.sector_id = str(default_sector.id)
                docs_migrados += 1

        if docs_migrados > 0:
            kb._salvar_db()
            print(f"      {docs_migrados} documento(s) migrado(s)")
        else:
            print("      Nenhum documento para migrar")

        # 4. Adiciona todos os usuarios existentes ao setor padrao
        print("\n[4/4] Adicionando usuarios ao setor padrao...")
        users = db.query(User).all()
        users_adicionados = 0

        for user in users:
            # Verifica se ja e membro
            is_member = db.execute(
                user_sectors.select().where(
                    (user_sectors.c.user_id == user.id) &
                    (user_sectors.c.sector_id == default_sector.id)
                )
            ).first()

            if not is_member:
                # Adiciona como admin se for o primeiro usuario, senao como membro
                role = "admin" if user.id == 1 else "member"
                add_user_to_sector(db, user.id, default_sector.id, role=role)
                users_adicionados += 1

        if users_adicionados > 0:
            print(f"      {users_adicionados} usuario(s) adicionado(s)")
        else:
            print("      Todos os usuarios ja estao no setor")

        print("\n" + "=" * 50)
        print("Migracao concluida com sucesso!")
        print("=" * 50)
        print(f"\nResumo:")
        print(f"  - Setor padrao: {default_sector.name} (ID: {default_sector.id})")
        print(f"  - Documentos migrados: {docs_migrados}")
        print(f"  - Usuarios adicionados: {users_adicionados}")
        print(f"\nVoce pode agora criar novos setores na interface web.")

    except Exception as e:
        db.rollback()
        print(f"\nErro na migracao: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Confirma execucao
    print("\nEste script ira:")
    print("  1. Criar as tabelas de setores no banco de dados")
    print("  2. Criar um setor padrao chamado 'Geral'")
    print("  3. Migrar documentos existentes para o setor 'Geral'")
    print("  4. Adicionar usuarios existentes ao setor 'Geral'")
    print()

    resposta = input("Deseja continuar? (s/n): ").strip().lower()
    if resposta in ['s', 'sim', 'y', 'yes']:
        migrate()
    else:
        print("Migracao cancelada.")
