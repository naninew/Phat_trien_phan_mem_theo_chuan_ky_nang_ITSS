"""
Customer requests page to view and track rescue requests.
"""
from nicegui import ui
from typing import Optional, Dict, Any, List
from ..core.auth import require_auth, get_current_user, get_access_token, CUSTOMER_DASHBOARD
from ..components.navbar import create_navbar
from ..services.rescue_api import get_my_requests, get_request_details, cancel_request


def create_requests_page():
    """Create customer requests page with NiceGUI components."""
    
    @ui.page('/customer/requests')
    def requests_page():
        # Require authentication
        if not require_auth():
            return
        
        create_navbar("My Requests")
        
        with ui.column().classes('w-full p-8'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('My Rescue Requests').classes('text-2xl font-bold')
                ui.button('Back to Dashboard', on_click=lambda: ui.navigate.to(CUSTOMER_DASHBOARD)).props('outline')
            
            # Status filter
            status_filter = ui.select(
                options=['all', 'pending', 'accepted', 'in_progress', 'completed', 'cancelled'],
                label='Filter by Status',
                value='all'
            ).classes('w-full max-w-xs mt-4')
            
            # Refresh button
            refresh_btn = ui.button(icon='refresh', on_click=lambda: load_requests()).props('round dense flat')
            
            # Requests container
            requests_container = ui.column().classes('w-full mt-4')
            
            # Status colors mapping
            status_colors = {
                'pending': 'orange',
                'accepted': 'blue',
                'in_progress': 'purple',
                'completed': 'green',
                'cancelled': 'red',
            }
            
            async def load_requests():
                """Load and display user's requests."""
                token = get_access_token()
                
                with requests_container:
                    requests_container.clear()
                    
                    try:
                        requests = await get_my_requests(token=token)
                        
                        if not requests:
                            ui.label('No rescue requests found').classes('text-gray-500 p-4')
                            return
                        
                        # Filter by status
                        filter_val = status_filter.value
                        if filter_val != 'all':
                            requests = [r for r in requests if r.get('status') == filter_val]
                        
                        for req in requests:
                            request_id = req.get('id')
                            status = req.get('status', 'unknown')
                            service_name = req.get('service_name', 'Unknown Service')
                            created_at = req.get('created_at', 'N/A')
                            
                            # Create request card
                            with ui.card().classes('w-full p-4 mb-4'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    ui.label(f'Request #{request_id}').classes('text-lg font-bold')
                                    ui.badge(status, color=status_colors.get(status, 'gray'))
                                
                                ui.label(f'Service: {service_name}').classes('text-gray-600')
                                ui.label(f'Created: {created_at}').classes('text-gray-500 text-sm')
                                
                                # Location info
                                location = req.get('address_description', 'No description')
                                ui.label(f'Location: {location}').classes('text-gray-600')
                                
                                # Issue description
                                issue = req.get('car_issue_detail', 'No details')
                                ui.label(f'Issue: {issue}').classes('text-gray-600')
                                
                                # Company info if assigned
                                company_name = req.get('company_name')
                                if company_name:
                                    ui.label(f'Company: {company_name}').classes('text-blue-600')
                                
                                # ETA if available
                                eta = req.get('eta_minutes')
                                if eta:
                                    ui.label(f'ETA: {eta} minutes').classes('text-purple-600')
                                
                                # Actions
                                with ui.row().classes('w-full gap-2 mt-2'):
                                    # View details button
                                    async def show_details(r=req):
                                        """Show request details dialog."""
                                        details = await get_request_details(r.get('id'), token=token)
                                        if details:
                                            ui.notify(f'Request #{r.get("id")} - {details}', color='info')
                                    
                                    ui.button('Details', on_click=show_details).props('outline')
                                    
                                    # Cancel button (only for pending requests)
                                    if status == 'pending':
                                        async def do_cancel(r=req):
                                            """Cancel a pending request."""
                                            confirmed = await ui.dialog(
                                                title='Confirm Cancel',
                                                message='Are you sure you want to cancel this request?',
                                                persistent=True
                                            ).wait()
                                            
                                            if confirmed:
                                                try:
                                                    await cancel_request(r.get('id'), token=token)
                                                    ui.notify('Request cancelled', color='positive')
                                                    await load_requests()
                                                except Exception as e:
                                                    ui.notify(f'Cancel failed: {str(e)}', color='negative')
                                        
                                        ui.button('Cancel', on_click=do_cancel).props('color=negative outline')
                        
                    except Exception as e:
                        ui.label(f'Error loading requests: {str(e)}').classes('text-red-500')
            
            # Initial load
            ui.timer(1.0, load_requests, once=True)

