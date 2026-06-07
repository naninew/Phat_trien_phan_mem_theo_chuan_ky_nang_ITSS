"""
Modern company detail dialog for customer-facing rescue company profiles.
"""

from collections import Counter
from datetime import datetime
import traceback

import httpx
from nicegui import ui

from core.auth import get_access_token
from core.config import BACKEND_URL


SERVICE_ITEMS = [
    ("Kéo xe ô tô", "local_shipping", "Xe cẩu, xe sàn trượt"),
    ("Kéo xe máy", "two_wheeler", "Vận chuyển xe máy"),
    ("Kích bình", "battery_charging_full", "Hỗ trợ ắc quy"),
    ("Thay lốp", "tire_repair", "Vá và thay lốp"),
    ("Tiếp nhiên liệu", "local_gas_station", "Xăng dầu khẩn cấp"),
]

GALLERY_ITEMS = [
    ("Đội xe cứu hộ", "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=900&q=80"),
    ("Kỹ thuật tại hiện trường", "https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?auto=format&fit=crop&w=900&q=80"),
    ("Trung tâm điều phối", "https://images.unsplash.com/photo-1530046339160-ce3e530c7d2f?auto=format&fit=crop&w=900&q=80"),
    ("Dịch vụ đường dài", "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=900&q=80"),
]

DEFAULT_COVER_IMAGE = "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=1800&q=85"


