from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.community import PostCreate, PostUpdate, PostResponse, ReplyCreate, ReplyResponse
from app.services import auth_svc, community_svc
from app.utils.response import success_response

router = APIRouter(prefix="/community", tags=["Community"])

@router.post("/posts", response_model=dict)
def create_post(
    post_data: PostCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Tạo bài đăng mới trên cộng đồng."""
    post = community_svc.create_post(db, current_user["user_id"], post_data)
    # Prepare response data manually because of user_name relation mapping
    data = {
        "id": post.id,
        "user_id": post.user_id,
        "user_name": post.user.full_name,
        "title": post.title,
        "content": post.content,
        "incident_type": post.incident_type,
        "is_closed": post.is_closed,
        "created_at": post.created_at.isoformat()
    }
    return success_response(data=data, message="Đã tạo bài đăng")

@router.get("/posts", response_model=dict)
def get_posts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Lấy danh sách bài đăng."""
    posts = community_svc.get_posts(db, skip, limit)
    data = []
    for p in posts:
        data.append({
            "id": p.id,
            "user_id": p.user_id,
            "user_name": p.user.full_name,
            "title": p.title,
            "content": p.content,
            "incident_type": p.incident_type,
            "is_closed": p.is_closed,
            "created_at": p.created_at.isoformat(),
            "reply_count": len(p.replies)
        })
    return success_response(data=data)

@router.get("/posts/{post_id}", response_model=dict)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Chi tiết một bài đăng kèm các phản hồi."""
    post = community_svc.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài đăng")
    
    data = {
        "id": post.id,
        "user_id": post.user_id,
        "user_name": post.user.full_name,
        "title": post.title,
        "content": post.content,
        "images": post.images,
        "incident_type": post.incident_type,
        "is_closed": post.is_closed,
        "created_at": post.created_at.isoformat(),
        "replies": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "user_name": r.user.full_name,
                "content": r.content,
                "is_helpful": r.is_helpful,
                "created_at": r.created_at.isoformat()
            } for r in post.replies
        ]
    }
    return success_response(data=data)

@router.post("/posts/{post_id}/replies", response_model=dict)
def create_reply(
    post_id: int,
    reply_data: ReplyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Phản hồi một bài đăng."""
    post = community_svc.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài đăng")
    
    reply = community_svc.create_reply(db, current_user["user_id"], post_id, reply_data)
    return success_response(data={
        "id": reply.id,
        "content": reply.content,
        "user_name": current_user["username"]
    }, message="Đã gửi phản hồi")

@router.put("/replies/{reply_id}/helpful", response_model=dict)
def mark_helpful(
    reply_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Đánh dấu phản hồi là hữu ích."""
    ok = community_svc.mark_reply_helpful(db, reply_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy phản hồi")
    return success_response(data={}, message="Đã đánh dấu hữu ích")
