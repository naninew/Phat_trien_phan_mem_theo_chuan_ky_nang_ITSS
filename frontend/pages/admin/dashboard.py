"""
Trang Dashboard dành cho Quản trị viên (Admin).
"""
from nicegui import ui
from typing import Optional, Dict, Any, List

from core.auth import require_admin_auth, get_user_name
from components.page_layout import page_layout
from services.admin_api import get_stats, get_all_requests


def create_admin_dashboard():

    @ui.page('/admin/dashboard')
    async def admin_dashboard():
        if not require_admin_auth():
            return

        with page_layout("/admin/dashboard", title="Hệ Thống Quản Trị"):
            name = get_user_name()
            
            # Header section
            with ui.card().classes("w-full rounded-3xl bg-indigo-900 text-white p-8 shadow-xl border-none"):
                with ui.row().classes("w-full justify-between items-center"):
                    with ui.column().classes("gap-1"):
                        ui.label(f"Chào mừng Admin, {name}!").classes("text-3xl font-bold")
                        ui.label("Hệ thống quản lý cứu hộ xe toàn quốc").classes("text-indigo-300")
                    
                    with ui.row().classes("gap-2"):
                        ui.button("Người Dùng", icon="people", on_click=lambda: ui.navigate.to("/admin/users")).classes("bg-white/10 rounded-xl font-bold")
                        ui.button("Công Ty", icon="business", on_click=lambda: ui.navigate.to("/admin/companies")).classes("bg-white/10 rounded-xl font-bold")

            # Thống kê hệ thống
            ui.label("Thống kê toàn hệ thống").classes("text-xl font-bold text-gray-700 mt-4 ml-2")
            with ui.row().classes("w-full gap-4"):
                user_card = _stat_card("Người dùng", "...", "people", "blue")
                company_card = _stat_card("Công ty", "...", "business", "green")
                request_card = _stat_card("Yêu cầu (Tổng)", "...", "assignment", "purple")
                req_today_card = _stat_card("Yêu cầu (Hôm nay)", "...", "today", "orange")
                revenue_card = _stat_card("Doanh thu (Tổng)", "...", "payments", "emerald")
                rev_month_card = _stat_card("Doanh thu (Tháng)", "...", "account_balance_wallet", "teal")

            # Trạng thái yêu cầu
            ui.label("Trạng thái yêu cầu").classes("text-xl font-bold text-gray-700 mt-6 ml-2")
            with ui.row().classes("w-full gap-4"):
                pending_card = _stat_card("Đang chờ", "...", "pending", "amber")
                progress_card = _stat_card("Đang xử lý", "...", "engineering", "blue")
                completed_card = _stat_card("Đã hoàn thành", "...", "check_circle", "green")

            # Charts section
            ui.label("Biểu đồ phân tích").classes("text-xl font-bold text-gray-700 mt-6 ml-2")
            with ui.row().classes("w-full gap-4"):
                with ui.card().classes("flex-1 rounded-2xl shadow-sm border border-gray-100 p-4 min-w-[300px]"):
                    ui.label("Phân bổ trạng thái yêu cầu").classes("font-bold text-gray-500 mb-2")
                    status_chart = ui.echart({
                        'tooltip': {'trigger': 'item'},
                        'legend': {'bottom': '0'},
                        'series': [{
                            'name': 'Trạng thái',
                            'type': 'pie',
                            'radius': ['40%', '70%'],
                            'avoidLabelOverlap': False,
                            'itemStyle': {'borderRadius': 10, 'borderColor': '#fff', 'borderWidth': 2},
                            'label': {'show': False, 'position': 'center'},
                            'emphasis': {'label': {'show': True, 'fontSize': '20', 'fontWeight': 'bold'}},
                            'data': []
                        }]
                    }).classes("h-64 w-full")

                with ui.card().classes("flex-1 rounded-2xl shadow-sm border border-gray-100 p-4 min-w-[300px]"):
                    ui.label("Loại sự cố phổ biến").classes("font-bold text-gray-500 mb-2")
                    incident_chart = ui.echart({
                        'xAxis': {'type': 'category', 'data': []},
                        'yAxis': {'type': 'value'},
                        'series': [{'data': [], 'type': 'bar', 'itemStyle': {'color': '#6366f1'}}]
                    }).classes("h-64 w-full")

                with ui.card().classes("flex-1 rounded-2xl shadow-sm border border-gray-100 p-4 min-w-[300px]"):
                    ui.label("Yêu cầu 7 ngày gần đây").classes("font-bold text-gray-500 mb-2")
                    daily_chart = ui.echart({
                        'xAxis': {'type': 'category', 'data': []},
                        'yAxis': {'type': 'value'},
                        'series': [{'data': [], 'type': 'bar', 'itemStyle': {'color': '#3b82f6'}}]
                    }).classes("h-64 w-full")

            # Pending Companies Table
            ui.label("Công ty chờ xác minh").classes("text-xl font-bold text-gray-700 mt-8 ml-2")
            with ui.card().classes("w-full rounded-2xl p-0 overflow-hidden shadow-sm border border-gray-100 mt-2"):
                pending_companies_table = ui.table(
                    columns=[
                        {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                        {'name': 'name', 'label': 'Tên công ty', 'field': 'company_name', 'align': 'left'},
                        {'name': 'rep', 'label': 'Người đại diện', 'field': 'representative_name', 'align': 'left'},
                        {'name': 'phone', 'label': 'SĐT', 'field': 'phone', 'align': 'center'},
                        {'name': 'date', 'label': 'Ngày đăng ký', 'field': 'registered_at', 'align': 'center'},
                        {'name': 'actions', 'label': 'Thao tác', 'field': 'id', 'align': 'center'},
                    ],
                    rows=[]
                ).classes("w-full shadow-none").props("flat")
                
                pending_companies_table.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn flat dense round color="positive" icon="check" @click="$parent.$emit('approve', props.row.id)">
                            <q-tooltip>Duyệt</q-tooltip>
                        </q-btn>
                        <q-btn flat dense round color="negative" icon="close" @click="$parent.$emit('reject', props.row.id)">
                            <q-tooltip>Từ chối</q-tooltip>
                        </q-btn>
                    </q-td>
                ''')

            # Recent Requests Table
            ui.label("Hoạt động gần đây").classes("text-xl font-bold text-gray-700 mt-8 ml-2")
            with ui.card().classes("w-full rounded-2xl p-0 overflow-hidden shadow-sm border border-gray-100 mt-2"):
                requests_table = ui.table(
                    columns=[
                        {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                        {'name': 'customer', 'label': 'Khách hàng', 'field': 'customer_name', 'align': 'left'},
                        {'name': 'company', 'label': 'Công ty', 'field': 'company_name', 'align': 'left'},
                        {'name': 'status', 'label': 'Trạng thái', 'field': 'status', 'align': 'center'},
                        {'name': 'cost', 'label': 'Chi phí', 'field': 'total_cost', 'align': 'right'},
                        {'name': 'payment', 'label': 'Thanh toán', 'field': 'payment_status', 'align': 'center'},
                    ],
                    rows=[]
                ).classes("w-full shadow-none").props("flat")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def on_approve(e):
            from services.admin_api import update_company_status
            try:
                await update_company_status(e.args, "active")
                ui.notify("Đã duyệt công ty", type="positive")
                await _load_data()
            except Exception as ex:
                ui.notify(f"Lỗi: {ex}", type="negative")
                
        async def on_reject(e):
            from services.admin_api import update_company_status
            try:
                # Update status to suspended or rejected
                await update_company_status(e.args, "suspended")
                ui.notify("Đã từ chối công ty", type="warning")
                await _load_data()
            except Exception as ex:
                ui.notify(f"Lỗi: {ex}", type="negative")

        pending_companies_table.on('approve', on_approve)
        pending_companies_table.on('reject', on_reject)

        async def _load_data():
            try:
                from services.admin_api import get_chart_stats, get_daily_stats, get_pending_companies
                
                # Load basic stats
                s = await get_stats()
                user_card.clear()
                with user_card: _stat_card("Người dùng", str(s.get('total_users', 0)), "people", "blue")
                company_card.clear()
                with company_card: _stat_card("Công ty", str(s.get('active_companies', 0)), "business", "green")
                request_card.clear()
                with request_card: _stat_card("Yêu cầu (Tổng)", str(s.get('total_requests', 0)), "assignment", "purple")
                req_today_card.clear()
                with req_today_card: _stat_card("Yêu cầu (Hôm nay)", str(s.get('requests_today', 0)), "today", "orange")
                
                rev_fmt = f"{int(s.get('total_revenue', 0)):,} đ"
                revenue_card.clear()
                with revenue_card: _stat_card("Doanh thu (Tổng)", rev_fmt, "payments", "emerald")
                
                rev_month_fmt = f"{int(s.get('revenue_this_month', 0)):,} đ"
                rev_month_card.clear()
                with rev_month_card: _stat_card("Doanh thu (Tháng)", rev_month_fmt, "account_balance_wallet", "teal")

                # Status cards
                status_dict = s.get('requests_by_status', {})
                pending_card.clear()
                with pending_card: _stat_card("Đang chờ", str(status_dict.get('PENDING', 0)), "pending", "amber")
                progress_card.clear()
                with progress_card: _stat_card("Đang xử lý", str(status_dict.get('IN_PROGRESS', 0)), "engineering", "blue")
                completed_card.clear()
                with completed_card: _stat_card("Đã hoàn thành", str(status_dict.get('COMPLETED', 0)), "check_circle", "green")

                # Load pie and incident charts
                c = await get_chart_stats()
                status_chart.options['series'][0]['data'] = c.get('status_chart', [])
                status_chart.update()
                
                incident_chart.options['xAxis']['data'] = c.get('incident_chart', {}).get('labels', [])
                incident_chart.options['series'][0]['data'] = c.get('incident_chart', {}).get('values', [])
                incident_chart.update()

                # Load daily chart
                d = await get_daily_stats(7)
                daily_chart.options['xAxis']['data'] = d.get('labels', [])
                daily_chart.options['series'][0]['data'] = d.get('values', [])
                daily_chart.update()

                # Load pending companies
                comps = await get_pending_companies()
                for c_item in comps:
                    # format date
                    if 'registered_at' in c_item:
                        c_item['registered_at'] = c_item['registered_at'][:10]
                pending_companies_table.rows = comps

                # Load recent requests
                reqs = await get_all_requests()
                requests_table.rows = reqs[:10]
            except Exception as e:
                ui.notify(f"Lỗi tải dữ liệu: {e}", type="negative")

        await _load_data()
        timer = ui.timer(60, _load_data)
        ui.context.client.on_disconnect(timer.deactivate)


def _stat_card(title, value, icon, color):
    with ui.card().classes(f"flex-1 min-w-[150px] rounded-2xl p-6 shadow-sm border border-{color}-100 bg-white items-center gap-1") as card:
        ui.icon(icon, size="2rem", color=color)
        ui.label(value).classes(f"text-4xl font-bold text-{color}-700 break-words text-center w-full")
        ui.label(title).classes("text-xs sm:text-sm text-gray-400 font-bold uppercase text-center w-full")
    return card


def _action_card(title, icon, route, desc, color):
    with ui.card().classes("flex-1 min-w-[280px] rounded-2xl p-6 shadow-sm border border-gray-100 hover:border-indigo-300 transition-all cursor-pointer").on("click", lambda: ui.navigate.to(route)):
        with ui.row().classes("items-center gap-4"):
            ui.avatar(icon=icon).classes(f"bg-{color}-100 text-{color}-600")
            with ui.column().classes("gap-0"):
                ui.label(title).classes("font-bold text-lg text-gray-800")
                ui.label(desc).classes("text-sm text-gray-500")

