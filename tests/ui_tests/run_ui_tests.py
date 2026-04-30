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
import json
from datetime import datetime
from typing import List, Dict, Any
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn


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
                "message": "✓",
                "timestamp": datetime.now().isoformat()
            })
            self.passed += 1
            return True
        except Exception as e:
            self.results.append({
                "name": test_name,
                "status": "FAILED",
                "message": f"✗ {str(e)}",
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
        tests = [
            ("Homepage Loads", self.test_homepage_loads),
            ("Login Page Exists", self.test_login_page_exists),
            ("Register Page Exists", self.test_register_page_exists),
            ("Dashboard Requires Auth", self.test_dashboard_requires_auth),
            ("API Health Check", self.test_api_health_endpoint),
            ("Navbar Component", self.test_navbar_component),
            ("Static Assets Load", self.test_static_assets_load),
        ]
        
        console.print(f"\n[bold blue]Running UI Tests against {self.base_url}[/bold blue]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Running tests...", total=len(tests))
            
            for test_name, test_func in tests:
                progress.update(task, description=f"Testing: {test_name}")
                await self.run_test(test_name, test_func)
                progress.advance(task)
        
        return self.results
    
    def print_summary(self):
        """Print test results summary."""
        total = self.passed + self.failed + self.skipped
        
        console.print("\n[bold]Test Results Summary[/bold]\n")
        
        table = Table(title="Test Results")
        table.add_column("Status", style="cyan", no_wrap=True)
        table.add_column("Test Name", style="magenta")
        table.add_column("Details", style="green")
        table.add_column("Time", style="blue")
        
        for result in self.results:
            status_style = "green" if result["status"] == "PASSED" else "red"
            status_icon = "✓" if result["status"] == "PASSED" else "✗"
            table.add_row(
                f"[{status_style}]{status_icon} {result['status']}[/{status_style}]",
                result["name"],
                result["message"][:50] + "..." if len(result["message"]) > 50 else result["message"],
                result["timestamp"].split("T")[1].split(".")[0]
            )
        
        console.print(table)
        
        # Summary stats
        console.print("\n[bold]Statistics:[/bold]")
        console.print(f"  Total Tests: {total}")
        console.print(f"  [green]Passed: {self.passed}[/green]")
        console.print(f"  [red]Failed: {self.failed}[/red]")
        if self.skipped > 0:
            console.print(f"  [yellow]Skipped: {self.skipped}[/yellow]")
        
        success_rate = (self.passed / total * 100) if total > 0 else 0
        console.print(f"\n  Success Rate: {success_rate:.1f}%")
        
        if self.failed == 0:
            console.print("\n[bold green]✅ All tests passed![/bold green]")
            return 0
        else:
            console.print(f"\n[bold red]❌ {self.failed} test(s) failed[/bold red]")
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
