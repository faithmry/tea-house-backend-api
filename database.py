import os
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Member, MenuItem
from .security import hash_password

_DB_PATH = Path(__file__).parent / "tea_house.db"


def _build_engine():
    database_url = os.getenv("DATABASE_URL")

    if database_url and database_url.startswith(("postgresql", "postgres")):
        url = database_url.replace("postgres://", "postgresql://", 1)
        user = os.getenv("DATABASE_USER")
        password = os.getenv("DATABASE_PASSWORD")
        if user and "@" not in url.split("//", 1)[1]:
            cred = user if not password else f"{user}:{password}"
            url = url.replace("postgresql://", f"postgresql://{cred}@", 1)
        return create_engine(url, pool_pre_ping=True)

    return create_engine(
        f"sqlite+pysqlite:///{_DB_PATH}",
        connect_args={"check_same_thread": False},
    )


engine = _build_engine()
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False
)


def configure_databases() -> None:
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        member_exists = session.scalar(select(Member).limit(1)) is not None
        if not member_exists:
            session.add(
                Member(
                    id="001",
                    name="Andi",
                    email="andi@example.com",
                    phone="08123456789",
                    points=1000,
                    tier="Gold",
                    password_hash=hash_password("password123"),
                )
            )
            session.commit()

        menu_exists = session.scalar(select(MenuItem).limit(1)) is not None
        if not menu_exists:
            session.add_all([
                # Minuman (8)
                MenuItem(name="Green Tea Latte",   description="Premium matcha dengan susu segar",         price=28000, category="Minuman"),
                MenuItem(name="Oolong Milk Tea",   description="Oolong klasik dengan susu fresh",           price=25000, category="Minuman"),
                MenuItem(name="Jasmine Cold Brew", description="Cold brew teh melati yang menyegarkan",     price=22000, category="Minuman"),
                MenuItem(name="Taro Milk Tea",     description="Boba taro ungu dengan susu fresh",          price=27000, category="Minuman"),
                MenuItem(name="Brown Sugar Boba",  description="Boba dengan gula aren dan susu",            price=29000, category="Minuman"),
                MenuItem(name="Matcha Smoothie",   description="Matcha blend dengan yogurt dan madu",       price=32000, category="Minuman"),
                MenuItem(name="Lychee Oolong",     description="Oolong segar dengan lychee asli",           price=26000, category="Minuman"),
                MenuItem(name="Honey Lemon Tea",   description="Teh hitam dengan lemon dan madu",           price=23000, category="Minuman"),
                # Makanan (8)
                MenuItem(name="Earl Grey Cake",    description="Kue sponge dengan aroma bergamot",          price=35000, category="Makanan"),
                MenuItem(name="Matcha Cheesecake", description="Cheesecake no-bake dengan matcha premium",  price=38000, category="Makanan"),
                MenuItem(name="Onigiri Salmon",    description="Onigiri isi salmon mayo",                   price=25000, category="Makanan"),
                MenuItem(name="Croissant Matcha",  description="Croissant lapis matcha butter",             price=32000, category="Makanan"),
                MenuItem(name="Sandwich Tuna",     description="Sandwich roti tawar dengan tuna segar",     price=28000, category="Makanan"),
                MenuItem(name="Toast Butter Kaya", description="Roti toast dengan butter dan kaya",         price=22000, category="Makanan"),
                MenuItem(name="Mochi Ice Cream",   description="Mochi kenyal isi es krim matcha",           price=30000, category="Makanan"),
                MenuItem(name="Waffle Matcha",     description="Waffle crispy dengan topping matcha sauce", price=35000, category="Makanan"),
            ])
            session.commit()


def get_session():
    with SessionLocal() as session:
        yield session
