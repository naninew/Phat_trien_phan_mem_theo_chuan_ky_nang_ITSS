import asyncio
import json

from nicegui import app, ui
from core.auth import is_authenticated, get_access_token, get_user_name, logout_user, get_user_role
from core.config import APP_TITLE, BACKEND_URL, LOGIN_PAGE
from services.notification_api import get_notifications, mark_all_notifications_read, mark_notification_read

try:
    import websockets
    _HAS_WEBSOCKETS = True
except ImportError:
    _HAS_WEBSOCKETS = False

def create_navbar():
    """Create a modern Material Design 3 navbar."""
    _inject_theme_styles()
    _apply_saved_theme()

    with ui.header().classes('glass-panel px-6 py-2 flex items-center justify-between fixed h-16 top-0 w-full z-50'):
        # Left side: Logo
        with ui.row().classes('items-center gap-3 cursor-pointer h-full').on('click', lambda: ui.navigate.to('/')):
            ui.icon('local_taxi', size='1.8rem').classes('text-blue-600')
            ui.label(APP_TITLE).classes('text-xl text-slate-800 font-extrabold font-outfit tracking-tight hide-on-mobile')

        # Right side: Auth/User Actions
        with ui.row().classes('items-center gap-3 h-full'):
            if is_authenticated():
                _theme_toggle_button()

                # Notifications
                _notification_button()
                
                # User Profile Dropdown
                with ui.button().props('flat').classes('px-2 py-1 text-on-surface font-semibold !text-white'):
                    with ui.row().classes("items-center gap-2"):
                        ui.avatar(icon="account_circle", size="md").classes("bg-white/20 text-white")
                        ui.label(get_user_name()).classes("font-bold hide-on-mobile")
                    with ui.menu() as menu:
                        ui.menu_item('Hồ sơ cá nhân', on_click=lambda: ui.navigate.to('/profile'))
                        ui.menu_item('Cài đặt', on_click=_open_settings_dialog)
                        ui.separator()
                        ui.menu_item('Đăng xuất', on_click=logout_user).classes('text-red-500 hover:bg-red-50')
            else:
                ui.button('Đăng Nhập', on_click=lambda: ui.navigate.to(LOGIN_PAGE)).props('flat').classes('text-primary font-semibold')
                ui.button('Đăng Ký', on_click=lambda: ui.navigate.to('/register')).classes('btn-primary px-4')


def _get_ui_settings():
    return app.storage.user.setdefault("ui_settings", {"language": "vi", "theme": "light"})


def _inject_theme_styles():
    ui.add_head_html("""
    <style>
        body.body--dark,
        .body--dark {
            --surface: #0f172a;
            --on-surface: #e5eefb;
            --surface-variant: #1e293b;
            --on-surface-variant: #94a3b8;
            --glass: rgba(30, 41, 59, 0.92);
            --glass-border: rgba(148, 163, 184, 0.2);
            background: #0b1120 !important;
            color: #e5eefb !important;
        }

        body.body--dark .bg-surface,
        body.body--dark .q-page,
        body.body--dark .nicegui-content {
            background: #0b1120 !important;
            color: #e5eefb !important;
        }

        body.body--dark .q-card,
        body.body--dark .modern-card,
        body.body--dark .m3-card {
            background: #111827 !important;
            border-color: #263449 !important;
            color: #e5eefb !important;
        }

        body.body--dark .text-slate-900,
        body.body--dark .text-gray-900,
        body.body--dark .text-on-surface {
            color: #f8fafc !important;
        }

        body.body--dark .text-slate-800,
        body.body--dark .text-gray-700 {
            color: #dbeafe !important;
        }

        body.body--dark .text-slate-700,
        body.body--dark .text-slate-600,
        body.body--dark .text-slate-500,
        body.body--dark .text-gray-500,
        body.body--dark .text-on-surface-variant {
            color: #94a3b8 !important;
        }

        body.body--dark .bg-white,
        body.body--dark .bg-slate-50 {
            background: #111827 !important;
        }

        body.body--dark .border-slate-100,
        body.body--dark .border-slate-200,
        body.body--dark .border-surface-variant {
            border-color: #263449 !important;
        }

        body.body--dark .q-field__control {
            background: #0f172a !important;
            color: #e5eefb !important;
        }
    </style>
    """)


