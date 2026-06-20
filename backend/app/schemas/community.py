from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ReplyCreate(BaseModel):
    content: str

class ReplyResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    user_name: str
    user_avatar_url: Optional[str] = None
    content: str
    is_helpful: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    title: str
    content: str
    incident_type: Optional[str] = None
    images: Optional[str] = None

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_closed: Optional[bool] = None

class PostResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_avatar_url: Optional[str] = None
    title: str
    content: str
    images: Optional[str]
    incident_type: Optional[str]
    is_closed: bool
    created_at: datetime
    replies: List[ReplyResponse] = []

    class Config:
        from_attributes = True
