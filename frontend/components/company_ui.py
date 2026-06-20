"""
Shared presentation helpers for company dashboard pages.
"""
from __future__ import annotations

from nicegui import ui


def inject_company_styles() -> None:
    ui.add_head_html("""
    <style>
        .company-page {
            width: 100%;
            max-width: 1280px;
            margin: 0 auto;
            padding: 0 4px 28px;
        }
        .company-header-title {
            color: #0f172a;
            font-size: 30px;
            line-height: 1.15;
            font-weight: 900;
            letter-spacing: 0;
        }
        .company-header-subtitle {
            color: #64748b;
            font-size: 14px;
            line-height: 1.5;
        }
        .company-icon-box {
            height: 44px;
            width: 44px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #eff6ff;
            color: #2563eb;
            box-shadow: inset 0 0 0 1px #dbeafe;
        }
        .company-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 22px;
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
        }
        .company-two-column {
            display: grid;
            grid-template-columns: minmax(0, 1.6fr) minmax(300px, 1fr);
            gap: 20px;
            align-items: start;
            width: 100%;
        }
        .company-two-column-main {
            min-width: 0;
        }
        .company-two-column-side {
            min-width: 0;
            width: 100%;
            justify-self: end;
        }
        @media (max-width: 980px) {
            .company-two-column {
                grid-template-columns: 1fr;
            }
        }
        .company-card-hover {
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }
        .company-card-hover:hover {
            transform: translateY(-2px);
            border-color: #bfdbfe;
            box-shadow: 0 16px 34px rgba(15, 23, 42, 0.10);
        }
        .company-primary-btn {
            height: 44px;
            border-radius: 14px;
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            color: #ffffff;
            font-weight: 850;
            text-transform: none;
            box-shadow: 0 12px 24px rgba(37, 99, 235, 0.24);
        }
        .company-primary-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 16px 30px rgba(37, 99, 235, 0.30);
        }
        .company-muted-btn {
            border-radius: 12px;
            color: #2563eb;
            font-weight: 800;
            text-transform: none;
        }
        .company-section-title {
            color: #0f172a;
            font-size: 18px;
            font-weight: 900;
            letter-spacing: 0;
        }
        .company-section-subtitle {
            color: #64748b;
            font-size: 13px;
        }
        .company-kpi-label {
            color: #94a3b8;
            font-size: 12px;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .company-kpi-value {
            color: #0f172a;
            font-size: 30px;
            line-height: 1.1;
            font-weight: 950;
        }
        .company-kpi-subtitle {
            color: #64748b;
            font-size: 12px;
            font-weight: 650;
        }
        .company-status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            width: fit-content;
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 12px;
            line-height: 1;
            font-weight: 850;
            border: 1px solid;
        }
        .company-badge-blue { background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; }
        .company-badge-amber { background: #fffbeb; color: #b45309; border-color: #fde68a; }
        .company-badge-emerald { background: #ecfdf5; color: #047857; border-color: #a7f3d0; }
        .company-badge-red { background: #fef2f2; color: #dc2626; border-color: #fecaca; }
        .company-badge-slate { background: #f8fafc; color: #475569; border-color: #e2e8f0; }
        .company-donut {
            --value: 50;
            --track: #e5e7eb;
            --color: #2563eb;
            width: 86px;
            height: 86px;
            border-radius: 50%;
            background: conic-gradient(var(--color) calc(var(--value) * 1%), var(--track) 0);
            position: relative;
            flex-shrink: 0;
        }
        .company-donut::after {
            content: "";
            position: absolute;
            inset: 12px;
            border-radius: 50%;
            background: #ffffff;
            box-shadow: inset 0 0 0 1px #eef2f7;
        }
        .company-donut-label {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1;
            color: #0f172a;
            font-size: 16px;
            font-weight: 950;
        }
        .company-table {
            border-radius: 20px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
            overflow: hidden;
        }
        .company-table thead tr {
            background: #f8fafc;
        }
        .company-table th {
            color: #64748b;
            font-size: 12px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .company-table tbody tr:hover {
            background: #f8fafc;
        }
        .company-field .q-field__control {
            border-radius: 14px;
        }
        body.body--dark .company-page,
        body.body--dark .company-header-title,
        body.body--dark .company-section-title,
        body.body--dark .company-kpi-value,
        body.body--dark .company-donut-label {
            color: #f8fbff !important;
        }
        body.body--dark .company-header-subtitle,
        body.body--dark .company-section-subtitle,
        body.body--dark .company-kpi-subtitle {
            color: #a8b7cf !important;
        }
        body.body--dark .company-card,
        body.body--dark .company-table {
            background: #111c2f !important;
            border-color: rgba(148, 163, 184, 0.18) !important;
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.22) !important;
        }
        body.body--dark .company-donut::after {
            background: #111c2f;
            box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.18);
        }
    </style>
    """)