def open_company_detail(company_id: int):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {"info": {}, "reviews": [], "history": []}

    def _safe_rating(value) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def _stars(rating: float) -> str:
        rounded = int(round(_safe_rating(rating)))
        return "★" * max(0, min(5, rounded)) + "☆" * max(0, 5 - rounded)

    def _format_date(value: str) -> str:
        if not value:
            return "--"
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d/%m/%Y")
        except ValueError:
            return value[:10]

    def _initials(name: str) -> str:
        words = [part for part in (name or "Khách hàng").split() if part]
        return "".join(word[0].upper() for word in words[:2]) or "KH"

    def _company_images(info: dict) -> list[str]:
        candidates = (
            info.get("images")
            or info.get("gallery")
            or info.get("photos")
            or info.get("company_images")
            or []
        )
        if isinstance(candidates, str):
            return [candidates]
        if isinstance(candidates, list):
            result = []
            for item in candidates:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict):
                    url = item.get("url") or item.get("image_url") or item.get("src")
                    if url:
                        result.append(url)
            return result
        return []

    def _cover_image(info: dict) -> str:
        images = _company_images(info)
        return images[0] if images else DEFAULT_COVER_IMAGE

    def _completed_count() -> int:
        return sum(1 for item in data["history"] if item.get("status") == "COMPLETED")

    def _eta_minutes(info: dict) -> int:
        radius = info.get("service_radius_km") or 50
        try:
            return max(12, min(45, round(float(radius) * 0.7)))
        except (TypeError, ValueError):
            return 25

    def _rating_distribution() -> Counter:
        counter = Counter()
        for review in data["reviews"]:
            try:
                rating = int(review.get("rating") or 0)
            except (TypeError, ValueError):
                rating = 0
            if 1 <= rating <= 5:
                counter[rating] += 1
        return counter

    async def _load_details():
        try:
            loading_bar.visible = True
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BACKEND_URL}/rescue/companies/{company_id}/full-details",
                    headers=headers,
                    timeout=10,
                )
                if response.status_code != 200:
                    raise RuntimeError(f"API ERROR: {response.status_code}")

                payload = response.json().get("data", {})
                data["info"] = payload
                data["reviews"] = payload.get("reviews", [])
                data["history"] = payload.get("my_history", [])
                _render_ui()
        except Exception as exc:
            print("\n========== DETAIL ERROR ==========")
            traceback.print_exc()
            print("==================================\n")
            ui.notify(f"Lỗi tải chi tiết: {exc}", type="negative")
            dialog.close()
        finally:
            loading_bar.visible = False

    def _kpi_card(label: str, value: str, icon: str, accent: str):
        with ui.card().classes("flex-1 min-w-[150px] rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"):
            with ui.row().classes("w-full items-center justify-between gap-3"):
                with ui.column().classes("gap-0"):
                    ui.label(label).classes("text-[11px] font-bold uppercase text-slate-400")
                    ui.label(value).classes("text-xl font-black text-slate-900")
                with ui.element("div").classes(f"h-11 w-11 rounded-2xl {accent} flex items-center justify-center"):
                    ui.icon(icon, size="1.25rem")

    def _service_chip(title: str, icon: str, subtitle: str):
        with ui.card().classes("min-w-[170px] flex-1 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"):
            with ui.row().classes("items-center gap-3"):
                with ui.element("div").classes("h-11 w-11 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center"):
                    ui.icon(icon, size="1.35rem")
                with ui.column().classes("gap-0 min-w-0"):
                    ui.label(title).classes("text-sm font-black text-slate-900")
                    ui.label(subtitle).classes("text-xs text-slate-500")

    def _review_card(review: dict):
        name = review.get("customer_name") or "Khách hàng"
        rating = _safe_rating(review.get("rating"))
        with ui.card().classes("w-full rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"):
            with ui.row().classes("w-full items-start gap-3"):
                with ui.element("div").classes("h-11 w-11 shrink-0 rounded-full bg-blue-50 text-blue-700 flex items-center justify-center"):
                    ui.label(_initials(name)).classes("text-sm font-black")
                with ui.column().classes("flex-1 gap-2 min-w-0"):
                    with ui.row().classes("w-full items-start justify-between gap-3"):
                        with ui.column().classes("gap-0"):
                            ui.label(name).classes("text-sm font-black text-slate-900")
                            ui.label(_format_date(review.get("created_at", ""))).classes("text-xs text-slate-400")
                        ui.label(_stars(rating)).classes("text-sm tracking-wide text-amber-500")
                    ui.label(review.get("comment") or "Khách hàng chưa để lại nhận xét.").classes(
                        "text-sm leading-relaxed text-slate-600"
                    )

    def _rating_chart():
        reviews = data["reviews"]
        total = max(1, len(reviews))
        distribution = _rating_distribution()
        with ui.card().classes("w-full rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"):
            ui.label("Phân bố đánh giá").classes("text-base font-black text-slate-900")
            with ui.column().classes("w-full gap-2 mt-3"):
                for star in range(5, 0, -1):
                    count = distribution.get(star, 0)
                    percent = (count / total) * 100 if reviews else 0
                    with ui.row().classes("w-full items-center gap-3"):
                        ui.label(f"{star} sao").classes("w-12 text-xs font-bold text-slate-500")
                        with ui.element("div").classes("h-2 flex-1 overflow-hidden rounded-full bg-slate-100"):
                            ui.element("div").classes("h-full rounded-full bg-amber-400").style(f"width: {percent:.1f}%")
                        ui.label(str(count)).classes("w-7 text-right text-xs font-bold text-slate-500")

    def _gallery():
        company_images = _company_images(data["info"])
        gallery_items = (
            [(f"Ảnh doanh nghiệp {index + 1}", image_url) for index, image_url in enumerate(company_images)]
            or GALLERY_ITEMS
        )
        with ui.card().classes("w-full rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"):
            ui.label("Hình ảnh doanh nghiệp").classes("text-base font-black text-slate-900")
            with ui.row().classes("w-full gap-3 mt-3"):
                for title, image_url in gallery_items[:4]:
                    with ui.element("div").classes(
                        "relative min-h-[120px] flex-1 min-w-[180px] overflow-hidden rounded-2xl bg-slate-100"
                    ):
                        ui.image(image_url).classes("h-full w-full object-cover")
                        with ui.element("div").classes("absolute inset-x-0 bottom-0 bg-black/45 px-3 py-2"):
                            ui.label(title).classes("text-xs font-bold text-white")

    def _render_ui():
        try:
            info_container.clear()
            info = data["info"]
            rating_avg = _safe_rating(info.get("rating_avg"))
            rating_count = int(info.get("rating_count") or len(data["reviews"]) or 0)
            hotline = info.get("hotline") or ""
            eta = _eta_minutes(info)
            status = (info.get("status") or "active").lower()
            is_active = status in ("active", "verified", "online", "available")

            with info_container:
                with ui.scroll_area().classes("w-full h-[88vh] bg-slate-50"):
                    with ui.column().classes("w-full gap-0"):
                        with ui.element("div").classes("w-full bg-white p-3 md:p-4"):
                            with ui.element("div").classes(
                                "relative h-[320px] w-full overflow-hidden rounded-[28px] bg-slate-900 shadow-xl md:h-[360px]"
                            ):
                                ui.image(_cover_image(info)).classes("absolute inset-0 h-full w-full object-cover")
                                ui.element("div").classes(
                                    "absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-black/15"
                                )
                                ui.button(icon="close", on_click=dialog.close).props("round flat").classes(
                                    "absolute right-4 top-4 z-10 bg-white/90 text-slate-700 shadow-sm"
                                )

                                with ui.column().classes(
                                    "absolute inset-x-0 bottom-0 gap-4 p-5 text-white md:p-7"
                                ):
                                    with ui.row().classes("w-full items-end justify-between gap-5 flex-wrap"):
                                        with ui.row().classes("items-end gap-4 min-w-0"):
                                            with ui.column().classes("gap-2 min-w-0 pb-1"):
                                                ui.label(info.get("company_name", "Đơn vị cứu hộ")).classes(
                                                    "text-3xl font-black leading-tight text-white md:text-4xl"
                                                )
                                                with ui.row().classes("items-center gap-2 flex-wrap"):
                                                    ui.label(_stars(rating_avg)).classes("text-base tracking-wide text-amber-300")
                                                    ui.label(f"{rating_avg:.1f}").classes("text-sm font-black text-white")
                                                    ui.label(f"({rating_count} đánh giá)").classes("text-sm text-white/85")
                                                with ui.row().classes("items-center gap-2 text-white/90 flex-wrap"):
                                                    ui.icon("place", size="1rem")
                                                    ui.label(info.get("address") or "Chưa cập nhật địa chỉ").classes("text-sm")
                                                with ui.row().classes("items-center gap-2 text-white/90 flex-wrap"):
                                                    ui.icon("call", size="1rem")
                                                    ui.label(hotline or "Chưa cập nhật hotline").classes("text-sm font-semibold")
                                                with ui.row().classes(
                                                    "w-fit items-center gap-2 rounded-full bg-white/15 px-3 py-1 backdrop-blur-md"
                                                ):
                                                    ui.icon("circle", size="0.7rem").classes(
                                                        "text-emerald-400" if is_active else "text-slate-300"
                                                    )
                                                    ui.label("Đang hoạt động" if is_active else "Ngoại tuyến").classes(
                                                        "text-xs font-bold text-white"
                                                    )

                                        with ui.row().classes("gap-2 pb-1 flex-wrap"):
                                            ui.button(
                                                "Gọi ngay",
                                                icon="phone",
                                                on_click=lambda: ui.navigate.to(f"tel:{hotline}") if hotline else ui.notify("Chưa có hotline", type="warning"),
                                            ).classes("rounded-xl bg-emerald-500 px-4 py-2.5 font-bold text-white shadow-lg hover:bg-emerald-600").props("unelevated")
                                            ui.button(
                                                "Đặt cứu hộ",
                                                icon="near_me",
                                                on_click=lambda: (dialog.close(), ui.navigate.to("/customer/find-rescue")),
                                            ).classes("rounded-xl bg-orange-500 px-4 py-2.5 font-bold text-white shadow-lg hover:bg-orange-600").props("unelevated")

                        with ui.column().classes("w-full gap-4 p-4 md:p-6"):
                            with ui.row().classes("w-full gap-3 flex-wrap"):
                                _kpi_card("Đã hoàn thành", str(_completed_count()), "task_alt", "bg-emerald-50 text-emerald-600")
                                _kpi_card("Đánh giá TB", f"{rating_avg:.1f}/5", "star", "bg-amber-50 text-amber-600")
                                _kpi_card("Phạm vi phục vụ", f"{info.get('service_radius_km') or 50} km", "hub", "bg-blue-50 text-blue-600")
                                _kpi_card("ETA trung bình", f"{eta} phút", "schedule", "bg-indigo-50 text-indigo-600")

                            if info.get("description"):
                                with ui.card().classes("w-full rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"):
                                    ui.label("Giới thiệu").classes("text-base font-black text-slate-900")
                                    ui.label(info["description"]).classes("mt-2 text-sm leading-relaxed text-slate-600")

                            with ui.card().classes("w-full rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"):
                                ui.label("Dịch vụ cung cấp").classes("text-base font-black text-slate-900")
                                with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
                                    for title, icon, subtitle in SERVICE_ITEMS:
                                        _service_chip(title, icon, subtitle)

                            _gallery()

                            with ui.row().classes("w-full gap-4 items-start"):
                                with ui.column().classes("flex-[1.15] min-w-[300px] gap-3"):
                                    ui.label(f"Đánh giá khách hàng ({len(data['reviews'])})").classes(
                                        "text-lg font-black text-slate-900"
                                    )
                                    if not data["reviews"]:
                                        with ui.card().classes("w-full rounded-2xl border border-dashed border-slate-200 bg-white p-8 items-center shadow-sm"):
                                            ui.icon("reviews", size="2rem").classes("text-slate-300")
                                            ui.label("Chưa có đánh giá nào").classes("text-sm font-semibold text-slate-500")
                                    else:
                                        for review in data["reviews"][:8]:
                                            _review_card(review)

                                with ui.column().classes("flex-1 min-w-[280px] gap-4"):
                                    _rating_chart()
                                    with ui.card().classes("w-full rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"):
                                        ui.label("Lịch sử của bạn").classes("text-base font-black text-slate-900")
                                        if not data["history"]:
                                            ui.label("Bạn chưa sử dụng dịch vụ của đơn vị này.").classes(
                                                "mt-2 text-sm text-slate-500"
                                            )
                                        else:
                                            with ui.column().classes("w-full gap-3 mt-3"):
                                                for item in data["history"][:5]:
                                                    services = ", ".join(item.get("services", [])) or "Dịch vụ cứu hộ"
                                                    with ui.row().classes("w-full items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2"):
                                                        with ui.column().classes("gap-0 min-w-0"):
                                                            ui.label(services).classes("truncate text-sm font-bold text-slate-800")
                                                            ui.label(_format_date(item.get("created_at", ""))).classes("text-xs text-slate-400")
                                                        ui.badge(item.get("status", "--")).classes("rounded-full bg-blue-50 text-blue-700")
        except Exception as exc:
            print("\n========== RENDER ERROR ==========")
            traceback.print_exc()
            print("==================================\n")
            ui.notify(f"Lỗi render UI: {exc}", type="negative")

    with ui.dialog() as dialog:
        with ui.card().classes("w-full max-w-6xl p-0 overflow-hidden rounded-[28px] border-none shadow-2xl"):
            loading_bar = ui.linear_progress(value=0, show_value=False).classes("absolute top-0 z-50 w-full")
            loading_bar.visible = False
            info_container = ui.column().classes("w-full")

    async def start():
        dialog.open()
        await _load_details()

    ui.timer(0.1, start, once=True)
