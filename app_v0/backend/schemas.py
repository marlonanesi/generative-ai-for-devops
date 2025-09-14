from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_validator

from .enums import Status

class ConfigUUIDModel(BaseModel):
    class Config:
        json_encoders = {uuid.UUID: str}

class ItemBase(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Status | None = None

class ItemCreate(ItemBase):
    title: str

    @field_validator('title')
    def title_not_empty(cls, v: str) -> str:
        v2 = v.strip()
        if not v2:
            raise ValueError('title não pode ser vazio')
        return v2

class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Status | None = None

    @field_validator('title')
    def title_not_empty_if_present(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v2 = v.strip()
        if not v2:
            raise ValueError('title não pode ser vazio')
        return v2

class ItemOut(ConfigUUIDModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: Status
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
