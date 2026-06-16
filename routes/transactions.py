"""Transaction routes — equivalent of routes/TransactionRoutes.kt.

Protected by JWT (the `require_jwt` dependency), like the Ktor
`authenticate("auth-jwt") { transactionRouting() }` block.
"""

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
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
    # BUGFIX: the Kotlin version updated points (0 rows if the member was
    # missing) but still inserted a Transaction referencing a non-existent
    # member_id — an orphan row / FK violation — before returning 404. Here we
    # verify the member exists first and abort cleanly if not.
    member = session.get(Member, request.member_id)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    # 1. SERVER-SIDE CALCULATION: Rp 5.000 = 1 Point
    points_to_add = int(request.amount // 5000)

    # 2. Update member points.
    member.points += points_to_add

    # 3. Log the transaction.
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

    # 4. Return the updated profile.
    return member