def _set_theme(theme: str):
    if theme == "dark":
        ui.dark_mode().enable()
        ui.run_javascript("document.body.classList.add('body--dark')")
    elif theme == "light":
        ui.dark_mode().disable()
        ui.run_javascript("document.body.classList.remove('body--dark')")
    else:
        ui.run_javascript("""
            const dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.body.classList.toggle('body--dark', dark);
        """)


def _apply_saved_theme():
    _set_theme(_get_ui_settings().get("theme", "light"))


def _theme_toggle_button():
    settings = _get_ui_settings()
    state = {"theme": settings.get("theme", "light")}

    def _toggle_theme():
        state["theme"] = "dark" if state["theme"] != "dark" else "light"
        settings["theme"] = state["theme"]
        app.storage.user["ui_settings"] = settings
        _set_theme(state["theme"])
        theme_btn.props(f"icon={'dark_mode' if state['theme'] == 'light' else 'light_mode'}")
        theme_btn.tooltip("Chuyển sang chế độ tối" if state["theme"] == "light" else "Chuyển sang chế độ sáng")

    with ui.button(
        icon="dark_mode" if state["theme"] == "light" else "light_mode",
        on_click=_toggle_theme,
    ).props("flat round").classes("text-white") as theme_btn:
        theme_btn.tooltip("Chuyển sang chế độ tối" if state["theme"] == "light" else "Chuyển sang chế độ sáng")


