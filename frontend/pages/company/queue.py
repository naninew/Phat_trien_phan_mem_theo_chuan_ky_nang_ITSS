"""
Company queue management page for NiceGUI frontend.
"""
from nicegui import ui
from typing import Optional, Dict, Any, List
from ..core.auth import require_auth, get_current_user, get_access_token, get_user_role
from ..components.navbar import create_navbar


def create_queue_page():
    """Create company queue management page with NiceGUI components."""
    
    @ui.page('/company/queue')
    def queue_page():
        # Require authentication
        if not require_auth():
            return
        
        create_navbar("Queue Management")
        
        with ui.column().classes('w-full p-8'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('Rescue Request Queue').classes('text-2xl font-bold')
                
                # Status filter
                status_filter = ui.select(
                    options=['all', 'pending', 'accepted', 'in_progress', 'completed'],
                    label='Filter by Status',
                    value='all'
                ).classes('w-full max-w-xs')
            
            # Refresh button
            ui.button(icon='refresh', on_click=lambda: load_queue()).props('round dense flat')
            
            # Queue container
            queue_container = ui.column().classes('w-full mt-4')
            
            # Status colors
            status_colors = {
                'pending': 'orange',
                'accepted': 'blue',
                'in_progress': 'purple',
                'completed': 'green',
                'cancelled': 'red',
            }
            
            async def load_queue():
                """Load and display queue requests."""
                token = get_access_token()
                
                with queue_container:
                    queue_container.clear()
                    
                    # Mock data for demonstration (replace with API call)
                    mock_requests = [
                        {
                            'id': 1,
                            'status': 'pending',
                            'service_name': 'Tire Change',
                            'customer_name': 'Nguyen Van A',
                            'location': 'Highway 1, Km 15',
                            'issue': 'Flat tire, need replacement',
                            'created_at': '2024-01-15 10:30:00',
                        },
                        {
                            'id': 2,
                            'status': 'in_progress',
                            'service_name': 'Battery Jump-Start',
                            'customer_name': 'Tran Thi B',
                            'location': 'Le Loi Street, District 1',
                            'issue': 'Car won\'t start, dead battery',
                            'created_at': '2024-01-15 09:15:00',
                        },
                    ]
                    
                    # Filter by status
                    filter_val = status_filter.value
                    if filter_val != 'all':
                        mock_requests = [r for r in mock_requests if r.get('status') == filter_val]
                    
                    if not mock_requests:
                        ui.label('No requests in queue').classes('text-gray-500 p-4')
                        return
                    
                    for req in mock_requests:
                        request_id = req.get('id')
                        status = req.get('status', 'unknown')
                        
                        with ui.card().classes('w-full p-4 mb-4'):
                            with ui.row().classes('w-full items-center justify-between'):
                                ui.label(f'Request #{request_id}').classes('text-lg font-bold')
                                ui.badge(status, color=status_colors.get(status, 'gray'))
                            
                            ui.label(f'Service: {req.get("service_name")}').classes('text-gray-600')
                            ui.label(f'Customer: {req.get("customer_name")}').classes('text-gray-600')
                            ui.label(f'Location: {req.get("location")}').classes('text-gray-600')
                            ui.label(f'Issue: {req.get("issue")}').classes('text-gray-600')
                            ui.label(f'Time: {req.get("created_at")}').classes('text-gray-500 text-sm')
                            
                            # Action buttons based on status
                            with ui.row().classes('w-full gap-2 mt-2'):
                                if status == 'pending':
                                    async def accept_request(r=req):
                                        """Accept a pending request."""
                                        ui.notify(f'Accepted request #{r.get("id")}', color='positive')
                                        await load_queue()
                                    
                                    async def reject_request(r=req):
                                        """Reject a request."""
                                        ui.notify(f'Rejected request #{r.get("id")}', color='negative')
                                        await load_queue()
                                    
                                    ui.button('Accept', on_click=accept_request).props('color=positive')
                                    ui.button('Reject', on_click=reject_request).props('color=negative outline')
                                
                                elif status == 'accepted':
                                    async def start_service(r=req):
                                        """Start servicing the request."""
                                        ui.notify(f'Started service for request #{r.get("id")}', color='info')
                                        await load_queue()
                                    
                                    ui.button('Start Service', on_click=start_service).props('color=blue')
                                
                                elif status == 'in_progress':
                                    async def complete_request(r=req):
                                        """Mark request as completed."""
                                        ui.notify(f'Completed request #{r.get("id")}', color='positive')
                                        await load_queue()
                                    
                                    ui.button('Complete', on_click=complete_request).props('color=green')
            
            # Initial load
            ui.timer(1.0, load_queue, once=True)