def page_header(title: str, subtitle: str, icon: str, action_label: str | None = None,
                action_icon: str = "add", on_action=None):
    with ui.row().classes("w-full items-center justify-between gap-4"):
        with ui.row().classes("items-center gap-3"):
            with ui.element("div").classes("company-icon-box"):
                ui.icon(icon, size="22px")
            with ui.column().classes("gap-1"):
                ui.label(title).classes("company-header-title font-outfit")
                ui.label(subtitle).classes("company-header-subtitle")
        if action_label:
            ui.button(action_label, icon=action_icon, on_click=on_action).classes("company-primary-btn px-5").props("unelevated no-caps")


def kpi_card(title: str, value: str | int, subtitle: str, icon: str, accent: str = "#2563eb"):
    with ui.element("div").classes("company-card-hover flex-1 min-w-[200px] p-5 rounded-[22px]").style(
        f"background: color-mix(in srgb, {accent} 10%, white); "
        f"border: 1px solid color-mix(in srgb, {accent} 18%, #e5e7eb);"
    ):
        with ui.row().classes("w-full items-start justify-between gap-4"):
            with ui.column().classes("gap-1"):
                ui.label(title).classes("text-[11px] font-extrabold uppercase tracking-widest").style(
                    f"color: color-mix(in srgb, {accent} 65%, #64748b);"
                )
                ui.label(str(value)).classes("text-[32px] font-black font-outfit leading-none mt-1").style(
                    f"color: color-mix(in srgb, {accent} 85%, #0f172a);"
                )
                ui.label(subtitle).classes("text-xs font-medium mt-1").style("color: #64748b;")
            with ui.element("div").classes(
                "h-12 w-12 rounded-2xl flex items-center justify-center flex-shrink-0"
            ).style(
                f"background: white; color: {accent}; "
                f"box-shadow: 0 4px 14px color-mix(in srgb, {accent} 22%, transparent);"
            ):
                ui.icon(icon, size="26px")


def section_heading(title: str, subtitle: str = ""):
    with ui.column().classes("gap-1"):
        ui.label(title).classes("company-section-title font-outfit")
        if subtitle:
            ui.label(subtitle).classes("company-section-subtitle")


def status_badge(text: str, tone: str = "slate"):
    ui.label(text).classes(f"company-status-badge company-badge-{tone}")


def donut(value: int, label: str, color: str = "#2563eb"):
    value = max(0, min(100, int(value)))
    with ui.element("div").classes("company-donut").style(f"--value: {value}; --color: {color};"):
        ui.label(label).classes("company-donut-label")


def empty_state(icon: str, title: str, subtitle: str):
    with ui.column().classes("w-full items-center justify-center gap-3 py-16 rounded-3xl border border-dashed border-slate-200 bg-slate-50"):
        ui.icon(icon, size="3.5rem").classes("text-slate-300")
        ui.label(title).classes("text-lg font-black text-slate-700")
        ui.label(subtitle).classes("text-sm text-slate-500 text-center")
