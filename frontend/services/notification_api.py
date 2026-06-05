"""
Notification API service.
"""
from typing import Any, Dict, List

from services.api_client import api_client


async def get_notifications(unread_only: bool = False) -> List[Dict[str, Any]]:
    r = await api_client.get("/chat/notifications", params={"unread_only": unread_only})
    return r.get("data", [])


async def mark_notification_read(notification_id: int) -> bool:
    r = await api_client.put(f"/chat/notifications/{notification_id}/read")
    return r.get("success") is True


async def mark_all_notifications_read() -> bool:
    r = await api_client.put("/chat/notifications/read-all")
    return r.get("success") is True
