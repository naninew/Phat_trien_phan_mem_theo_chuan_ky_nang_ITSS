#!/usr/bin/env python3
"""
Entry point script to run the NiceGUI frontend.
Usage: python -m frontend.run
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from frontend.main import run_frontend

if __name__ == "__main__":
    run_frontend(host="0.0.0.0", port=8080, reload=True)
