# Tests Package
"""
Test Suite for Queue Management System

This package contains all automated tests for the project:
- Backend unit tests (services, models)
- API integration tests (FastAPI endpoints)
- UI automated tests (NiceGUI)

Directory Structure:
├── fixtures/          # Shared test fixtures and utilities
├── backend_tests/     # Backend unit and API tests
├── ui_tests/          # UI automated tests with NiceGUI
└── run_all_tests.sh   # Master script to run all tests

Quick Start:
    # Run all tests
    ./tests/run_all_tests.sh
    
    # Run backend tests only
    pytest tests/backend_tests/ -v
    
    # Run UI tests against live app
    python tests/ui_tests/run_ui_tests.py --url http://localhost:8080

For detailed documentation, see HOW_TO_RUN_TEST.md in project root.
"""

__version__ = "1.0.0"
