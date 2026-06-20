#!/usr/bin/env python3
"""
Entry point script to run the NiceGUI frontend.
Usage: python -m frontend.run
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import setup_app

if __name__ in {"__main__", "__mp_main__"}:
    setup_app()
