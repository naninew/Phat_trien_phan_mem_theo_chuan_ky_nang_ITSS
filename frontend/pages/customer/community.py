"""
Community Page - NiceGUI
"""
import inspect
import mimetypes
import os
from datetime import datetime
from typing import Any, Dict, List

from nicegui import ui

from components.page_layout import page_layout
from core.auth import get_current_user, require_role
from core.config import BACKEND_URL
from services.api_client import api_client
from services.community_api import (
    close_post,
    create_post,
    create_reply,
    delete_post,
    get_post_detail,
    get_posts,
    mark_reply_helpful,
    upload_community_image,
)


COMMUNITY_TOPICS = {
    "all": {"label": "Tất cả", "icon": "dynamic_feed"},
    "qa": {"label": "Hỏi đáp", "icon": "help"},
    "experience": {"label": "Kinh nghiệm", "icon": "construction"},
    "review": {"label": "Review", "icon": "verified"},
    "alert": {"label": "Cảnh báo", "icon": "warning"},
}

POST_TOPIC_OPTIONS = {
    "Hỏi đáp": "Hỏi đáp",
    "Kinh nghiệm sửa xe": "Kinh nghiệm sửa xe",
    "Review đơn vị cứu hộ": "Review đơn vị cứu hộ",
    "Cảnh báo giao thông": "Cảnh báo giao thông",
    "Sự cố khẩn cấp": "Sự cố khẩn cấp",
    "Mẹo bảo dưỡng": "Mẹo bảo dưỡng",
    "Khác": "Khác",
}


TOPIC_BADGE_CLASSES = {
    "qa": "bg-sky-50 text-sky-800 border-sky-200",
    "experience": "bg-amber-50 text-amber-800 border-amber-200",
    "review": "bg-violet-50 text-violet-800 border-violet-200",
    "alert": "bg-rose-50 text-rose-800 border-rose-200",
}


def _topic_key(value: str | None) -> str:
    text = (value or "").lower()
    if any(word in text for word in ["hỏi", "hỏi đáp", "khác", "hỏng", "thủng", "hết xăng", "tai nạn"]):
        return "qa"
    if any(word in text for word in ["kinh nghiệm", "mẹo", "bảo dưỡng", "sửa"]):
        return "experience"
    if any(word in text for word in ["review", "đánh giá"]):
        return "review"
    if any(word in text for word in ["cảnh báo", "đường", "nguy hiểm"]):
        return "alert"
    return "qa"


def _topic_badge_classes(value: str | None) -> str:
    return TOPIC_BADGE_CLASSES.get(_topic_key(value), TOPIC_BADGE_CLASSES["qa"])


def _safe_time(value: str | None) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return datetime.min


def _format_time(value: str | None) -> str:
    parsed = _safe_time(value)
    if parsed == datetime.min:
        return "--"
    return parsed.strftime("%d/%m/%Y %H:%M")


def _post_metric(post: Dict[str, Any], kind: str) -> int:
    replies = int(post.get("reply_count") or len(post.get("replies") or []))
    return replies


def _thumbnail_url(post: Dict[str, Any]) -> str | None:
    images = post.get("images")
    if not images:
        return None
    if isinstance(images, str):
        first = images.split(",")[0].strip()
        return first or None
    if isinstance(images, list) and images:
        return images[0]
    return None


def _media_url(path: str | None) -> str:
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{BACKEND_URL.replace('/api/v1', '')}{path}"


def _avatar_url(data: Dict[str, Any]) -> str:
    return _media_url(
        data.get("user_avatar_url")
        or data.get("avatar_url")
        or data.get("user_avatar")
    )


