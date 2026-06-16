"""Application entry point — equivalent of Application.kt.

Run with:  uvicorn teahouse.main:app --host 0.0.0.0 --port 8080
"""

import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import configure_databases, get_session
from .models import Member, Transaction
from .routes import transactions
from .schemas import (
    AuthResponse,
    LoginRequest,
    MemberOut,
    RegisterRequest,
    TransactionOut,
)
from .security import generate_token, require_jwt


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_databases()
    yield


app = FastAPI(title="Tea House API", lifespan=lifespan)


@app.get("/", response_class=PlainTextResponse)
def root() -> str:
    return "Tea House API is Live!"


@app.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest, session: Session = Depends(get_session)
) -> AuthResponse:
    # Phone is the login identifier, so reject duplicates with 409.
    existing = session.scalar(select(Member).where(Member.phone == request.phone))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number is already registered",
        )

    member = Member(
        id=str(uuid.uuid4()),
        name=request.name,
        email=request.email,
        phone=request.phone,
        points=0,
        tier="Bronze",
    )
    session.add(member)
    session.commit()
    session.refresh(member)

    return AuthResponse(
        token=generate_token(member.id),
        member_id=member.id,
        member=MemberOut.model_validate(member),
    )


@app.post("/login", response_model=AuthResponse)
def login(
    request: LoginRequest, session: Session = Depends(get_session)
) -> AuthResponse:
    # Look the member up by phone and issue a token for *their* id (no longer a
    # hardcoded mock). The seeded demo member "Andi" logs in via phone too.
    member = session.scalar(select(Member).where(Member.phone == request.phone))
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phone number is not registered",
        )

    return AuthResponse(
        token=generate_token(member.id),
        member_id=member.id,
        member=MemberOut.model_validate(member),
    )


@app.get("/members/{member_id}", response_model=MemberOut)
def get_member(
    member_id: str,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_jwt),
) -> Member:
    # Protected + ownership check: a member may only read their own profile.
    if payload.get("id") != member_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own profile",
        )
    member = session.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return member


@app.get("/members/{member_id}/transactions", response_model=list[TransactionOut])
def get_member_transactions(
    member_id: str,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_jwt),
) -> list[Transaction]:
    # Protected + ownership check: only your own transaction history.
    if payload.get("id") != member_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own transactions",
        )
    if session.get(Member, member_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return list(
        session.scalars(
            select(Transaction).where(Transaction.member_id == member_id)
        )
    )


app.include_router(transactions.router)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
