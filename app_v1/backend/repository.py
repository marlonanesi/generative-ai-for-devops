from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ItemORM
from .schemas import ItemCreate, ItemUpdate
from .enums import Status

MAX_LIMIT = 200

def list_items(session: Session, limit: int = 50, offset: int = 0, status: Status | None = None) -> Sequence[ItemORM]:
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
    stmt = select(ItemORM).offset(offset).limit(limit).order_by(ItemORM.created_at.desc())
    if status:
        stmt = select(ItemORM).where(ItemORM.status == status).offset(offset).limit(limit).order_by(ItemORM.created_at.desc())
    return session.execute(stmt).scalars().all()

def get_item(session: Session, id: uuid.UUID) -> ItemORM | None:
    return session.get(ItemORM, id)

def create_item(session: Session, data: ItemCreate) -> ItemORM:
    obj = ItemORM(
        title=data.title,
        description=data.description,
        status=data.status or Status.pending,
    )
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

def update_item(session: Session, id: uuid.UUID, data: ItemUpdate) -> ItemORM | None:
    obj = session.get(ItemORM, id)
    if not obj:
        return None
    if data.title is not None:
        obj.title = data.title
    if data.description is not None:
        obj.description = data.description
    if data.status is not None:
        obj.status = data.status
    session.commit()
    session.refresh(obj)
    return obj

def delete_item(session: Session, id: uuid.UUID) -> bool:
    obj = session.get(ItemORM, id)
    if not obj:
        return False
    session.delete(obj)
    session.commit()
    return True
