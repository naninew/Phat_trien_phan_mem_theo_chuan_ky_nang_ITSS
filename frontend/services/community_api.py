"""
Community API Service
"""
from typing import List, Dict, Any, Optional
from .api_client import api_client

async def get_posts(skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    r = await api_client.get("/community/posts", params={"skip": skip, "limit": limit})
    return r.get("data", [])

async def get_post_detail(post_id: int) -> Optional[Dict[str, Any]]:
    r = await api_client.get(f"/community/posts/{post_id}")
    return r.get("data")

async def create_post(title: str, content: str, incident_type: str) -> Dict[str, Any]:
    payload = {
        "title": title,
        "content": content,
        "incident_type": incident_type
    }
    r = await api_client.post("/community/posts", data=payload)
    return r.get("data", {})

async def create_reply(post_id: int, content: str) -> Dict[str, Any]:
    payload = {"content": content}
    r = await api_client.post(f"/community/posts/{post_id}/replies", data=payload)
    return r.get("data", {})

async def mark_reply_helpful(reply_id: int) -> bool:
    r = await api_client.put(f"/community/replies/{reply_id}/helpful")
    return r.get("success") is True
async def close_post(post_id: int):
    # token = get_access_token()
    # headers = {"Authorization": f"Bearer {token}"}

    # async with httpx.AsyncClient() as client:
        r = await api_client.put(
            f"/community/posts/{post_id}",
             data={"is_closed": True},
            # headers=headers,
            # timeout=10,
        )

        return r.get("success") is True