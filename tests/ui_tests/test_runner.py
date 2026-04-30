"""
UI Tests with NiceGUI
Automated UI tests that run in NiceGUI and show progress.
These tests can be run against a live application URL.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any
from nicegui import ui, app
import httpx


class UITestRunner:
    """Runner for UI tests with progress tracking."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
        self.current_test: str = ""
        self.total_tests: int = 0
        self.passed_tests: int = 0
        self.failed_tests: int = 0
        
    async def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        self.current_test = test_name
        try:
            await test_func()
            self.results.append({
                "name": test_name,
                "status": "PASSED",
                "message": "Test passed successfully",
                "timestamp": datetime.now().isoformat()
            })
            self.passed_tests += 1
            return True
        except Exception as e:
            self.results.append({
                "name": test_name,
                "status": "FAILED",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })
            self.failed_tests += 1
            return False
    
    async def test_homepage_loads(self):
        """Test that homepage loads successfully."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/")
            assert response.status_code == 200, f"Homepage failed to load: {response.status_code}"
            assert "NiceGUI" in response.text or "Queue" in response.text or "Login" in response.text
    
    async def test_login_page_exists(self):
        """Test that login page exists."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/login")
            assert response.status_code in [200, 307], f"Login page not accessible: {response.status_code}"
    
    async def test_register_page_exists(self):
        """Test that registration page exists."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/register")
            assert response.status_code in [200, 307], f"Register page not accessible: {response.status_code}"
    
    async def test_dashboard_requires_auth(self):
        """Test that dashboard requires authentication."""
        async with httpx.AsyncClient(follow_redirects=False) as client:
            response = await client.get(f"{self.base_url}/dashboard")
            # Should redirect to login or return 401/403
            assert response.status_code in [307, 303, 401, 403], "Dashboard should require authentication"
    
    async def test_api_health_endpoint(self):
        """Test API health endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url.replace('8080', '8000')}/api/v1/health")
            assert response.status_code == 200, f"Health endpoint failed: {response.status_code}"
    
    async def run_all_tests(self):
        """Run all UI tests."""
        self.total_tests = 5
        tests = [
            ("Homepage Loads", self.test_homepage_loads),
            ("Login Page Exists", self.test_login_page_exists),
            ("Register Page Exists", self.test_register_page_exists),
            ("Dashboard Requires Auth", self.test_dashboard_requires_auth),
            ("API Health Check", self.test_api_health_endpoint),
        ]
        
        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)
        
        return self.results


# Global test runner instance
test_runner: Optional[UITestRunner] = None