def _notification_button():
    notifications_state = {"items": [], "ws_task": None}

    def _notification_ws_url(token: str) -> str:
        base = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://")
        return f"{base}/ws/notifications?token={token}"

    def _format_time(value):
        if not value:
            return ""
        try:
            from datetime import datetime
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%H:%M • %d/%m")
        except Exception:
            return value

    async def _open_request(notification):
        if not notification.get("is_read"):
            await mark_notification_read(notification["id"])
        request_id = notification.get("request_id")
        if request_id:
            role = get_user_role()
            if role == "customer":
                ui.navigate.to(f"/customer/track/{request_id}")
            elif role == "company_staff":
                ui.navigate.to("/company/queue")
            else:
                ui.navigate.to("/admin/dashboard")
        await _load_notifications()

    async def _mark_read(notification):
        if await mark_notification_read(notification["id"]):
            notification["is_read"] = True
            _render_notifications()

    async def _mark_all_read():
        if await mark_all_notifications_read():
            for item in notifications_state["items"]:
                item["is_read"] = True
            _render_notifications()

    async def _load_notifications():
        try:
            notifications_state["items"] = await get_notifications()
            _render_notifications()
        except Exception:
            notifications_state["items"] = []
            _render_notifications(error=True)

    def _upsert_notification(notification):
        items = notifications_state["items"]
        existing_index = next(
            (index for index, item in enumerate(items) if item.get("id") == notification.get("id")),
            None,
        )
        if existing_index is None:
            notifications_state["items"] = [notification, *items]
        else:
            items[existing_index] = notification
        _render_notifications()

    async def _connect_notifications_ws():
        if not _HAS_WEBSOCKETS:
            return
        token = get_access_token()
        if not token:
            return

        while get_access_token():
            try:
                async with websockets.connect(
                    _notification_ws_url(token),
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5,
                ) as ws:
                    async for raw in ws:
                        try:
                            payload = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        if payload.get("type") == "notification":
                            notification = payload.get("notification")
                            if notification:
                                _upsert_notification(notification)
                                ui.notify(notification.get("title", "Bạn có thông báo mới"), type="info")
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)

    def _render_notifications(error=False):
        unread_count = sum(1 for n in notifications_state["items"] if not n.get("is_read"))
        badge.set_text("99+" if unread_count > 99 else str(unread_count))
        badge.set_visibility(unread_count > 0)
        menu_container.clear()

        with menu_container:
            if error:
                with ui.column().classes("items-center gap-2 py-8"):
                    ui.icon("error_outline", size="2rem").classes("text-red-500")
                    ui.label("Không thể tải thông báo").classes("font-bold text-slate-700")
                return

            if not notifications_state["items"]:
                with ui.column().classes("items-center gap-2 py-8"):
                    ui.icon("notifications_none", size="2.5rem").classes("text-slate-300")
                    ui.label("Chưa có thông báo").classes("font-bold text-slate-700")
                    ui.label("Các cập nhật về yêu cầu cứu hộ sẽ xuất hiện tại đây.").classes(
                        "text-xs text-slate-400 text-center"
                    )
                return

            for n in notifications_state["items"][:8]:
                row_classes = (
                    "w-full cursor-pointer rounded-xl px-3 py-3 transition-all hover:bg-blue-50 "
                    + ("bg-blue-50/70" if not n.get("is_read") else "bg-white")
                )
                with ui.row().classes(row_classes).on("click", lambda n=n: asyncio.ensure_future(_open_request(n))):
                    with ui.element("div").classes(
                        "h-9 w-9 shrink-0 rounded-xl bg-blue-50 flex items-center justify-center"
                    ):
                        ui.icon("notifications", size="1.15rem").classes(
                            "text-blue-600" if not n.get("is_read") else "text-slate-400"
                        )
                    with ui.column().classes("flex-1 min-w-0 gap-0"):
                        with ui.row().classes("w-full items-center justify-between gap-2"):
                            ui.label(n.get("title", "Thông báo")).classes(
                                "text-sm font-bold text-slate-800 truncate"
                            )
                            if not n.get("is_read"):
                                ui.element("div").classes("h-2 w-2 rounded-full bg-blue-600 shrink-0")
                        ui.label(n.get("content", "")).classes(
                            "text-xs text-slate-500 leading-snug line-clamp-2"
                        )
                        ui.label(_format_time(n.get("sent_time"))).classes("text-[11px] text-slate-400 mt-1")
                    if not n.get("is_read"):
                        ui.button(
                            icon="done",
                            on_click=lambda n=n: asyncio.ensure_future(_mark_read(n)),
                        ).props("flat round dense").classes("text-emerald-600")

    with ui.element("div").classes("relative"):
        with ui.button(icon='notifications').props('flat round').classes('text-on-surface-variant text-white'):
            with ui.menu().classes("w-[360px] max-w-[calc(100vw-24px)] rounded-2xl p-0 shadow-xl"):
                with ui.column().classes("w-full gap-0"):
                    with ui.row().classes("w-full items-center justify-between border-b border-slate-100 px-4 py-3"):
                        with ui.column().classes("gap-0"):
                            ui.label("Thông báo").classes("text-lg font-bold text-slate-900")
                            ui.label("Cập nhật mới nhất của bạn").classes("text-xs text-slate-400")
                        with ui.row().classes("items-center gap-1"):
                            ui.button(
                                "Đọc tất cả",
                                icon="done_all",
                                on_click=lambda: asyncio.ensure_future(_mark_all_read()),
                            ).props("flat dense").classes("text-xs font-bold text-blue-700")
                            ui.button(icon="refresh", on_click=lambda: asyncio.ensure_future(_load_notifications())).props("flat round dense")
                    menu_container = ui.column().classes("w-full gap-1 p-2 max-h-[420px] overflow-y-auto")
        badge = ui.badge("0").classes(
            "absolute -right-2 -top-2 z-[60] flex h-5 min-w-5 items-center justify-center "
            "rounded-full border-2 border-white px-1 text-[11px] font-black "
            "leading-none shadow-lg"
        ).style(
            "background-color:#dc2626 !important;"
            "color:#ffffff !important;"
            "line-height:1;"
        )
        badge.set_visibility(False)

    ui.timer(0.2, _load_notifications, once=True)
    ui.timer(30, _load_notifications)

    notifications_state["ws_task"] = asyncio.create_task(_connect_notifications_ws())

    def cleanup():
        task = notifications_state.get("ws_task")
        if task and not task.done():
            task.cancel()

    ui.context.client.on_disconnect(cleanup)


