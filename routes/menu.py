from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import MenuItem
from ..schemas import MenuItemOut

router = APIRouter(prefix="/menu")


@router.get("", response_model=list[MenuItemOut])
def get_menu(session: Session = Depends(get_session)) -> list[MenuItem]:
    return list(session.scalars(select(MenuItem).where(MenuItem.is_available == True)))
