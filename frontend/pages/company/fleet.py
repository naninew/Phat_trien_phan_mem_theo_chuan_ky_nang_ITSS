"""
Company fleet management page for NiceGUI frontend.
"""
from nicegui import ui
from typing import Optional, Dict, Any, List
from ..core.auth import require_auth, get_current_user, get_access_token, get_user_role
from ..components.navbar import create_navbar


def create_fleet_page():
    """Create company fleet management page with NiceGUI components."""
    
    @ui.page('/company/fleet')
    def fleet_page():
        # Require authentication
        if not require_auth():
            return
        
        create_navbar("Fleet Management")
        
        with ui.column().classes('w-full p-8'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('Vehicle Fleet').classes('text-2xl font-bold')
                ui.button('Add Vehicle', on_click=lambda: show_add_vehicle_dialog()).props('color=primary')
            
            # Vehicles container
            vehicles_container = ui.column().classes('w-full mt-4')
            
            # Vehicle types
            vehicle_types = {
                'tow_truck': 'Tow Truck',
                'flatbed': 'Flatbed Truck',
                'service_van': 'Service Van',
                'motorcycle': 'Motorcycle',
                'battery_truck': 'Battery Service Truck',
            }
            
            # Status colors
            status_colors = {
                'available': 'green',
                'busy': 'orange',
                'maintenance': 'red',
                'offline': 'gray',
            }
            
            async def load_vehicles():
                """Load and display fleet vehicles."""
                token = get_access_token()
                
                with vehicles_container:
                    vehicles_container.clear()
                    
                    # Mock data for demonstration
                    mock_vehicles = [
                        {
                            'id': 1,
                            'license_plate': '51C-12345',
                            'vehicle_type': 'tow_truck',
                            'capacity': 'Up to 2 tons',
                            'status': 'available',
                            'driver_name': 'Le Van C',
                            'driver_phone': '0901234567',
                        },
                        {
                            'id': 2,
                            'license_plate': '51D-67890',
                            'vehicle_type': 'service_van',
                            'capacity': 'Tools & Parts',
                            'status': 'busy',
                            'driver_name': 'Pham Thi D',
                            'driver_phone': '0909876543',
                        },
                    ]
                    
                    if not mock_vehicles:
                        ui.label('No vehicles in fleet').classes('text-gray-500 p-4')
                        return
                    
                    for vehicle in mock_vehicles:
                        vehicle_id = vehicle.get('id')
                        status = vehicle.get('status', 'unknown')
                        
                        with ui.card().classes('w-full p-4 mb-4'):
                            with ui.row().classes('w-full items-center justify-between'):
                                ui.label(f'{vehicle.get("license_plate")}').classes('text-lg font-bold')
                                ui.badge(status, color=status_colors.get(status, 'gray'))
                            
                            ui.label(f'Type: {vehicle_types.get(vehicle.get("vehicle_type"), "Unknown")}').classes('text-gray-600')
                            ui.label(f'Capacity: {vehicle.get("capacity")}').classes('text-gray-600')
                            ui.label(f'Driver: {vehicle.get("driver_name")}').classes('text-gray-600')
                            ui.label(f'Phone: {vehicle.get("driver_phone")}').classes('text-gray-600')
                            
                            # Action buttons
                            with ui.row().classes('w-full gap-2 mt-2'):
                                async def edit_vehicle(v=vehicle):
                                    """Edit vehicle details."""
                                    ui.notify(f'Edit vehicle {v.get("license_plate")}', color='info')
                                
                                async def toggle_status(v=vehicle):
                                    """Toggle vehicle status."""
                                    new_status = 'busy' if v.get('status') == 'available' else 'available'
                                    ui.notify(f'Vehicle status changed to {new_status}', color='info')
                                    await load_vehicles()
                                
                                ui.button('Edit', on_click=edit_vehicle).props('outline')
                                ui.button('Toggle Status', on_click=toggle_status).props('outline')
            
            def show_add_vehicle_dialog():
                """Show dialog to add new vehicle."""
                with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-4'):
                    ui.label('Add New Vehicle').classes('text-xl font-bold mb-4')
                    
                    license_plate = ui.input(label='License Plate').classes('w-full')
                    vehicle_type = ui.select(
                        options=vehicle_types,
                        label='Vehicle Type',
                        value=None
                    ).classes('w-full')
                    capacity = ui.input(label='Capacity').classes('w-full')
                    driver_name = ui.input(label='Driver Name').classes('w-full')
                    driver_phone = ui.input(label='Driver Phone').classes('w-full')
                    
                    with ui.row().classes('w-full gap-2 mt-4'):
                        async def save_vehicle():
                            """Save new vehicle."""
                            if not all([license_plate.value, vehicle_type.value, driver_name.value]):
                                ui.notify('Please fill in required fields', color='negative')
                                return
                            
                            ui.notify(f'Vehicle {license_plate.value} added', color='positive')
                            dialog.close()
                            await load_vehicles()
                        
                        ui.button('Save', on_click=save_vehicle).props('color=positive')
                        ui.button('Cancel', on_click=dialog.close).props('outline')
                
                dialog.open()
            
            # Initial load
            ui.timer(1.0, load_vehicles, once=True)