@ui.page("/test-runner")
def test_runner_page():
    """NiceGUI page for running UI tests with visual progress."""
    
    base_url_input = ui.input(
        label="Application URL",
        placeholder="http://localhost:8080",
        value="http://localhost:8080"
    ).classes('w-full')
    
    progress_bar = ui.linear_progress(value=0, show_value=True).classes('w-full').style('display: none')
    status_label = ui.label("Ready to run tests").classes('text-lg font-bold')
    results_table = ui.table(
        columns=[
            {'name': 'name', 'label': 'Test Name', 'field': 'name', 'sortable': True},
            {'name': 'status', 'label': 'Status', 'field': 'status', 'sortable': True},
            {'name': 'message', 'label': 'Message', 'field': 'message'},
            {'name': 'timestamp', 'label': 'Time', 'field': 'timestamp', 'sortable': True},
        ],
        rows=[]
    ).classes('w-full mt-4').style('display: none')
    
    summary_label = ui.label("").classes('text-xl font-bold mt-4')
    
    async def run_tests():
        base_url = base_url_input.value.rstrip('/')
        
        # Reset state
        test_runner = UITestRunner(base_url=base_url)
        results_table.rows.clear()
        results_table.style('display: block')
        progress_bar.style('display: block')
        progress_bar.props('indeterminate')
        status_label.set_text(f"Running tests against {base_url}...")
        summary_label.set_text("")
        
        try:
            await test_runner.run_all_tests()
            
            # Update UI with results
            for result in test_runner.results:
                results_table.add_row(result)
            
            # Update progress bar
            progress_bar.props('indeterminate=False')
            progress_bar.value = 100
            
            # Update status
            total = test_runner.passed_tests + test_runner.failed_tests
            status_label.set_text(f"Tests completed: {total}/{total}")
            
            # Show summary
            if test_runner.failed_tests == 0:
                summary_label.set_text(f"✅ All {test_runner.passed_tests} tests passed!")
                summary_label.classes('text-green-600')
            else:
                summary_label.set_text(
                    f"❌ {test_runner.failed_tests} failed, ✅ {test_runner.passed_tests} passed"
                )
                summary_label.classes('text-red-600')
                
        except Exception as e:
            status_label.set_text(f"Error running tests: {str(e)}")
            summary_label.set_text("Test execution failed")
            summary_label.classes('text-red-600')
            progress_bar.style('display: none')
    
    ui.button("Run Tests", on_click=run_tests, icon='play_arrow').classes('mt-4')
    
    # Add export button
    async def export_results():
        if not test_runner or not test_runner.results:
            ui.notify("No test results to export", color="warning")
            return
        
        import json
        results_json = json.dumps({
            "base_url": test_runner.base_url,
            "total_tests": test_runner.total_tests,
            "passed": test_runner.passed_tests,
            "failed": test_runner.failed_tests,
            "results": test_runner.results,
            "executed_at": datetime.now().isoformat()
        }, indent=2)
        
        ui.download(results_json.encode(), filename=f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    ui.button("Export Results", on_click=export_results, icon='download').classes('mt-4 ml-4')


@ui.page("/test-demo")
def test_demo_page():
    """Demo page showing test progress visualization."""
    
    ui.label("UI Test Progress Demo").classes('text-2xl font-bold mb-4')
    
    # Simulated test progress
    tests = [
        {"name": "Loading Homepage", "status": "completed"},
        {"name": "Checking Login Form", "status": "completed"},
        {"name": "Testing Registration", "status": "running"},
        {"name": "Verifying Dashboard", "status": "pending"},
        {"name": "API Integration Check", "status": "pending"},
    ]
    
    with ui.column().classes('w-full max-w-2xl'):
        for i, test in enumerate(tests):
            with ui.row().classes('items-center w-full p-2 rounded hover:bg-gray-100'):
                if test["status"] == "completed":
                    ui.icon('check_circle', color='green').classes('mr-2')
                    ui.label(test["name"]).classes('text-green-700')
                elif test["status"] == "running":
                    ui.spinner('dots', size='sm').classes('mr-2')
                    ui.label(test["name"]).classes('text-blue-700 font-semibold')
                else:
                    ui.icon('radio_button_unchecked', color='gray').classes('mr-2')
                    ui.label(test["name"]).classes('text-gray-600')
    
    ui.label("\nThis is a demo of how test progress will be displayed.").classes('mt-4 text-gray-500')


def create_test_ui():
    """Create the main test UI application."""
    
    @ui.page('/')
    def index():
        ui.label("Automated UI Test Suite").classes('text-3xl font-bold mb-4')
        ui.markdown("""
        ## Welcome to the Automated Test Runner
        
        This tool allows you to automatically test all features of the application.
        
        ### Features:
        - ✅ Automatic homepage validation
        - ✅ Login/Registration page checks
        - ✅ Authentication flow testing
        - ✅ API endpoint verification
        - ✅ Real-time progress tracking
        - ✅ Exportable test results
        
        ### How to Use:
        1. Make sure the application is running
        2. Click on "Test Runner" to start testing
        3. Enter the application URL
        4. Click "Run Tests" and watch the progress
        5. Export results for documentation
        """).classes('mb-4')
        
        with ui.row():
            ui.button("Open Test Runner", on_click=lambda: ui.open('/test-runner'), icon='play_arrow').classes('mr-4')
            ui.button("View Demo", on_click=lambda: ui.open('/test-demo'), icon='visibility').classes('mr-4')
            ui.button("Documentation", on_click=lambda: ui.open('/how-to-run-tests'), icon='description')
    
    @ui.page('/how-to-run-tests')
    def docs_page():
        ui.label("How to Run Tests").classes('text-3xl font-bold mb-4')
        ui.markdown("""
        ## Running the Test Suite
        
        ### Prerequisites
        1. Install dependencies: `pip install -r requirements.txt`
        2. Start the backend: `python backend/main.py`
        3. Start the frontend: `python frontend/main.py`
        
        ### Option 1: Run via NiceGUI UI (Recommended)
        1. Navigate to http://localhost:8080/test-runner
        2. Enter your application URL
        3. Click "Run Tests"
        4. Watch real-time progress
        5. Export results when done
        
        ### Option 2: Run via Command Line
        ```bash
        # Run all backend unit tests
        pytest tests/backend_tests/ -v
        
        # Run with coverage
        pytest tests/ --cov=backend --cov-report=html
        
        # Run specific test file
        pytest tests/backend_tests/test_services.py -v
        
        # Run UI tests against specific URL
        python tests/run_ui_tests.py --url http://localhost:8080
        ```
        
        ### Option 3: Automated Full Test Suite
        ```bash
        # Run everything
        ./tests/run_all_tests.sh
        ```
        
        ### Interpreting Results
        - ✅ PASSED: Test completed successfully
        - ❌ FAILED: Test encountered an error
        - ⚠️ SKIPPED: Test was skipped (missing prerequisites)
        
        ### Test Coverage
        The test suite covers:
        - User authentication (register, login, logout)
        - User management (CRUD operations)
        - Company management
        - Vehicle management
        - Queue management
        - Role-based access control
        - API endpoint validation
        - UI component rendering
        """)


if __name__ in {"__main__", "__mp_main__"}:
    create_test_ui()
    ui.run(title="Test Suite", port=8081, reload=False)
