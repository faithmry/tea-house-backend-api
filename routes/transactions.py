import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import Member, Transaction
from ..schemas import MemberOut, TransactionRequest
from ..security import require_jwt

router = APIRouter(prefix="/transactions", dependencies=[Depends(require_jwt)])


@router.post("", response_model=MemberOut)
def create_transaction(
    request: TransactionRequest,
    session: Session = Depends(get_session),
) -> Member:
    member = session.get(Member, request.member_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    points_to_add = int(request.amount // 5000)
    member.points += points_to_add

    session.add(
        Transaction(
            id=str(uuid.uuid4()),
            member_id=request.member_id,
            amount=request.amount,
            points_earned=points_to_add,
            date=str(int(time.time() * 1000)),
            type="PURCHASE",
        )
    )

    session.commit()
    session.refresh(member)
    return member
