from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: str = "admin"

class UserUpdate(BaseModel):
    password: Optional[str] = None