def _open_settings_dialog():
    role_labels = {
        "customer": "Khách hàng",
        "company_staff": "Đơn vị cứu hộ",
        "admin": "Quản trị viên",
    }
    role = get_user_role()
    user_settings = _get_ui_settings()
    selected_language = user_settings.get("language", "vi")
    selected_theme = user_settings.get("theme", "light")

    language_options = {
        "vi": "Tiếng Việt",
        "en": "English",
    }
    theme_options = {
        "light": "Chế độ sáng",
        "dark": "Chế độ tối",
        "system": "Theo hệ thống",
    }

    def _save_setting(key: str, value: str):
        user_settings[key] = value
        app.storage.user["ui_settings"] = user_settings
        if key == "theme":
            _set_theme(value)
        ui.notify("Đã cập nhật cài đặt hiển thị", type="positive")

    with ui.dialog() as dialog, ui.card().classes("w-[520px] max-w-full rounded-3xl p-0 shadow-xl"):
        with ui.column().classes("w-full gap-0"):
            with ui.row().classes("w-full items-center justify-between border-b border-slate-100 px-6 py-5"):
                with ui.row().classes("items-center gap-3"):
                    with ui.element("div").classes(
                        "h-11 w-11 rounded-2xl bg-blue-50 flex items-center justify-center"
                    ):
                        ui.icon("settings", size="1.45rem").classes("text-blue-600")
                    with ui.column().classes("gap-0"):
                        ui.label("Cài đặt").classes("text-xl font-bold text-slate-900")
                        ui.label("Tùy chỉnh trải nghiệm sử dụng hệ thống").classes("text-xs text-slate-400")
                ui.button(icon="close", on_click=dialog.close).props("flat round dense")

            with ui.column().classes("w-full gap-4 px-6 py-5"):
                with ui.row().classes("w-full items-center gap-3 rounded-2xl bg-slate-50 p-4"):
                    ui.avatar(icon="account_circle").classes("bg-blue-100 text-blue-700")
                    with ui.column().classes("gap-0 flex-1"):
                        ui.label(get_user_name()).classes("font-bold text-slate-900")
                        ui.label(role_labels.get(role, "Người dùng")).classes("text-sm text-slate-500")
                    ui.button(
                        "Hồ sơ",
                        icon="person",
                        on_click=lambda: ui.navigate.to('/profile'),
                    ).classes("rounded-xl text-blue-700 font-bold").props("flat")

                with ui.column().classes("w-full gap-3"):
                    ui.label("Tùy chọn nhanh").classes("text-sm font-bold uppercase text-slate-400")
                    with ui.row().classes("w-full items-center justify-between rounded-2xl border border-slate-100 px-4 py-3"):
                        with ui.row().classes("items-center gap-3"):
                            ui.icon("notifications_active").classes("text-blue-600")
                            with ui.column().classes("gap-0"):
                                ui.label("Thông báo realtime").classes("font-bold text-slate-800")
                                ui.label("Nhận cập nhật khi yêu cầu thay đổi").classes("text-xs text-slate-400")
                        ui.switch(value=True).props("color=primary")

                    with ui.row().classes("w-full items-center gap-3 rounded-2xl border border-slate-100 px-4 py-3"):
                        with ui.row().classes("items-center gap-3"):
                            ui.icon("language").classes("text-blue-600")
                            with ui.column().classes("gap-0"):
                                ui.label("Ngôn ngữ").classes("font-bold text-slate-800")
                                ui.label("Language / Ngôn ngữ").classes("text-xs text-slate-400")
                        ui.select(
                            options=language_options,
                            value=selected_language,
                            on_change=lambda e: _save_setting("language", e.value),
                        ).props("outlined dense rounded").classes("ml-auto w-40")

                    with ui.row().classes("w-full items-center gap-3 rounded-2xl border border-slate-100 px-4 py-3"):
                        with ui.row().classes("items-center gap-3"):
                            ui.icon("palette").classes("text-blue-600")
                            with ui.column().classes("gap-0"):
                                ui.label("Giao diện").classes("font-bold text-slate-800")
                                ui.label("Sáng, tối hoặc theo hệ thống").classes("text-xs text-slate-400")
                        ui.select(
                            options=theme_options,
                            value=selected_theme,
                            on_change=lambda e: _save_setting("theme", e.value),
                        ).props("outlined dense rounded").classes("ml-auto w-44")

            with ui.row().classes("w-full justify-end gap-3 border-t border-slate-100 px-6 py-4"):
                ui.button("Đóng", on_click=dialog.close).props("flat").classes("rounded-xl font-bold")
                ui.button(
                    "Cập nhật hồ sơ",
                    icon="edit",
                    on_click=lambda: ui.navigate.to('/profile'),
                ).classes("rounded-xl bg-blue-600 px-5 font-bold text-white")

    dialog.open()
