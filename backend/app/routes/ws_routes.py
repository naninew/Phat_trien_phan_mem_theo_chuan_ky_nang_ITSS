"""
WebSocket routes for real-time chat between customer and company.
"""
import json
import logging
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services import chat_svc, rescue_svc
from app.utils.jwt_helper import decode_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket Chat"])


# ──────────────────────────────────────────────────────────────────────────────
# Connection Manager
# ──────────────────────────────────────────────────────────────────────────────

class ConnectionManager:
    """Quản lý WebSocket connections theo room (request_id)."""

    def __init__(self):
        # { request_id: [ (websocket, user_id, sender_name) ] }
        self.rooms: Dict[int, List[tuple]] = {}

    async def connect(self, request_id: int, websocket: WebSocket,
                      user_id: int, sender_name: str):
        await websocket.accept()
        if request_id not in self.rooms:
            self.rooms[request_id] = []
        self.rooms[request_id].append((websocket, user_id, sender_name))
        logger.info(
            f"[WS] User {user_id} ({sender_name}) joined room {request_id}. "
            f"Total: {len(self.rooms[request_id])}"
        )

    def disconnect(self, request_id: int, websocket: WebSocket):
        if request_id in self.rooms:
            self.rooms[request_id] = [
                e for e in self.rooms[request_id] if e[0] is not websocket
            ]
            if not self.rooms[request_id]:
                del self.rooms[request_id]
        logger.info(f"[WS] Client disconnected from room {request_id}")

    async def broadcast(self, request_id: int, payload: dict,
                        exclude_ws: WebSocket = None):
        """Gửi message tới tất cả clients trong room, trừ exclude_ws."""
        if request_id not in self.rooms:
            return
        dead = []
        for (ws, uid, name) in self.rooms[request_id]:
            if ws is exclude_ws:
                continue
            try:
                await ws.send_text(json.dumps(payload, ensure_ascii=False))
            except Exception as e:
                logger.warning(f"[WS] Failed to send to user {uid}: {e}")
                dead.append(ws)
        # Cleanup dead connections
        if dead:
            self.rooms[request_id] = [
                e for e in self.rooms[request_id] if e[0] not in dead
            ]

    async def broadcast_chat_message(self, request_id: int, message_id: int, content: str,
                                     sender_id: int, sender_name: str, created_at: str):
        """Gửi message tới tất cả clients trong room, tự động set 'is_me' dựa trên user_id."""
        if request_id not in self.rooms:
            return
        dead = []
        for (ws, uid, name) in self.rooms[request_id]:
            payload = {
                "type": "message",
                "id": message_id,
                "message": content,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "is_me": uid == sender_id,
                "created_at": created_at,
            }
            try:
                await ws.send_text(json.dumps(payload, ensure_ascii=False))
            except Exception as e:
                logger.warning(f"[WS] Failed to send to user {uid}: {e}")
                dead.append(ws)
        # Cleanup dead connections
        if dead:
            self.rooms[request_id] = [
                e for e in self.rooms[request_id] if e[0] not in dead
            ]


manager = ConnectionManager()


# ──────────────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────────────

def _get_sender_display_name(msg) -> str:
    try:
        user = msg.sender
        return user.full_name or user.username or f"User#{msg.sender_id}"
    except Exception:
        return f"User#{msg.sender_id}"


# ──────────────────────────────────────────────────────────────────────────────
# WebSocket Endpoint
# ──────────────────────────────────────────────────────────────────────────────

@router.websocket("/chat/{request_id}")
async def websocket_chat(
    request_id: int,
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    """
    WebSocket real-time chat endpoint.
    URL: ws://host/api/v1/ws/chat/{request_id}?token=<JWT>

    Protocol:
      - Server → Client on connect: { "type": "history", "messages": [...] }
      - Client → Server to send:    { "type": "message", "message": "..." }
      - Server → Client on message: { "type": "message", "message": "...",
                                      "sender_name": "...", "is_me": bool,
                                      "created_at": "HH:MM dd/mm", "id": int }
      - Client → Server keepalive:  { "type": "ping" }
      - Server → Client keepalive:  { "type": "pong" }
    """
    db: Session = SessionLocal()
    try:
        # ── 1. Xác thực token ────────────────────────────────────────────────
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Unauthorized: invalid token")
            return

        user_id: int = payload.get("user_id")
        role: str = payload.get("role", "")
        username: str = payload.get("username", "")

        if not user_id:
            await websocket.close(code=4001, reason="Unauthorized: missing user_id")
            return

        # ── 2. Kiểm tra quyền truy cập request ──────────────────────────────
        req = rescue_svc.get_request_by_id(db, request_id)
        if not req:
            await websocket.close(code=4004, reason="Request not found")
            return

        if role == "customer" and req.user_id != user_id:
            await websocket.close(code=4003, reason="Forbidden")
            return

        if role == "company_staff":
            company = rescue_svc.get_company_by_owner_id(db, user_id)
            if not company or req.company_id != company.id:
                await websocket.close(code=4003, reason="Forbidden")
                return

        # Lấy tên hiển thị
        sender_name = username
        try:
            from app.services.auth_svc import get_user_by_id
            db_user = get_user_by_id(db, user_id)
            if db_user and db_user.full_name:
                sender_name = db_user.full_name
        except Exception:
            pass

        # ── 3. Connect & gửi lịch sử ─────────────────────────────────────────
        await manager.connect(request_id, websocket, user_id, sender_name)

        history = chat_svc.get_messages_by_request(db, request_id)
        history_msgs = []
        from datetime import timedelta
        for m in history:
            local_time = m.sent_time + timedelta(hours=7)
            history_msgs.append({
                "id": m.id,
                "message": m.content,
                "sender_id": m.sender_id,
                "sender_name": _get_sender_display_name(m),
                "is_me": m.sender_id == user_id,
                "created_at": local_time.strftime("%H:%M %d/%m"),
            })

        await websocket.send_text(json.dumps(
            {"type": "history", "messages": history_msgs},
            ensure_ascii=False
        ))

        # ── 4. Lắng nghe message ─────────────────────────────────────────────
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type", "message")

            # Keepalive
            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            # Tin nhắn thực sự
            content = data.get("message", "").strip()
            if not content:
                continue

            sender_type = "customer" if role == "customer" else "company"

            # Lưu DB
            from app.schemas.chat import MessageCreate
            msg_data = MessageCreate(
                request_id=request_id,
                receiver_id=0,
                sender_type=sender_type,
                content=content,
            )
            saved = chat_svc.send_message(db, user_id, msg_data)

            from datetime import timedelta
            local_time = saved.sent_time + timedelta(hours=7)
            created_at_str = local_time.strftime("%H:%M %d/%m")

            # Echo lại cho chính sender (is_me=True)
            await websocket.send_text(json.dumps({
                "type": "message",
                "id": saved.id,
                "message": content,
                "sender_id": user_id,
                "sender_name": sender_name,
                "is_me": True,
                "created_at": created_at_str,
            }, ensure_ascii=False))

            # Broadcast tới tất cả clients khác trong room (is_me=False)
            await manager.broadcast(request_id, {
                "type": "message",
                "id": saved.id,
                "message": content,
                "sender_id": user_id,
                "sender_name": sender_name,
                "is_me": False,
                "created_at": created_at_str,
            }, exclude_ws=websocket)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"[WS] Error in room {request_id}: {e}", exc_info=True)
    finally:
        manager.disconnect(request_id, websocket)
        db.close()