def _excerpt(text: str | None, limit: int = 180) -> str:
    value = (text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."


async def _get_top_companies() -> List[Dict[str, Any]]:
    try:
        res = await api_client.get("/rescue/companies")
        companies = res.get("data") or []
        return sorted(
            companies,
            key=lambda c: (float(c.get("rating_avg") or 0), int(c.get("rating_count") or 0)),
            reverse=True,
        )[:3]
    except Exception:
        return []


async def _read_upload_content(upload_event) -> tuple[str, bytes, str]:
    file_obj = getattr(upload_event, "file", None)
    content_obj = getattr(upload_event, "content", None) or file_obj
    if content_obj is None or not hasattr(content_obj, "read"):
        raise ValueError("Không đọc được file ảnh đã chọn")

    raw_content = content_obj.read()
    if inspect.isawaitable(raw_content):
        raw_content = await raw_content
    if isinstance(raw_content, str):
        raw_content = raw_content.encode()
    if not raw_content:
        raise ValueError("File ảnh rỗng hoặc không hợp lệ")

    raw_name = getattr(upload_event, "name", None) or getattr(file_obj, "name", None) or "community.jpg"
    filename = os.path.basename(str(raw_name)) or "community.jpg"
    content_type = (
        getattr(upload_event, "type", None)
        or getattr(file_obj, "content_type", None)
        or mimetypes.guess_type(filename)[0]
        or "application/octet-stream"
    )
    if "." not in filename:
        filename = f"{filename}{mimetypes.guess_extension(content_type) or '.jpg'}"

    return filename, raw_content, content_type


def create_community_page():
    """Register /customer/community route."""

    @ui.page("/customer/community")
    async def community_page():
        if not require_role("customer"):
            return

        current_user = get_current_user() or {}
        current_user_id = current_user.get("id")
        state = {
            "posts": [],
            "query": "",
            "topic": "all",
            "sort": "newest",
            "top_companies": [],
        }

        ui.add_head_html("""
        <style>
            .community-page {
                width: 100%;
                max-width: 1280px;
                margin: 0 auto;
                padding: 0 4px 24px;
            }
            .community-title {
                font-size: 30px;
                font-weight: 900;
                line-height: 1.15;
                color: #0f172a;
            }
            .community-subtitle {
                color: #64748b;
                font-size: 14px;
            }
            .create-post-btn {
                min-height: 44px;
                border-radius: 12px;
                background: #2563eb;
                color: #ffffff;
                font-weight: 900;
                box-shadow: 0 8px 18px rgba(37, 99, 235, 0.18);
            }
            .community-toolbar,
            .community-panel,
            .feed-card {
                background: #ffffff;
                border: 1px solid #f1f5f9;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
            }
            .community-toolbar {
                border-radius: 16px;
                padding: 16px;
            }
            .topic-tab {
                border-radius: 999px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 800;
                cursor: pointer;
                transition: 160ms ease;
                white-space: nowrap;
            }
            .topic-tab-active {
                background: #2563eb;
                color: white;
                box-shadow: 0 1px 3px rgba(37, 99, 235, 0.16);
            }
            .topic-tab-idle {
                background: #ffffff;
                color: #475569;
                border: 1px solid #e2e8f0;
            }
            .topic-tab-idle:hover {
                background: #eff6ff;
                color: #2563eb;
            }
            .feed-card {
                border-radius: 16px;
                transition: 180ms ease;
                cursor: pointer;
                overflow: hidden;
            }
            .feed-card:hover {
                border-color: #dbeafe;
                box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
            }
            .post-title-modern {
                font-size: 19px;
                line-height: 1.25;
                font-weight: 900;
                color: #0f172a;
            }
            .post-title-modern:hover {
                color: #1d4ed8;
            }
            .post-excerpt {
                color: #475569;
                font-size: 14px;
                line-height: 1.55;
            }
            .post-thumb {
                width: 168px;
                height: 108px;
                border-radius: 12px;
                object-fit: cover;
                border: 1px solid #e2e8f0;
            }
            .comment-pill {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                color: #64748b;
                font-size: 13px;
                font-weight: 700;
            }
            .status-resolved-badge,
            .topic-badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                width: fit-content;
                border: 1px solid;
                border-radius: 999px;
                padding: 5px 10px;
                font-size: 12px;
                line-height: 1;
                font-weight: 900;
            }
            .status-resolved-badge {
                background: #dcfce7;
                border-color: #bbf7d0;
                color: #166534;
            }
            .community-panel {
                border-radius: 16px;
                padding: 16px;
            }
            .panel-title {
                font-size: 16px;
                font-weight: 950;
                color: #0f172a;
            }
            .panel-heading {
                display: flex;
                align-items: center;
                gap: 10px;
                border-radius: 14px;
                border: 1px solid;
                padding: 10px 12px;
            }
            .panel-heading-blue {
                background: #eff6ff;
                border-color: #bfdbfe;
            }
            .panel-heading-emerald {
                background: #ecfdf5;
                border-color: #a7f3d0;
            }
            .panel-heading-amber {
                background: #fffbeb;
                border-color: #fde68a;
            }
            .panel-heading-slate {
                background: #f1f5f9;
                border-color: #cbd5e1;
            }
            .panel-heading-icon {
                height: 34px;
                width: 34px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #eff6ff;
                box-shadow: inset 0 0 0 1px #dbeafe;
            }
            .panel-heading-icon-blue {
                background: #eff6ff;
                box-shadow: inset 0 0 0 1px #dbeafe;
                color: #2563eb;
            }
            .panel-heading-icon-emerald {
                background: #ecfdf5;
                box-shadow: inset 0 0 0 1px #bbf7d0;
                color: #059669;
            }
            .panel-heading-icon-amber {
                background: #fffbeb;
                box-shadow: inset 0 0 0 1px #fde68a;
                color: #d97706;
            }
            .panel-heading-icon-slate {
                background: #f1f5f9;
                box-shadow: inset 0 0 0 1px #cbd5e1;
                color: #475569;
            }
            .rank-row {
                border-radius: 14px;
                padding: 10px;
                transition: 160ms ease;
                border: 1px solid transparent;
            }
            .rank-row:hover {
                background: #f8fafc;
                border-color: #e2e8f0;
            }
            .rank-number {
                height: 34px;
                width: 34px;
                border-radius: 12px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background: #eff6ff;
                color: #1d4ed8;
                font-weight: 950;
                box-shadow: inset 0 0 0 1px #dbeafe;
            }
            .sidebar-avatar {
                height: 38px;
                width: 38px;
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #ecfdf5;
                box-shadow: inset 0 0 0 1px #bbf7d0;
            }
            .posting-tip {
                border-radius: 14px;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                padding: 10px;
            }
            .dialog-card {
                border-radius: 22px;
                box-shadow: 0 25px 70px rgba(15, 23, 42, 0.20);
            }
            .post-detail-scroll {
                overflow-y: auto;
                min-height: 0;
            }
            .post-detail-scroll::-webkit-scrollbar {
                width: 6px;
            }
            .post-detail-scroll::-webkit-scrollbar-thumb {
                background: #cbd5e1;
                border-radius: 999px;
            }
            .reply-card {
                width: 100%;
                padding: 14px;
                border-radius: 16px;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
            }
            .helpful-done {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                border-radius: 999px;
                background: #dcfce7;
                color: #166534;
                font-size: 12px;
                font-weight: 800;
            }
            .community-uploader .q-uploader {
                width: 100%;
                border-radius: 16px;
                border: 1px dashed #cbd5e1;
                box-shadow: none;
                background: #f8fafc;
            }
            .community-uploader .q-uploader__header {
                background: transparent;
                color: #2563eb;
            }
            .community-uploader .q-uploader__list {
                display: none;
            }
            .create-dialog-body {
                max-height: min(68vh, 720px);
                overflow-y: auto;
            }
            .create-dialog-body::-webkit-scrollbar {
                width: 6px;
            }
            .create-dialog-body::-webkit-scrollbar-thumb {
                background: #cbd5e1;
                border-radius: 999px;
            }
            .image-preview-box {
                width: 100%;
                min-height: 160px;
                border-radius: 16px;
                border: 1px solid #e2e8f0;
                background: #f8fafc;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .image-preview-box img {
                width: 100%;
                max-height: 260px;
                object-fit: cover;
            }
            .post-detail-image {
                width: 100%;
                min-height: 320px;
                border-radius: 18px;
                overflow: hidden;
                border: 1px solid #e2e8f0;
                background: #f8fafc;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .post-detail-photo {
                width: 100%;
                height: auto;
                max-height: 420px;
                object-fit: contain;
                display: block;
            }
            .comment-box {
                border-top: 1px solid #e2e8f0;
                background: #ffffff;
                box-shadow: 0 -8px 24px rgba(15, 23, 42, 0.04);
            }
            body.body--dark .community-page {
                color: #eaf2ff;
            }
            body.body--dark .community-title,
            body.body--dark .post-title-modern,
            body.body--dark .panel-title {
                color: #f8fbff !important;
            }
            body.body--dark .community-subtitle,
            body.body--dark .post-excerpt,
            body.body--dark .comment-pill {
                color: #a8b7cf !important;
            }
            body.body--dark .community-toolbar,
            body.body--dark .community-panel,
            body.body--dark .feed-card {
                background: rgba(17, 28, 47, 0.96) !important;
                border-color: rgba(148, 163, 184, 0.18) !important;
                box-shadow: 0 14px 32px rgba(0, 0, 0, 0.22) !important;
            }
            body.body--dark .feed-card:hover {
                border-color: rgba(96, 165, 250, 0.46) !important;
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.30) !important;
            }
            body.body--dark .topic-tab-idle {
                background: rgba(15, 23, 42, 0.86) !important;
                color: #c8d5e8 !important;
                border-color: rgba(148, 163, 184, 0.24) !important;
            }
            body.body--dark .topic-tab-idle:hover {
                background: rgba(37, 99, 235, 0.18) !important;
                color: #93c5fd !important;
                border-color: rgba(96, 165, 250, 0.38) !important;
            }
            body.body--dark .topic-tab-active,
            body.body--dark .create-post-btn {
                background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
                color: #ffffff !important;
                box-shadow: 0 12px 26px rgba(37, 99, 235, 0.28) !important;
            }
            body.body--dark .panel-heading-blue,
            body.body--dark .panel-heading-emerald,
            body.body--dark .panel-heading-amber,
            body.body--dark .panel-heading-slate,
            body.body--dark .posting-tip,
            body.body--dark .reply-card,
            body.body--dark .image-preview-box,
            body.body--dark .post-detail-image,
            body.body--dark .comment-box {
                background: rgba(13, 22, 40, 0.92) !important;
                border-color: rgba(148, 163, 184, 0.20) !important;
                color: #eaf2ff !important;
            }
            body.body--dark .panel-heading-icon,
            body.body--dark .panel-heading-icon-blue,
            body.body--dark .panel-heading-icon-emerald,
            body.body--dark .panel-heading-icon-amber,
            body.body--dark .panel-heading-icon-slate,
            body.body--dark .rank-number,
            body.body--dark .sidebar-avatar {
                background: rgba(37, 99, 235, 0.14) !important;
                box-shadow: inset 0 0 0 1px rgba(96, 165, 250, 0.28) !important;
                color: #93c5fd !important;
            }
            body.body--dark .rank-row:hover {
                background: rgba(148, 163, 184, 0.09) !important;
                border-color: rgba(148, 163, 184, 0.18) !important;
            }
            body.body--dark .status-resolved-badge {
                background: rgba(22, 101, 52, 0.22) !important;
                border-color: rgba(74, 222, 128, 0.36) !important;
                color: #bbf7d0 !important;
            }
            body.body--dark .post-thumb {
                border-color: rgba(148, 163, 184, 0.22) !important;
            }
            body.body--dark .community-toolbar .q-field__control,
            body.body--dark .community-toolbar .q-field__native,
            body.body--dark .community-toolbar .q-field__label {
                color: #eaf2ff !important;
            }
            @media (max-width: 1180px) {
                .community-grid {
                    flex-direction: column;
                    flex-wrap: nowrap;
                }
                .community-right-sidebar {
                    width: 100% !important;
                    min-width: 0 !important;
                    display: grid;
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                    gap: 14px;
                }
            }
            @media (max-width: 780px) {
                .community-page {
                    padding: 0 0 20px;
                }
                .community-title {
                    font-size: 24px;
                }
                .post-thumb {
                    width: 100%;
                    height: 170px;
                }
                .feed-card-body {
                    flex-direction: column;
                }
                .community-right-sidebar {
                    display: flex;
                    flex-direction: column;
                }
            }
        </style>
        """)

        with page_layout("/customer/community", title="Cộng Đồng Rescue"):
            with ui.column().classes("community-page w-full gap-5"):
                with ui.row().classes("w-full items-center justify-between gap-4"):
                    with ui.column().classes("gap-1"):
                        ui.label("Cộng đồng cứu hộ").classes("community-title")
                        ui.label(
                            "Hỏi đáp sự cố, chia sẻ kinh nghiệm và review dịch vụ cứu hộ từ người dùng thật."
                        ).classes("community-subtitle")
                    ui.button(
                        "Đăng bài mới",
                        icon="edit_square",
                        on_click=lambda: _open_create_dialog(),
                    ).props("unelevated no-caps").classes("create-post-btn px-5")

                with ui.element("div").classes("community-toolbar w-full"):
                    with ui.row().classes("w-full items-center gap-3 flex-wrap"):
                        search_input = ui.input(
                            placeholder="Tìm kiếm tiêu đề, nội dung, chủ đề..."
                        ).classes("min-w-[260px] flex-1").props("outlined dense rounded clearable")
                        search_input.on("update:model-value", lambda: _set_query(search_input.value))

                        sort_select = ui.select(
                            options={
                                "newest": "Mới nhất",
                                "comments": "Nhiều bình luận",
                            },
                            value="newest",
                            label="Sắp xếp",
                            on_change=lambda: _set_sort(sort_select.value),
                        ).classes("w-48").props("outlined dense rounded")

                    topic_tabs = ui.row().classes("w-full gap-2 mt-3 overflow-x-auto no-wrap")

                with ui.row().classes("community-grid w-full gap-5 items-start no-wrap"):
                    feed_container = ui.column().classes("flex-1 w-full gap-3 min-w-0")
                    right_sidebar = ui.column().classes("community-right-sidebar w-[320px] min-w-[320px] shrink-0 gap-4")

        def _set_query(value):
            state["query"] = value or ""
            _render_feed()

        def _set_sort(value):
            state["sort"] = value or "newest"
            _render_feed()

        def _set_topic(value):
            state["topic"] = value
            _render_topic_tabs()
            _render_feed()

        def _filtered_posts() -> List[Dict[str, Any]]:
            query = state["query"].strip().lower()
            result = []
            for post in state["posts"]:
                if state["topic"] != "all" and _topic_key(post.get("incident_type")) != state["topic"]:
                    continue
                if query:
                    haystack = " ".join(
                        [
                            post.get("title", ""),
                            post.get("content", ""),
                            post.get("incident_type", ""),
                            post.get("user_name", ""),
                        ]
                    ).lower()
                    if query not in haystack:
                        continue
                result.append(post)

            if state["sort"] == "comments":
                result.sort(key=lambda p: (_post_metric(p, "comments"), _safe_time(p.get("created_at"))), reverse=True)
            else:
                result.sort(key=lambda p: _safe_time(p.get("created_at")), reverse=True)
            return result

        def _render_topic_tabs():
            topic_tabs.clear()
            with topic_tabs:
                for key, meta in COMMUNITY_TOPICS.items():
                    active = state["topic"] == key
                    classes = "topic-tab topic-tab-active" if active else "topic-tab topic-tab-idle"
                    with ui.row().classes(f"items-center gap-2 {classes}").on("click", lambda e, key=key: _set_topic(key)):
                        ui.label(meta["label"])

        def _render_feed():
            feed_container.clear()
            posts = _filtered_posts()
            with feed_container:
                if not posts:
                    with ui.element("div").classes("community-panel w-full"):
                        with ui.column().classes("items-center gap-2 py-10"):
                            ui.icon("search_off", size="3rem").classes("text-slate-300")
                            ui.label("Không tìm thấy bài viết phù hợp").classes("text-lg font-bold text-slate-700")
                            ui.label("Thử đổi từ khóa, chủ đề hoặc sắp xếp.").classes("text-sm text-slate-400")
                    return
                for post in posts:
                    _render_post_card(post)

        def _open_detail_handler(post_id: int):
            async def handler(_event=None):
                await _open_post_detail(post_id)

            return handler

        def _render_post_card(post: Dict[str, Any]):
            topic_meta = COMMUNITY_TOPICS.get(_topic_key(post.get("incident_type")), COMMUNITY_TOPICS["qa"])
            thumb = _thumbnail_url(post)
            with ui.element("article").classes("feed-card w-full block").on(
                "click", _open_detail_handler(post["id"])
            ):
                with ui.row().classes("w-full gap-4 feed-card-body no-wrap p-4"):
                    with ui.column().classes("flex-1 min-w-0 gap-3"):
                        with ui.row().classes("items-start justify-between gap-3"):
                            with ui.row().classes("items-center gap-2 min-w-0"):
                                _render_user_avatar(post)
                                with ui.column().classes("gap-0 min-w-0"):
                                    ui.label(post.get("user_name", "Người dùng")).classes("text-sm font-black text-slate-800 truncate")
                                    ui.label(_format_time(post.get("created_at"))).classes("text-xs text-slate-400")
                            if post.get("is_closed"):
                                _render_resolved_badge()

                        with ui.row().classes("items-center gap-2 flex-wrap"):
                            _render_topic_badge(post.get("incident_type") or topic_meta["label"])

                        ui.label(post.get("title", "")).classes("post-title-modern")
                        ui.label(_excerpt(post.get("content"))).classes("post-excerpt")

                        with ui.row().classes("items-center gap-3 flex-wrap border-t border-slate-100 pt-3"):
                            _comment_stat(_post_metric(post, "comments"))

                    if thumb:
                        ui.image(_media_url(thumb)).classes("post-thumb shrink-0")

        def _comment_stat(count: int):
            with ui.element("span").classes("comment-pill"):
                ui.icon("mode_comment", size="1rem")
                ui.label(f"{count} bình luận")

        def _render_user_avatar(data: Dict[str, Any], size_class: str = "h-10 w-10"):
            avatar = _avatar_url(data)
            if avatar:
                ui.image(avatar).classes(f"{size_class} rounded-full object-cover border border-slate-200 shrink-0")
                return
            with ui.element("div").classes(f"{size_class} rounded-full bg-blue-50 flex items-center justify-center shrink-0"):
                ui.icon("account_circle").classes("text-blue-600")

        def _render_resolved_badge():
            with ui.element("span").classes("status-resolved-badge"):
                ui.icon("check_circle", size="0.9rem")
                ui.label("Đã giải quyết")

        def _render_topic_badge(label: str | None):
            with ui.element("span").classes(f"topic-badge {_topic_badge_classes(label)}"):
                meta = COMMUNITY_TOPICS.get(_topic_key(label), COMMUNITY_TOPICS["qa"])
                ui.icon(meta["icon"], size="0.9rem")
                ui.label(label or meta["label"])

        def _panel_heading(title: str, icon: str, heading_class: str, icon_class: str):
            with ui.element("div").classes(f"panel-heading {heading_class} w-full"):
                with ui.element("div").classes(f"panel-heading-icon {icon_class} shrink-0"):
                    ui.icon(icon, size="1.15rem")
                ui.label(title).classes("panel-title")

        def _render_sidebar():
            right_sidebar.clear()
            top_posts = sorted(
                state["posts"],
                key=lambda p: (_post_metric(p, "comments"), _safe_time(p.get("created_at"))),
                reverse=True,
            )[:4]
            active_members = {}
            for post in state["posts"]:
                name = post.get("user_name") or "Người dùng"
                active_members[name] = active_members.get(name, 0) + 1 + int(post.get("reply_count") or 0)
            member_rows = sorted(active_members.items(), key=lambda item: item[1], reverse=True)[:4]

            with right_sidebar:
                with ui.element("aside").classes("community-panel w-full"):
                    _panel_heading("Bài viết nổi bật", "local_fire_department", "panel-heading-blue", "panel-heading-icon-blue")
                    with ui.column().classes("w-full gap-2 mt-3"):
                        for index, post in enumerate(top_posts, start=1):
                            with ui.row().classes("rank-row w-full items-start gap-3 cursor-pointer").on(
                                "click", _open_detail_handler(post["id"])
                            ):
                                ui.label(str(index)).classes("rank-number shrink-0")
                                with ui.column().classes("gap-0 min-w-0 flex-1"):
                                    ui.label(post.get("title", "")).classes("text-sm font-bold text-slate-800 line-clamp-2")
                                    ui.label(f"{_post_metric(post, 'comments')} bình luận").classes("text-xs text-slate-400")

                with ui.element("aside").classes("community-panel w-full"):
                    _panel_heading("Thành viên tích cực", "groups", "panel-heading-emerald", "panel-heading-icon-emerald")
                    with ui.column().classes("w-full gap-2 mt-3"):
                        for name, score in member_rows:
                            with ui.row().classes("rank-row w-full items-center gap-3"):
                                with ui.element("div").classes("sidebar-avatar shrink-0"):
                                    ui.icon("person").classes("text-emerald-600")
                                with ui.column().classes("gap-0 min-w-0 flex-1"):
                                    ui.label(name).classes("text-sm font-bold text-slate-800 truncate")
                                    ui.label(f"{score} đóng góp").classes("text-xs text-slate-400")

                with ui.element("aside").classes("community-panel w-full"):
                    _panel_heading("Đơn vị cứu hộ được đánh giá cao", "workspace_premium", "panel-heading-amber", "panel-heading-icon-amber")
                    with ui.column().classes("w-full gap-2 mt-3"):
                        if not state["top_companies"]:
                            ui.label("Chưa có dữ liệu đánh giá.").classes("text-sm text-slate-400")
                        for company in state["top_companies"]:
                            with ui.row().classes("rank-row w-full items-center gap-3"):
                                with ui.element("div").classes("h-9 w-9 rounded-xl bg-amber-50 flex items-center justify-center"):
                                    ui.icon("star").classes("text-amber-500")
                                with ui.column().classes("gap-0 min-w-0 flex-1"):
                                    ui.label(company.get("company_name", "Đơn vị cứu hộ")).classes("text-sm font-bold text-slate-800 truncate")
                                    ui.label(
                                        f"{float(company.get('rating_avg') or 0):.1f} sao · {int(company.get('rating_count') or 0)} đánh giá"
                                    ).classes("text-xs text-slate-400")

                with ui.element("aside").classes("community-panel w-full"):
                    _panel_heading("Lưu ý khi đăng bài", "tips_and_updates", "panel-heading-slate", "panel-heading-icon-slate")
                    with ui.column().classes("w-full gap-2 mt-3"):
                        tips = [
                            ("Mô tả rõ hiện tượng", "Nêu loại xe, tình huống xảy ra và dấu hiệu bất thường."),
                            ("Thêm ảnh nếu có", "Ảnh lỗi, vị trí hoặc phụ tùng giúp cộng đồng hỗ trợ nhanh hơn."),
                            ("Chọn đúng chủ đề", "Hỏi đáp, kinh nghiệm, review hoặc cảnh báo để bài dễ tìm."),
                        ]
                        for icon, (title, body) in zip(["description", "photo_camera", "sell"], tips):
                            with ui.row().classes("posting-tip w-full items-start gap-3"):
                                with ui.element("div").classes("h-8 w-8 rounded-xl bg-blue-50 flex items-center justify-center shrink-0"):
                                    ui.icon(icon, size="1rem").classes("text-blue-600")
                                with ui.column().classes("gap-0 min-w-0"):
                                    ui.label(title).classes("text-sm font-bold text-slate-800")
                                    ui.label(body).classes("text-xs leading-snug text-slate-500")

        def _open_create_dialog():
            with ui.dialog() as dialog, ui.card().classes("dialog-card w-[620px] max-w-[94vw] max-h-[92vh] p-0 overflow-hidden"):
                with ui.column().classes("w-full max-h-[92vh] gap-0"):
                    with ui.row().classes("w-full items-center justify-between border-b border-slate-100 px-6 py-5"):
                        with ui.row().classes("items-center gap-3"):
                            with ui.element("div").classes("h-12 w-12 rounded-2xl bg-blue-50 flex items-center justify-center"):
                                ui.icon("edit_square", size="1.6rem").classes("text-blue-600")
                            with ui.column().classes("gap-0"):
                                ui.label("Tạo bài đăng mới").classes("text-2xl font-black text-slate-900")
                                ui.label("Chia sẻ vấn đề, kinh nghiệm hoặc cảnh báo cho cộng đồng.").classes("text-sm text-slate-500")
                        ui.button(icon="close", on_click=dialog.close).props("flat round dense")

                    with ui.column().classes("create-dialog-body w-full gap-4 px-6 py-5"):
                        title = ui.input("Tiêu đề").classes("w-full").props("outlined rounded clearable")
                        incident = ui.select(
                            options=POST_TOPIC_OPTIONS,
                            label="Chủ đề",
                            value="Hỏi đáp",
                        ).classes("w-full").props("outlined rounded")
                        uploaded_image = {"url": ""}
                        upload_status = ui.column().classes("w-full gap-2")
                        preview_container = ui.column().classes("w-full")

                        def render_image_preview(filename: str = ""):
                            preview_container.clear()
                            with preview_container:
                                if uploaded_image["url"]:
                                    with ui.element("div").classes("image-preview-box bg-white"):
                                        ui.image(_media_url(uploaded_image["url"])).classes("w-full")
                                    with ui.row().classes("w-full items-center justify-between rounded-2xl bg-emerald-50 p-3 border border-emerald-100"):
                                        with ui.column().classes("gap-0 min-w-0"):
                                            ui.label("Preview ảnh bài viết").classes("text-sm font-bold text-emerald-700")
                                            ui.label(filename or uploaded_image["url"]).classes("text-xs text-emerald-600 truncate")
                                        ui.button(
                                            icon="close",
                                            on_click=lambda: clear_image_preview(),
                                        ).props("flat round dense color=green")
                                else:
                                    with ui.element("div").classes("image-preview-box flex items-center justify-center"):
                                        with ui.column().classes("items-center gap-1 text-center p-5"):
                                            ui.icon("image", size="2rem").classes("text-slate-300")
                                            ui.label("Ảnh preview sẽ hiển thị ở đây sau khi tải lên").classes("text-sm font-bold text-slate-500")
                                            ui.label("Ảnh này sẽ được đính kèm vào bài đăng.").classes("text-xs text-slate-400")

                        def clear_image_preview():
                            uploaded_image["url"] = ""
                            upload_status.clear()
                            render_image_preview()
                            try:
                                post_uploader.reset()
                            except Exception:
                                pass

                        render_image_preview()

                        def handle_post_image_begin():
                            upload_status.clear()
                            with upload_status:
                                with ui.row().classes("items-center gap-2 rounded-2xl bg-blue-50 px-3 py-2 border border-blue-100"):
                                    ui.spinner(size="sm").classes("text-blue-600")
                                    ui.label("Đang tải ảnh lên...").classes("text-xs font-bold text-blue-700")

                        def handle_post_image_rejected():
                            upload_status.clear()
                            with upload_status:
                                ui.label("Ảnh không hợp lệ hoặc vượt quá 5MB.").classes(
                                    "text-xs font-bold text-red-600"
                                )

                        async def handle_post_image_upload(event):
                            upload_status.clear()
                            try:
                                filename, content_bytes, content_type = await _read_upload_content(event)
                                image_url = await upload_community_image(filename, content_bytes, content_type)
                                if not image_url:
                                    return
                                uploaded_image["url"] = image_url
                                render_image_preview(filename)
                                with upload_status:
                                    ui.label("Đã tải ảnh lên thành công").classes("text-xs font-bold text-emerald-600")
                                post_uploader.reset()
                            except Exception as exc:
                                ui.notify(f"Lỗi tải ảnh: {exc}", type="negative")
                                with upload_status:
                                    ui.label("Không thể tải ảnh lên. Vui lòng thử lại.").classes(
                                        "text-xs font-bold text-red-600"
                                    )

                        post_uploader = ui.upload(
                            on_begin_upload=handle_post_image_begin,
                            on_upload=handle_post_image_upload,
                            on_rejected=handle_post_image_rejected,
                            auto_upload=True,
                            max_file_size=5 * 1024 * 1024,
                        ).props("accept=image/* label='Tải ảnh bài viết'").classes("community-uploader w-full")
                        content = ui.textarea("Nội dung").classes("w-full").props("outlined rounded rows=7")

                    with ui.row().classes("w-full justify-end gap-3 border-t border-slate-100 px-6 py-4"):
                        ui.button("Đóng", on_click=dialog.close).props("flat no-caps").classes("rounded-xl font-bold")

                        async def submit():
                            if not (title.value or "").strip() or not (content.value or "").strip():
                                ui.notify("Vui lòng nhập tiêu đề và nội dung", type="warning")
                                return
                            data = await create_post(
                                (title.value or "").strip(),
                                (content.value or "").strip(),
                                incident.value,
                                uploaded_image["url"],
                            )
                            if data:
                                ui.notify("Đã đăng bài thành công", type="positive")
                                dialog.close()
                                await refresh_posts()
                            else:
                                ui.notify("Không thể đăng bài", type="negative")

                        ui.button("Đăng bài", icon="send", on_click=submit).props("unelevated no-caps").classes(
                            "rounded-xl bg-blue-600 px-6 font-black text-white"
                        )

            dialog.open()

        def _confirm_delete_post(post_id: int, detail_dialog):
            with ui.dialog() as confirm_dialog, ui.card().classes("w-[420px] max-w-[92vw] rounded-3xl p-6"):
                with ui.column().classes("w-full gap-4"):
                    with ui.row().classes("items-center gap-3"):
                        with ui.element("div").classes("h-12 w-12 rounded-2xl bg-red-50 flex items-center justify-center"):
                            ui.icon("delete", size="1.5rem").classes("text-red-600")
                        with ui.column().classes("gap-0"):
                            ui.label("Xoá bài đăng?").classes("text-xl font-black text-slate-900")
                            ui.label("Bài đăng và toàn bộ bình luận sẽ bị xoá.").classes("text-sm text-slate-500")

                    with ui.row().classes("w-full justify-end gap-3 pt-2"):
                        ui.button("Huỷ", on_click=confirm_dialog.close).props("flat no-caps").classes("rounded-xl font-bold")

                        async def do_delete():
                            delete_btn.props("loading")
                            if await delete_post(post_id):
                                ui.notify("Đã xoá bài đăng", type="positive")
                                confirm_dialog.close()
                                detail_dialog.close()
                                await refresh_posts()
                            else:
                                ui.notify("Không thể xoá bài đăng", type="negative")
                                delete_btn.props(remove="loading")

                        delete_btn = ui.button(
                            "Xoá",
                            icon="delete",
                            on_click=do_delete,
                        ).props("unelevated no-caps").classes("rounded-xl bg-red-600 px-5 font-bold text-white")

            confirm_dialog.open()

        async def _open_post_detail(post_id: int):
            post = await get_post_detail(post_id)
            if not post:
                ui.notify("Không tìm thấy bài đăng", type="negative")
                return

            is_owner = post.get("user_id") == current_user_id
            thumb = _thumbnail_url(post)

            with ui.dialog() as dialog, ui.card().classes(
                "dialog-card w-[860px] max-w-[95vw] h-[88vh] p-0 overflow-hidden"
            ):
                with ui.column().classes("w-full h-full"):
                    with ui.column().classes("w-full flex-1 post-detail-scroll px-8 pt-8 pb-6"):
                        with ui.row().classes("w-full justify-between items-center mb-5"):
                            with ui.row().classes("items-center gap-2"):
                                ui.button(icon="arrow_back", on_click=dialog.close).props("flat round color=primary")
                                _render_topic_badge(post.get("incident_type") or "Thảo luận")
                                closed_badge_area = ui.row().classes("items-center gap-2")
                                with closed_badge_area:
                                    if post.get("is_closed"):
                                        _render_resolved_badge()

                            if is_owner:
                                with ui.row().classes("items-center gap-2"):
                                    if not post.get("is_closed"):
                                        close_btn = ui.button(
                                            "Đánh dấu đã giải quyết",
                                            icon="check_circle",
                                        ).classes("rounded-xl bg-green-600 px-4 font-bold text-white").props("unelevated no-caps")

                                        async def mark_closed(btn=close_btn):
                                            btn.props("loading")
                                            if await close_post(post_id):
                                                ui.notify("Đã đánh dấu bài viết là đã giải quyết", type="positive")
                                                btn.delete()
                                                with closed_badge_area:
                                                    _render_resolved_badge()
                                                await refresh_posts()
                                            else:
                                                ui.notify("Không thể đánh dấu bài viết", type="negative")
                                                btn.props(remove="loading")

                                        close_btn.on("click", mark_closed)

                                    ui.button(
                                        "Xoá bài",
                                        icon="delete",
                                        on_click=lambda: _confirm_delete_post(post_id, dialog),
                                    ).classes("rounded-xl px-4 font-bold text-red-600 bg-red-50 hover:bg-red-100").props("flat no-caps")

                        ui.label(post.get("title", "")).classes("text-3xl font-black text-slate-900 mb-4")

                        with ui.row().classes("items-center gap-3 mb-5"):
                            _render_user_avatar(post)
                            with ui.column().classes("gap-0"):
                                ui.label(post.get("user_name", "Người dùng")).classes("font-bold text-slate-800")
                                ui.label(_format_time(post.get("created_at"))).classes("text-xs text-slate-400")

                        if thumb:
                            with ui.element("div").classes("post-detail-image mb-5"):
                                ui.element("img").props(f'src="{_media_url(thumb)}" alt="Ảnh bài viết"').classes("post-detail-photo")

                        ui.label(post.get("content", "")).classes(
                            "text-base text-slate-700 leading-relaxed mb-8 whitespace-pre-wrap"
                        )

                        ui.separator().classes("mb-6")
                        with ui.row().classes("items-center gap-2 mb-4"):
                            ui.icon("mode_comment").classes("text-blue-600")
                            comment_count_label = ui.label(f"Bình luận ({len(post.get('replies') or [])})").classes("text-xl font-black text-slate-900")

                        replies_container = ui.column().classes("w-full gap-3")
                        empty_reply_label = None
                        with replies_container:
                            if not post.get("replies"):
                                empty_reply_label = ui.label("Chưa có bình luận nào.").classes("text-sm text-slate-400 italic")
                            for reply in post.get("replies") or []:
                                _render_reply(reply)

                    with ui.row().classes("w-full gap-3 items-center px-8 py-5 comment-box"):
                        reply_input = ui.input(placeholder="Viết bình luận...").classes("flex-1").props("outlined rounded dense")

                        async def send_reply():
                            nonlocal empty_reply_label
                            content = (reply_input.value or "").strip()
                            if not content:
                                ui.notify("Vui lòng nhập bình luận", type="warning")
                                return
                            send_btn.props("loading")
                            response = await create_reply(post_id, content)
                            if response:
                                ui.notify("Đã gửi bình luận", type="positive")
                                reply_input.value = ""
                                reply_input.update()
                                if empty_reply_label:
                                    empty_reply_label.delete()
                                    empty_reply_label = None
                                post.setdefault("replies", []).append(response)
                                comment_count_label.set_text(f"Bình luận ({len(post['replies'])})")
                                with replies_container:
                                    _render_reply({
                                        "id": response.get("id"),
                                        "user_name": response.get("user_name") or "Bạn",
                                        "user_avatar_url": response.get("user_avatar_url"),
                                        "content": response.get("content") or content,
                                        "created_at": response.get("created_at"),
                                    })
                                for item in state["posts"]:
                                    if item.get("id") == post_id:
                                        item["reply_count"] = int(item.get("reply_count") or 0) + 1
                                        break
                            else:
                                ui.notify("Không thể gửi bình luận", type="negative")
                            send_btn.props(remove="loading")

                        send_btn = ui.button(icon="send", on_click=send_reply).props("round unelevated color=primary")

            dialog.open()

        def _render_reply(reply: Dict[str, Any]):
            with ui.element("div").classes("reply-card"):
                with ui.row().classes("w-full justify-between gap-3"):
                    with ui.row().classes("items-center gap-2 min-w-0"):
                        _render_user_avatar(reply, "h-8 w-8")
                        ui.label(reply.get("user_name") or "Bạn").classes("font-bold text-sm text-blue-700 truncate")
                    ui.label(_format_time(reply.get("created_at")) if reply.get("created_at") else "Vừa xong").classes("text-xs text-slate-400")
                ui.label(reply.get("content", "")).classes("mt-2 text-sm text-slate-700")
                action_row = ui.row().classes("w-full justify-between items-center mt-3")
                with action_row:
                    if reply.get("is_helpful"):
                        with ui.element("div").classes("helpful-done"):
                            ui.icon("verified", size="xs")
                            ui.label("Hữu ích")
                    elif reply.get("id"):
                        helpful_btn = ui.button("Đánh dấu hữu ích", icon="thumb_up").props("flat dense no-caps").classes(
                            "rounded-xl font-bold text-blue-700"
                        )

                        async def mark_helpful_action(reply_id=reply["id"], btn=helpful_btn):
                            btn.props("loading")
                            if await mark_reply_helpful(reply_id):
                                ui.notify("Đã đánh dấu phản hồi hữu ích", type="positive")
                                btn.delete()
                                with action_row:
                                    with ui.element("div").classes("helpful-done"):
                                        ui.icon("verified", size="xs")
                                        ui.label("Hữu ích")
                            else:
                                ui.notify("Không thể đánh dấu phản hồi", type="negative")
                                btn.props(remove="loading")

                        helpful_btn.on("click", mark_helpful_action)

        async def refresh_posts():
            state["posts"] = await get_posts()
            state["top_companies"] = await _get_top_companies()
            _render_topic_tabs()
            _render_feed()
            _render_sidebar()

        await refresh_posts()
