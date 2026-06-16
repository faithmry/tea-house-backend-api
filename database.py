"""Database configuration — equivalent of plugins/Databases.kt.

Mirrors the Kotlin behavior:
  * DATABASE_URL drives the connection; default is an in-memory database that
    survives for the lifetime of the process (H2 `DB_CLOSE_DELAY=-1` -> SQLite
    in-memory backed by a shared StaticPool connection).
  * Tables are created on startup.
  * A test member ("Andi") is seeded if the table is empty.
"""

import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base, Member, MenuItem


def _build_engine():
    database_url = os.getenv("DATABASE_URL")

    if database_url and database_url.startswith(("postgresql", "postgres")):
        # Normalize the common "postgres://" form to SQLAlchemy's driver URL.
        url = database_url.replace("postgres://", "postgresql://", 1)
        user = os.getenv("DATABASE_USER")
        password = os.getenv("DATABASE_PASSWORD")
        if user and "@" not in url.split("//", 1)[1]:
            cred = user if not password else f"{user}:{password}"
            url = url.replace("postgresql://", f"postgresql://{cred}@", 1)
        return create_engine(url, pool_pre_ping=True)

    # Default: in-memory SQLite shared across all sessions for the whole
    # process lifetime (the equivalent of H2 mem + DB_CLOSE_DELAY=-1).
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


engine = _build_engine()
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False
)


def configure_databases() -> None:
    """Create tables and seed a test member if the table is empty."""
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        member_exists = session.scalar(select(Member).limit(1)) is not None
        if not member_exists:
            # BUGFIX: the Kotlin seed used id="1" while /login issues a token
            # for memberId="001", so /member/001 always 404'd. Seed "001" so
            # the mock login resolves to a real member end-to-end.
            session.add(
                Member(
                    id="001",
                    name="Andi",
                    email="andi@example.com",
                    phone="08123456789",
                    points=1000,
                    tier="Gold",
                )
            )
            session.commit()

        menu_exists = session.scalar(select(MenuItem).limit(1)) is not None
        if not menu_exists:
            session.add_all([
                MenuItem(name="Green Tea Latte", description="Premium matcha dengan susu segar", price=28000, category="Minuman"),
                MenuItem(name="Oolong Milk Tea", description="Oolong klasik dengan susu segar", price=25000, category="Minuman"),
                MenuItem(name="Jasmine Cold Brew", description="Cold brew teh melati yang menyegarkan", price=22000, category="Minuman"),
                MenuItem(name="Earl Grey Cake", description="Kue sponge dengan aroma bergamot", price=35000, category="Makanan"),
                MenuItem(name="Matcha Cheesecake", description="Cheesecake no-bake dengan matcha premium", price=38000, category="Makanan"),
            ])
            session.commit()


def get_session():
    """FastAPI dependency that yields a DB session and always closes it."""
    with SessionLocal() as session:
        yield session
