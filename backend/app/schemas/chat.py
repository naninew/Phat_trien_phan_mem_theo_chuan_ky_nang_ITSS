from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class MessageCreate(BaseModel):
    request_id: int
    content: str
    receiver_id: int
    sender_type: str  # 'customer' or 'company'

class MessageResponse(BaseModel):
    id: int
    request_id: int
    sender_id: int
    receiver_id: int
    sender_type: str
    content: str
    is_read: bool
    sent_time: datetime

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: int
    receiver_id: int
    request_id: Optional[int]
    title: str
    content: str
    is_read: bool
    sent_time: datetime

    class Config:
        from_attributes = True
