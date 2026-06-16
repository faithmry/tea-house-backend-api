"""Database models (equivalent of Exposed tables + serializable data classes).

The SQLAlchemy ORM classes mirror the Exposed `Members` / `Transactions`
tables, while the Pydantic schemas in `schemas.py` play the role of the
`@Serializable` Kotlin data classes used for the JSON request/response bodies.
"""

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Member(Base):
    __tablename__ = "members"

    # New members get an unguessable UUID (mitigates id enumeration on the
    # public lookup). The demo member is seeded with an explicit id instead.
    id: Mapped[str] = mapped_column(
        String(50), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))
    # Phone is the login identifier, so it must be unique.
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    points: Mapped[int] = mapped_column(Integer, default=0)
    tier: Mapped[str] = mapped_column(String(20), default="Bronze")
    profile_picture_url: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    member_id: Mapped[str] = mapped_column(String(50), ForeignKey("members.id"))
    amount: Mapped[float] = mapped_column(Float)
    points_earned: Mapped[int] = mapped_column(Integer)
    date: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(20), default="PURCHASE")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255), default="")
    price: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(50), default="Drink")
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id: Mapped[str] = mapped_column(String(50), ForeignKey("members.id"))
    total_amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    created_at: Mapped[str] = mapped_column(String(50))


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(String(50), ForeignKey("orders.id"))
    menu_item_id: Mapped[str] = mapped_column(String(50), ForeignKey("menu_items.id"))
    menu_item_name: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
