"""
Community API Service
"""
from typing import List, Dict, Any, Optional

import httpx
from nicegui import app, ui

from core.config import BACKEND_URL, SESSION_TOKEN_KEY
from .api_client import api_client

async def get_posts(skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    r = await api_client.get("/community/posts", params={"skip": skip, "limit": limit})
    return r.get("data", [])

async def get_post_detail(post_id: int) -> Optional[Dict[str, Any]]:
    r = await api_client.get(f"/community/posts/{post_id}")
    return r.get("data")

async def create_post(title: str, content: str, incident_type: str, image_url: str = "") -> Dict[str, Any]:
    payload = {
        "title": title,
        "content": content,
        "incident_type": incident_type
    }
    if image_url:
        payload["images"] = image_url
    r = await api_client.post("/community/posts", data=payload)
    return r.get("data", {})

async def upload_community_image(filename: str, content: bytes, content_type: str) -> str:
    token = app.storage.user.get(SESSION_TOKEN_KEY)
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BACKEND_URL}/community/upload-image",
                files={"file": (filename, content, content_type)},
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data") or {}
            return data.get("image_url") or ""
        except httpx.HTTPStatusError as exc:
            detail = "Không thể tải ảnh lên"
            try:
                detail = exc.response.json().get("detail", detail)
            except Exception:
                pass
            ui.notify(detail, type="negative")
        except Exception as exc:
            ui.notify(f"Lỗi tải ảnh: {exc}", type="negative")
    return ""

async def create_reply(post_id: int, content: str) -> Dict[str, Any]:
    payload = {"content": content}
    r = await api_client.post(f"/community/posts/{post_id}/replies", data=payload)
    return r.get("data", {})

async def mark_reply_helpful(reply_id: int) -> bool:
    r = await api_client.put(f"/community/replies/{reply_id}/helpful")
    return r.get("success") is True

async def delete_post(post_id: int) -> bool:
    r = await api_client.post(f"/community/posts/{post_id}/delete")
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
