#!/usr/bin/env python3
"""
Command-line UI Test Runner
Run automated tests against a live application URL.

Usage:
    python run_ui_tests.py --url http://localhost:8080
    python run_ui_tests.py --url http://localhost:8080 --verbose
    python run_ui_tests.py --help
"""

import asyncio
import argparse
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any
import httpx
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).parent.parent.parent.absolute()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
class Console:
    def print(self, *args, **kwargs):
        print(*args, **kwargs)

console = Console()


class CommandLineUITestRunner:
    """Command-line runner for UI tests with rich progress display."""
    
    def __init__(self, base_url: str, verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        
    async def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and display results."""
        try:
            await test_func()
            self.results.append({
                "name": test_name,
                "status": "PASSED",
                "message": "PASSED",
                "timestamp": datetime.now().isoformat()
            })
            self.passed += 1
            return True
        except Exception as e:
            self.results.append({
                "name": test_name,
                "status": "FAILED",
                "message": f"FAILED: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            self.failed += 1
            if self.verbose:
                console.print(f"  [red]Error:[/red] {str(e)}")
            return False
    
    async def test_homepage_loads(self):
        """Test that homepage loads successfully."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/")
            assert response.status_code == 200, f"Status code: {response.status_code}"
    
    async def test_login_page_exists(self):
        """Test that login page exists."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/login")
            assert response.status_code in [200, 307, 303], f"Status code: {response.status_code}"
    
    async def test_register_page_exists(self):
        """Test that registration page exists."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/register")
            assert response.status_code in [200, 307, 303], f"Status code: {response.status_code}"
    
    async def test_dashboard_requires_auth(self):
        """Test that dashboard requires authentication."""
        async with httpx.AsyncClient(follow_redirects=False) as client:
            response = await client.get(f"{self.base_url}/dashboard")
            assert response.status_code in [307, 303, 401, 403], \
                f"Dashboard should require auth, got: {response.status_code}"
    
    async def test_api_health_endpoint(self):
        """Test API health endpoint."""
        api_url = self.base_url.replace('8080', '8000')
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/api/v1/health")
            assert response.status_code == 200, f"Status code: {response.status_code}"
    
    async def test_navbar_component(self):
        """Test navbar component rendering."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/")
            assert response.status_code == 200
            # Check for common navbar elements
            content = response.text.lower()
            assert any(keyword in content for keyword in ['login', 'home', 'nav', 'menu']), \
                "Navbar components not found"
    
    async def test_static_assets_load(self):
        """Test that static assets load properly."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/_nicegui/")
            # Should either load or redirect, but not 404
            assert response.status_code != 404, "Static assets not found"
    
    async def run_all_tests(self):
        """Run all UI tests with progress display."""
        try:
            from tests.ui_tests.test_all_features import ALL_UI_TESTS
        except ImportError:
            # Fallback if import fails
            ALL_UI_TESTS = [
                ("Homepage Loads", lambda url: self.test_homepage_loads()),
                ("Login Page Exists", lambda url: self.test_login_page_exists()),
                ("Register Page Exists", lambda url: self.test_register_page_exists()),
                ("Dashboard Requires Auth", lambda url: self.test_dashboard_requires_auth()),
                ("API Health Check", lambda url: self.test_api_health_endpoint()),
                ("Navbar Component", lambda url: self.test_navbar_component()),
                ("Static Assets Load", lambda url: self.test_static_assets_load()),
            ]
        
        console.print(f"\nRunning UI Tests against {self.base_url}\n")
        
        for test_name, test_func in ALL_UI_TESTS:
            console.print(f"Testing: {test_name}...")
            # Adapt for different function signatures if necessary
            try:
                import inspect
                if inspect.iscoroutinefunction(test_func):
                    if len(inspect.signature(test_func).parameters) > 0:
                        await self.run_test(test_name, lambda f=test_func, u=self.base_url: f(u))
                    else:
                        await self.run_test(test_name, test_func)
                else:
                    await self.run_test(test_name, test_func)
            except Exception as e:
                self.results.append({
                    "name": test_name,
                    "status": "FAILED",
                    "message": f"Setup error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
                self.failed += 1
        
        return self.results
    
    def print_summary(self):
        """Print test results summary."""
        total = self.passed + self.failed + self.skipped
        
        console.print("\nTest Results Summary\n")
        
        print(f"{'Status':<15} | {'Test Name':<30} | {'Details':<30}")
        print("-" * 80)
        
        for result in self.results:
            status = result["status"]
            name = result["name"]
            message = result["message"][:50] + "..." if len(result["message"]) > 50 else result["message"]
            print(f"{status:<15} | {name:<30} | {message:<30}")
        
        # Summary stats
        console.print("\nStatistics:")
        console.print(f"  Total Tests: {total}")
        console.print(f"  Passed: {self.passed}")
        console.print(f"  Failed: {self.failed}")
        if self.skipped > 0:
            console.print(f"  [yellow]Skipped: {self.skipped}[/yellow]")
        
        success_rate = (self.passed / total * 100) if total > 0 else 0
        console.print(f"\n  Success Rate: {success_rate:.1f}%")
        
        if self.failed == 0:
            console.print("\nAll tests passed!")
            return 0
        else:
            console.print(f"\n{self.failed} test(s) failed")
            return 1
    
    def export_results(self, filename: str = None):
        """Export test results to JSON file."""
        if not filename:
            filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        results_data = {
            "base_url": self.base_url,
            "executed_at": datetime.now().isoformat(),
            "summary": {
                "total": self.passed + self.failed + self.skipped,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "success_rate": (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0
            },
            "results": self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        console.print(f"\nResults exported to: [bold]{filename}[/bold]")
        return filename


async def main():
    parser = argparse.ArgumentParser(description="Run UI tests against a live application")
    parser.add_argument("--url", type=str, default="http://localhost:8080",
                        help="Base URL of the application to test")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed error messages")
    parser.add_argument("--export", "-e", type=str, nargs='?', const='auto',
                        help="Export results to JSON file")
    
    args = parser.parse_args()
    
    runner = CommandLineUITestRunner(base_url=args.url, verbose=args.verbose)
    await runner.run_all_tests()
    exit_code = runner.print_summary()
    
    if args.export:
        filename = args.export if args.export != 'auto' else None
        runner.export_results(filename)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
