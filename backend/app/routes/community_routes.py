import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.community import PostCreate, PostUpdate, PostResponse, ReplyCreate, ReplyResponse
from app.services import auth_svc, community_svc
from app.utils.response import success_response

router = APIRouter(prefix="/community", tags=["Community"])

COMMUNITY_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "community")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024


def _validate_community_image(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}",
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_IMAGE_SIZE // (1024 * 1024)}MB",
        )


@router.post("/upload-image", response_model=dict)
def upload_community_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Upload ảnh cho bài đăng cộng đồng."""
    _validate_community_image(file)
    os.makedirs(COMMUNITY_UPLOAD_DIR, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    filename = f"{current_user['user_id']}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(COMMUNITY_UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    image_url = f"/uploads/community/{filename}"
    return success_response(data={"image_url": image_url}, message="Đã tải ảnh lên")

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
        "user_avatar_url": post.user.avatar_url,
        "title": post.title,
        "content": post.content,
        "images": post.images,
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
            "user_avatar_url": p.user.avatar_url,
            "title": p.title,
            "content": p.content,
            "images": p.images,
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
        "user_avatar_url": post.user.avatar_url,
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
                "user_avatar_url": r.user.avatar_url,
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
        "user_name": reply.user.full_name,
        "user_avatar_url": reply.user.avatar_url,
        "created_at": reply.created_at.isoformat(),
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
@router.put("/posts/{post_id}", response_model=dict)
def update_post(
    post_id: int,
    post_data: PostUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    post = community_svc.update_post(
        db,
        post_id,
        current_user["user_id"],
        post_data
    )

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy bài đăng hoặc bạn không có quyền sửa"
        )

    return success_response(
        data={
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "is_closed": post.is_closed,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        },
        message="Cập nhật bài đăng thành công"
    )


@router.delete("/posts/{post_id}", response_model=dict)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    ok = community_svc.delete_post(db, post_id, current_user["user_id"])
    if not ok:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy bài đăng hoặc bạn không có quyền xoá",
        )

    return success_response(data={"id": post_id}, message="Đã xoá bài đăng")


@router.post("/posts/{post_id}/delete", response_model=dict)
def delete_post_action(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    ok = community_svc.delete_post(db, post_id, current_user["user_id"])
    if not ok:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy bài đăng hoặc bạn không có quyền xoá",
        )

    return success_response(data={"id": post_id}, message="Đã xoá bài đăng")
