from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone_number: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone_number: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProfilePic(BaseModel):
    user_id: int
    file_data: bytes

    class Config:
        arbitrary_types_allowed = True
