"""
Admin companies management page for NiceGUI frontend.
"""
from nicegui import ui
from typing import Optional, Dict, Any, List
from frontend.core.auth import require_auth, get_current_user, get_access_token, ADMIN_DASHBOARD
from frontend.components.navbar import create_navbar


def create_companies_page():
    """Create admin companies management page with NiceGUI components."""
    
    @ui.page('/admin/companies')
    def companies_page():
        # Require authentication and admin role
        if not require_auth():
            return
        
        user_role = get_user_role()
        if user_role != 'admin':
            ui.notify("Access denied - Admin only", color="negative")
            ui.navigate.to(ADMIN_DASHBOARD)
            return
        
        create_navbar("Company Management")
        
        with ui.column().classes('w-full p-8'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('Rescue Companies').classes('text-2xl font-bold')
                
                # Status filter
                status_filter = ui.select(
                    options=['all', 'active', 'pending', 'suspended'],
                    label='Filter by Status',
                    value='all'
                ).classes('w-full max-w-xs')
            
            # Refresh button
            ui.button(icon='refresh', on_click=lambda: load_companies()).props('round dense flat')
            
            # Companies container
            companies_container = ui.column().classes('w-full mt-4')
            
            # Status colors
            status_colors = {
                'active': 'green',
                'pending': 'orange',
                'suspended': 'red',
            }
            
            async def load_companies():
                """Load and display all rescue companies."""
                token = get_access_token()
                
                with companies_container:
                    companies_container.clear()
                    
                    # Mock data for demonstration
                    mock_companies = [
                        {
                            'id': 1,
                            'company_name': 'Fast Rescue Co.',
                            'address': '123 Le Loi Street, District 1, HCMC',
                            'hotline': '19001234',
                            'license_number': 'GP-2024-001',
                            'rating_avg': 4.5,
                            'status': 'active',
                            'contact_person': 'Mr. Tran Van E',
                        },
                        {
                            'id': 2,
                            'company_name': '24/7 Roadside Assistance',
                            'address': '456 Nguyen Hue Boulevard, District 1, HCMC',
                            'hotline': '19005678',
                            'license_number': 'GP-2024-002',
                            'rating_avg': 4.2,
                            'status': 'pending',
                            'contact_person': 'Ms. Le Thi F',
                        },
                    ]
                    
                    # Filter by status
                    filter_val = status_filter.value
                    if filter_val != 'all':
                        mock_companies = [c for c in mock_companies if c.get('status') == filter_val]
                    
                    if not mock_companies:
                        ui.label('No companies found').classes('text-gray-500 p-4')
                        return
                    
                    for company in mock_companies:
                        company_id = company.get('id')
                        status = company.get('status', 'unknown')
                        rating = company.get('rating_avg', 0)
                        
                        with ui.card().classes('w-full p-4 mb-4'):
                            with ui.row().classes('w-full items-center justify-between'):
                                ui.label(f'{company.get("company_name")}').classes('text-lg font-bold')
                                with ui.row().classes('gap-2'):
                                    ui.badge(status, color=status_colors.get(status, 'gray'))
                                    ui.label(f'⭐ {rating}').classes('text-yellow-600 font-bold')
                            
                            ui.label(f'Address: {company.get("address")}').classes('text-gray-600')
                            ui.label(f'Hotline: {company.get("hotline")}').classes('text-gray-600')
                            ui.label(f'License: {company.get("license_number")}').classes('text-gray-600')
                            ui.label(f'Contact: {company.get("contact_person")}').classes('text-gray-600')
                            
                            # Action buttons
                            with ui.row().classes('w-full gap-2 mt-2'):
                                async def view_details(c=company):
                                    """View company details."""
                                    ui.notify(f'View details for {c.get("company_name")}', color='info')
                                
                                async def approve_company(c=company):
                                    """Approve a pending company."""
                                    ui.notify(f'Approved {c.get("company_name")}', color='positive')
                                    await load_companies()
                                
                                async def suspend_company(c=company):
                                    """Suspend a company."""
                                    confirmed = await ui.dialog(
                                        title='Confirm Suspend',
                                        message=f'Are you sure you want to suspend {c.get("company_name")}?',
                                        persistent=True
                                    ).wait()
                                    
                                    if confirmed:
                                        ui.notify(f'Suspended {c.get("company_name")}', color='negative')
                                        await load_companies()
                                
                                ui.button('View Details', on_click=view_details).props('outline')
                                
                                if status == 'pending':
                                    ui.button('Approve', on_click=approve_company).props('color=positive')
                                
                                if status == 'active':
                                    ui.button('Suspend', on_click=suspend_company).props('color=negative outline')
            
            # Initial load
            ui.timer(1.0, load_companies, once=True)

