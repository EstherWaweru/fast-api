from enum import Enum

from pydantic import BaseModel
from typing import List, Optional


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int
    status: Optional[str] = None

    class Config:
        orm_mode = True


class UserId(BaseModel):
    id: int


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    items: List[Item] = []

    class Config:
        orm_mode = True


class ItemStatusChoices(Enum):
    NEW = "NEW"
    APPROVED = "APPROVED"
    EOL = "EOL"


class ItemStatus(BaseModel):
    status: ItemStatusChoices
