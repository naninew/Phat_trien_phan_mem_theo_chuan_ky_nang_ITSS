"""
Centralized notification service for system alerts.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.communication import Notification
from app.models.company import RescueCompany


class NotificationType:
    SYSTEM = "SYSTEM"
    ACCOUNT_SUSPENDED = "ACCOUNT_SUSPENDED"
    ACCOUNT_VERIFIED = "ACCOUNT_VERIFIED"
    ACCOUNT_REJECTED = "ACCOUNT_REJECTED"
    REVIEW_DELETED = "REVIEW_DELETED"
    POST_DELETED = "POST_DELETED"
    REQUEST_UPDATE = "REQUEST_UPDATE"


_DEFAULT_TITLES = {
    NotificationType.SYSTEM: "Thông báo hệ thống",
    NotificationType.ACCOUNT_SUSPENDED: "Tạm khóa tài khoản",
    NotificationType.ACCOUNT_VERIFIED: "Xác minh tài khoản",
    NotificationType.ACCOUNT_REJECTED: "Từ chối xác minh",
    NotificationType.REVIEW_DELETED: "Đánh giá bị xóa",
    NotificationType.POST_DELETED: "Bài đăng bị xóa",
    NotificationType.REQUEST_UPDATE: "Cập nhật yêu cầu",
}


def send_notification(
    db: Session,
    user_id: int,
    message: str,
    notification_type: str = NotificationType.SYSTEM,
    title: Optional[str] = None,
    request_id: Optional[int] = None,
) -> Notification:
    """Create a notification for a user. Caller is responsible for db.commit()."""
    notif = Notification(
        receiver_id=user_id,
        title=title or _DEFAULT_TITLES.get(notification_type, "Thông báo hệ thống"),
        content=message,
        notification_type=notification_type,
        request_id=request_id,
        sent_time=datetime.utcnow(),
    )
    db.add(notif)
    return notif


def send_notification_to_company(
    db: Session,
    company_id: int,
    message: str,
    notification_type: str = NotificationType.SYSTEM,
    title: Optional[str] = None,
) -> None:
    """Send notification to the owner account of a rescue company."""
    company = db.query(RescueCompany).filter(RescueCompany.id == company_id).first()
    if not company:
        return
    send_notification(
        db,
        company.owner_id,
        message,
        notification_type=notification_type,
        title=title,
    )
