import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import Member, MenuItem, Order, OrderItem, Transaction
from ..schemas import CreateOrderRequest, OrderItemOut, OrderOut, UpdateOrderStatusRequest
from ..security import require_jwt

router = APIRouter(prefix="/orders")


def _load_order_out(order: Order, session: Session) -> OrderOut:
    items = list(session.scalars(select(OrderItem).where(OrderItem.order_id == order.id)))
    out = OrderOut.model_validate(order)
    out.items = [OrderItemOut.model_validate(i) for i in items]
    return out


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_jwt)])
def create_order(request: CreateOrderRequest, session: Session = Depends(get_session)) -> OrderOut:
    member = session.get(Member, request.member_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    order_items: list[OrderItem] = []
    total = 0.0
    for item_in in request.items:
        menu_item = session.get(MenuItem, item_in.menu_item_id)
        if menu_item is None:
            raise HTTPException(status_code=404, detail=f"MenuItem {item_in.menu_item_id} not found")
        total += menu_item.price * item_in.quantity
        order_items.append(OrderItem(
            menu_item_id=menu_item.id,
            menu_item_name=menu_item.name,
            quantity=item_in.quantity,
            unit_price=menu_item.price,
        ))

    order = Order(
        member_id=request.member_id,
        total_amount=total,
        status="PENDING",
        created_at=str(int(time.time() * 1000)),
    )
    session.add(order)
    session.flush()

    for oi in order_items:
        oi.order_id = order.id
        session.add(oi)

    session.commit()
    return _load_order_out(order, session)


@router.get("", response_model=list[OrderOut])
def list_orders(
    status: str | None = None,
    session: Session = Depends(get_session),
) -> list[OrderOut]:
    query = select(Order).order_by(Order.created_at.desc())
    if status:
        query = query.where(Order.status == status)
    orders = list(session.scalars(query))
    return [_load_order_out(o, session) for o in orders]


@router.get("/{order_id}", response_model=OrderOut, dependencies=[Depends(require_jwt)])
def get_order(order_id: str, session: Session = Depends(get_session)) -> OrderOut:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return _load_order_out(order, session)


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    session: Session = Depends(get_session),
) -> OrderOut:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if request.status not in ("PENDING", "RECEIVED", "CANCELLED"):
        raise HTTPException(status_code=400, detail="Status harus PENDING, RECEIVED, atau CANCELLED")

    was_pending = order.status == "PENDING"
    order.status = request.status

    if request.status == "RECEIVED" and was_pending:
        member = session.get(Member, order.member_id)
        if member:
            points_to_add = int(order.total_amount // 5000)
            member.points += points_to_add
            if member.points >= 1000:
                member.tier = "Platinum"
            elif member.points >= 500:
                member.tier = "Gold"
            elif member.points >= 200:
                member.tier = "Silver"
            else:
                member.tier = "Bronze"
            session.add(Transaction(
                id=str(uuid.uuid4()),
                member_id=order.member_id,
                amount=order.total_amount,
                points_earned=points_to_add,
                date=str(int(time.time() * 1000)),
                type="PURCHASE",
                order_id=order.id,
            ))

    session.commit()
    return _load_order_out(order, session)
