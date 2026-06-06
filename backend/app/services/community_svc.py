from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.community import CommunityPost, CommunityReply
from app.schemas.community import PostCreate, PostUpdate, ReplyCreate

def create_post(db: Session, user_id: int, post_data: PostCreate) -> CommunityPost:
    new_post = CommunityPost(
        user_id=user_id,
        title=post_data.title,
        content=post_data.content,
        incident_type=post_data.incident_type,
        images=post_data.images,
        created_at=datetime.utcnow()
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

def get_posts(db: Session, skip: int = 0, limit: int = 20) -> List[CommunityPost]:
    return db.query(CommunityPost).order_by(CommunityPost.created_at.desc()).offset(skip).limit(limit).all()

def get_post_by_id(db: Session, post_id: int) -> Optional[CommunityPost]:
    return db.query(CommunityPost).filter(CommunityPost.id == post_id).first()

def update_post(db: Session, post_id: int, user_id: int, post_data: PostUpdate) -> Optional[CommunityPost]:
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id, CommunityPost.user_id == user_id).first()
    if not post:
        return None
    
    if post_data.title is not None: post.title = post_data.title
    if post_data.content is not None: post.content = post_data.content
    if post_data.is_closed is not None: post.is_closed = post_data.is_closed
    
    db.commit()
    db.refresh(post)
    return post

def delete_post(db: Session, post_id: int, user_id: int) -> bool:
    post = db.query(CommunityPost).filter(
        CommunityPost.id == post_id,
        CommunityPost.user_id == user_id,
    ).first()
    if not post:
        return False

    db.delete(post)
    db.commit()
    return True

def create_reply(db: Session, user_id: int, post_id: int, reply_data: ReplyCreate) -> CommunityReply:
    new_reply = CommunityReply(
        post_id=post_id,
        user_id=user_id,
        content=reply_data.content,
        created_at=datetime.utcnow()
    )
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)
    return new_reply

def mark_reply_helpful(db: Session, reply_id: int) -> bool:
    reply = db.query(CommunityReply).filter(CommunityReply.id == reply_id).first()
    if reply:
        reply.is_helpful = True
        db.commit()
        return True
    return False
