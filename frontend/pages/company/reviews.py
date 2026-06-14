"""
Company Reviews - NiceGUI
"""
from collections import Counter
from datetime import datetime, timedelta
from html import escape
from urllib.parse import quote
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from components.company_ui import empty_state, inject_company_styles, kpi_card, page_header, section_heading, status_badge
from core.config import BACKEND_URL
from services.rescue_api import get_company_reviews


def _media_url(path: str | None) -> str:
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{BACKEND_URL.replace('/api/v1', '')}{path}"


def _fallback_avatar(name: str) -> str:
    initials = escape("".join(part[:1].upper() for part in (name or "KH").split()[:2]) or "KH")
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop stop-color="#60a5fa"/>
          <stop offset="1" stop-color="#2563eb"/>
        </linearGradient>
      </defs>
      <rect width="96" height="96" rx="48" fill="url(#g)"/>
      <text x="48" y="56" text-anchor="middle" font-family="Arial, sans-serif" font-size="28" font-weight="800" fill="white">{initials}</text>
    </svg>
    """
    return "data:image/svg+xml;charset=utf-8," + quote(svg)


def create_reviews_page():
    """Register /company/reviews route."""

    @ui.page('/company/reviews')
    async def reviews_page():
        if not require_role("company_staff"):
            return

        inject_company_styles()

        ui.add_head_html("""
        <style>
        .review-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            transition: transform 0.18s ease, box-shadow 0.18s ease;
            min-width: 0;
        }
        .review-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 14px 28px rgba(15, 23, 42, 0.11);
        }
        .review-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            width: 100%;
        }
        @media (max-width: 1100px) {
            .review-grid { grid-template-columns: repeat(2, 1fr); }
        }
        @media (max-width: 640px) {
            .review-grid { grid-template-columns: 1fr; }
        }
        body.body--dark .review-card {
            background: #111c2f !important;
            border-color: rgba(148,163,184,0.18) !important;
        }
        .review-rating-pie {
            width: 112px;
            height: 112px;
            border-radius: 50%;
            background: conic-gradient(#f59e0b 0deg 360deg);
            position: relative;
            flex-shrink: 0;
        }
        .review-rating-pie::after {
            content: "";
            position: absolute;
            inset: 16px;
            border-radius: 50%;
            background: #ffffff;
            box-shadow: inset 0 0 0 1px #eef2f7;
        }
        .review-rating-pie-label {
            position: absolute;
            inset: 0;
            z-index: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #0f172a;
            font-weight: 950;
            font-size: 18px;
        }
        </style>
        """)

        # Store all fetched reviews for client-side filtering
        all_reviews = []

        with page_layout("/company/reviews", title=""):
            with ui.column().classes("company-page gap-6"):
                page_header(
                    "Đánh giá khách hàng",
                    "Theo dõi chất lượng dịch vụ, xu hướng điểm số và phản hồi mới.",
                    "star_rate",
                )

                stats_row = ui.row().classes("w-full gap-4 flex-wrap")
                with ui.row().classes("w-full gap-5 items-start"):
                    with ui.element("div").classes("company-card p-5 flex-[1.3] min-w-[420px]"):
                        section_heading("Xu hướng đánh giá", "Điểm trung bình theo các phản hồi gần nhất")
                        trend_bars = ui.row().classes("w-full items-end gap-2 h-36 mt-5")
                    with ui.element("div").classes("company-card p-5 flex-1 min-w-[320px]"):
                        section_heading("Phân bổ số sao", "Tỷ lệ từng mức đánh giá")
                        star_donut = ui.column().classes("w-full gap-4 py-4")

                # ── Filter bar ────────────────────────────────────────────────
                with ui.element("div").classes("company-card p-4 w-full"):
                    with ui.row().classes("w-full items-center gap-3 flex-nowrap"):
                        ui.icon("filter_list", size="20px").classes("text-blue-600 flex-shrink-0")
                        ui.label("Bộ lọc:").classes("text-sm font-black text-slate-700 flex-shrink-0")

                        time_range = ui.select(
                            options={
                                'all': 'Tất cả thời gian',
                                '7d':  '7 ngày qua',
                                '1m':  '1 tháng qua',
                                '3m':  '3 tháng qua',
                                '6m':  '6 tháng qua',
                            },
                            value='all',
                        ).classes("min-w-[220px] flex-1 company-field").props("outlined rounded dense")

                        rating_filter = ui.select(
                            options={
                                0: "Tất cả số sao",
                                5: "⭐⭐⭐⭐⭐ 5 sao",
                                4: "⭐⭐⭐⭐ 4 sao",
                                3: "⭐⭐⭐ 3 sao",
                                2: "⭐⭐ 2 sao",
                                1: "⭐ 1 sao",
                            },
                            value=0,
                        ).classes("min-w-[220px] flex-1 company-field").props("outlined rounded dense")

                        def apply_filters():
                            _render_reviews(all_reviews)

                        def reset_filters():
                            time_range.value = 'all'
                            rating_filter.value = 0
                            time_range.update()
                            rating_filter.update()
                            _render_reviews(all_reviews)

                        rating_filter.on_value_change(lambda _: apply_filters())
                        time_range.on_value_change(lambda _: apply_filters())

                        with ui.row().classes("items-center gap-2 ml-auto flex-shrink-0"):
                            ui.button("Reset", icon="refresh", on_click=reset_filters).classes(
                                "company-primary-btn px-4"
                            ).props("unelevated no-caps")

                # ── Reviews grid ──────────────────────────────────────────────
                reviews_container = ui.element("div").classes("review-grid")

        def _render_reviews(reviews):
            tr = time_range.value
            r_min = rating_filter.value or 0

            if tr == '7d':
                d_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            elif tr == '1m':
                d_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            elif tr == '3m':
                d_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            elif tr == '6m':
                d_from = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            else:
                d_from = ''

            filtered = reviews
            if d_from:
                filtered = [r for r in filtered if str(r.get("created_at") or "")[:10] >= d_from]
            if r_min:
                filtered = [r for r in filtered if int(r.get("rating") or 0) == r_min]

            reviews_container.clear()
            with reviews_container:
                if not filtered:
                    empty_state("rate_review", "Chưa có đánh giá nào", "Khi khách hàng gửi phản hồi, danh sách sẽ xuất hiện tại đây.")
                for r in filtered:
                    _render_review_card(r)

        def _render_review_card(r):
            rating = int(r.get('rating') or 0)
            customer_name = r.get('customer_name') or 'Khách hàng ẩn danh'
            with ui.element("div").classes("review-card"):
                # Header: avatar + name + date
                with ui.row().classes("w-full items-center justify-between gap-2"):
                    with ui.row().classes("items-center gap-2 flex-1 min-w-0"):
                        avatar_url = _media_url(r.get("customer_avatar_url") or r.get("avatar_url")) or _fallback_avatar(customer_name)
                        ui.image(avatar_url).classes("h-9 w-9 rounded-full object-cover border border-slate-100 flex-shrink-0")
                        with ui.column().classes("gap-0 min-w-0"):
                            ui.label(customer_name).classes(
                                "text-sm font-black text-slate-900 truncate"
                            )
                            status_badge(r.get('service_name') or 'Dịch vụ cứu hộ', "blue")
                    ui.label(str(r.get('created_at') or '')[:10]).classes(
                        "text-xs font-bold text-slate-400 flex-shrink-0"
                    )

                # Stars
                with ui.row().classes("gap-0.5 items-center"):
                    for i in range(5):
                        ui.icon("star", size="16px").classes("text-amber-400" if i < rating else "text-slate-200")
                    ui.label(f"{rating}/5").classes("text-xs font-bold text-slate-500 ml-1")

                # Comment
                comment = r.get('comment') or "Không có nhận xét."
                ui.label(comment).classes(
                    "text-xs text-slate-600 leading-relaxed line-clamp-3"
                ).style("display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;")

        async def refresh_reviews():
            nonlocal all_reviews
            stats_row.clear()
            trend_bars.clear()
            star_donut.clear()

            reviews = await get_company_reviews()
            all_reviews = reviews
            total = len(reviews)
            avg = round(sum(int(r.get('rating') or 0) for r in reviews) / total, 1) if total else 0
            five_count = sum(1 for r in reviews if int(r.get('rating') or 0) == 5)
            five_pct = round(five_count / total * 100) if total else 0
            new_count = min(total, 5)

            with stats_row:
                kpi_card("Điểm trung bình", f"{avg}/5", "Trung bình toàn bộ đánh giá", "grade", "#f59e0b")
                kpi_card("Tổng đánh giá", total, "Phản hồi đã ghi nhận", "rate_review", "#2563eb")
                kpi_card("Tỷ lệ 5 sao", f"{five_pct}%", f"{five_count} đánh giá 5 sao", "stars", "#10b981")
                kpi_card("Phản hồi mới", new_count, "Các phản hồi gần đây", "mark_chat_unread", "#8b5cf6")

            rating_counts = Counter(int(r.get("rating") or 0) for r in reviews)
            rating_colors = {
                5: "#f59e0b",
                4: "#3b82f6",
                3: "#10b981",
                2: "#8b5cf6",
                1: "#ef4444",
            }
            segments = []
            cursor = 0
            for rating in [5, 4, 3, 2, 1]:
                deg = 360 * (rating_counts.get(rating, 0) / total) if total else 0
                if deg:
                    segments.append(f"{rating_colors[rating]} {cursor:.2f}deg {cursor + deg:.2f}deg")
                cursor += deg
            pie_bg = ", ".join(segments) if segments else "#e5e7eb 0deg 360deg"
            with star_donut:
                with ui.row().classes("w-full items-center justify-center gap-5 flex-wrap"):
                    with ui.element("div").classes("review-rating-pie").style(f"background: conic-gradient({pie_bg});"):
                        ui.label(f"{five_pct}%").classes("review-rating-pie-label")
                    with ui.column().classes("gap-2 min-w-[190px]"):
                        for rating in [5, 4, 3, 2, 1]:
                            count = rating_counts.get(rating, 0)
                            pct = round(count / total * 100) if total else 0
                            with ui.row().classes("w-full items-center justify-between rounded-xl bg-slate-50 px-3 py-2 gap-3"):
                                with ui.row().classes("items-center gap-2"):
                                    ui.element("div").classes("h-2.5 w-2.5 rounded-full").style(f"background:{rating_colors[rating]};")
                                    ui.label(f"{rating} sao").classes("text-xs font-bold text-slate-600")
                                ui.label(f"{pct}%").classes("text-xs font-black text-slate-800")

            with trend_bars:
                recent = reviews[-10:] if reviews else []
                for r in recent:
                    rating = int(r.get('rating') or 0)
                    height = max(10, rating * 22)
                    with ui.column().classes("flex-1 h-full justify-end items-center gap-2"):
                        ui.label(str(rating)).classes("text-xs font-bold text-slate-500")
                        ui.element("div").classes("w-full rounded-t-xl bg-amber-400").style(f"height:{height}px;")
                        ui.label(str(r.get('created_at') or '')[5:10]).classes("text-[10px] font-bold text-slate-400")

            _render_reviews(all_reviews)

        await refresh_reviews()
