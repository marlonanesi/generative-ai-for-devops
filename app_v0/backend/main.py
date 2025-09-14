from __future__ import annotations

import uuid
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db, engine
from .models import Base
from .schemas import ItemCreate, ItemOut, ItemUpdate
from .repository import list_items, get_item, create_item, update_item, delete_item
from .enums import Status

settings = get_settings()

app = FastAPI(title="Items API", version="0.1.0")

# CORS: permitir frontend Streamlit padrão
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)

@app.on_event("startup")
def startup_event() -> None:
    # Criação automática apenas para fins didáticos (ver README)
    Base.metadata.create_all(bind=engine)

@app.get("/items", response_model=List[ItemOut])
def api_list_items(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Status | None = Query(None),
    db: Session = Depends(get_db)
):
    return list_items(db, limit=limit, offset=offset, status=status)

@app.get("/items/{item_id}", response_model=ItemOut)
def api_get_item(item_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = get_item(db, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return obj

@app.post("/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def api_create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    try:
        obj = create_item(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return obj

@app.put("/items/{item_id}", response_model=ItemOut)
def api_update_item(item_id: uuid.UUID, payload: ItemUpdate, db: Session = Depends(get_db)):
    obj = update_item(db, item_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return obj

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_item(item_id: uuid.UUID, db: Session = Depends(get_db)):
    ok = delete_item(db, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return None
