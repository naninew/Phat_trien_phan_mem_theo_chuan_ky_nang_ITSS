"""
Find rescue page for customers to request help.
"""
from nicegui import ui
from typing import Optional, Dict, Any, List
from frontend.core.auth import require_auth, get_current_user, get_access_token
from frontend.components.navbar import create_navbar
from frontend.services.rescue_api import find_nearby_companies, create_rescue_request


def create_find_rescue_page():
    """Create find rescue page with NiceGUI components."""
    
    @ui.page('/customer/find-rescue')
    def find_rescue_page():
        # Require authentication
        if not require_auth():
            return
        
        create_navbar("Find Rescue")
        
        with ui.column().classes('w-full p-8'):
            ui.label('Request Rescue Service').classes('text-2xl font-bold mb-4')
            
            # Form section
            with ui.card().classes('w-full max-w-2xl'):
                # Location inputs
                ui.label('Location Information').classes('text-lg font-semibold mt-4')
                
                latitude = ui.number(label='Latitude', value=21.0285, format='%.6f').classes('w-full')
                longitude = ui.number(label='Longitude', value=105.8542, format='%.6f').classes('w-full')
                address_desc = ui.textarea(label='Address Description', placeholder='Describe your location (e.g., near landmark, street name)').classes('w-full')
                
                # Service selection
                ui.label('Service Information').classes('text-lg font-semibold mt-4')
                
                service_options = {
                    1: 'Tire Change/Repair',
                    2: 'Battery Jump-Start',
                    3: 'Fuel Delivery',
                    4: 'Towing Service',
                    5: 'Emergency Repair',
                }
                service_id = ui.select(
                    options=service_options,
                    label='Select Service',
                    value=None
                ).classes('w-full')
                
                # Vehicle issue details
                car_issue = ui.textarea(
                    label='Vehicle Issue Details',
                    placeholder='Describe the problem with your vehicle...',
                    rows=3
                ).classes('w-full')
                
                # Payment method
                payment_method = ui.select(
                    options=['cash', 'card', 'momo', 'banking'],
                    label='Payment Method',
                    value='cash'
                ).classes('w-full')
                
                # Status and results
                status_label = ui.label('').classes('text-gray-600 mt-4')
                error_label = ui.label('').classes('text-red-500 mt-2')
                
                # Companies list display
                companies_container = ui.column().classes('w-full mt-4')
                
                async def search_companies():
                    """Search for nearby rescue companies."""
                    if not service_id.value:
                        error_label.set_text('Please select a service')
                        return
                    
                    status_label.set_text('Searching for nearby companies...')
                    error_label.set_text('')
                    
                    try:
                        companies = await find_nearby_companies(
                            latitude=latitude.value,
                            longitude=longitude.value,
                            service_id=int(service_id.value),
                            radius_km=50.0,
                        )
                        
                        status_label.set_text(f'Found {len(companies)} companies')
                        
                        # Display companies
                        with companies_container:
                            companies_container.clear()
                            if companies:
                                for company in companies:
                                    with ui.card().classes('w-full p-4'):
                                        ui.label(company.get('company_name', 'Unknown')).classes('text-lg font-bold')
                                        ui.label(f"Phone: {company.get('hotline', 'N/A')}").classes('text-gray-600')
                                        ui.label(f"Rating: {company.get('rating_avg', 'N/A')} ⭐").classes('text-yellow-600')
                                        ui.label(f"Distance: {company.get('distance_km', 'N/A')} km").classes('text-gray-500')
                                        
                                        async def select_company(c=company):
                                            """Handle company selection."""
                                            await submit_request(c.get('id'))
                                        
                                        ui.button('Select This Company', on_click=select_company).classes('mt-2')
                            else:
                                ui.label('No companies found in your area').classes('text-gray-500')
                    
                    except Exception as e:
                        error_label.set_text(f'Search failed: {str(e)}')
                        status_label.set_text('')
                
                async def submit_request(company_id: Optional[int] = None):
                    """Submit rescue request."""
                    if not service_id.value or not car_issue.value:
                        error_label.set_text('Please fill in all required fields')
                        return
                    
                    token = get_access_token()
                    
                    try:
                        result = await create_rescue_request(
                            service_id=int(service_id.value),
                            latitude=latitude.value,
                            longitude=longitude.value,
                            address_description=address_desc.value or 'No description',
                            car_issue_detail=car_issue.value,
                            payment_method=payment_method.value,
                            token=token,
                        )
                        
                        ui.notify('Rescue request submitted successfully!', color='positive')
                        ui.navigate.to('/customer/requests')
                    
                    except Exception as e:
                        error_label.set_text(f'Request failed: {str(e)}')
                
                with ui.row().classes('w-full gap-4 mt-4'):
                    ui.button('Search Companies', on_click=search_companies).classes('flex-1')
                    ui.button('Submit Request', on_click=lambda: submit_request()).classes('flex-1', color='primary')

