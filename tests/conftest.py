import sys
import os
from pathlib import Path

# Add backend and tests to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(root_dir / "tests"))

# Import fixtures to make them available to all tests
from fixtures import (
    test_engine,
    db_session,
    override_get_db,
    test_admin,
    test_customer,
    test_company_staff,
    test_company,
    test_service,
    test_vehicle,
    test_rescue_staff
)
