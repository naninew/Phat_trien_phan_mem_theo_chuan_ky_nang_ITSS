import pytest
import sys
import os
from pathlib import Path

def run_backend_tests():
    print("====================================================")
    print("DANG CHAY BO KIEM THU BACKEND API TU DONG...")
    print("====================================================")
    
    # Đảm bảo thư mục backend có trong sys.path để import 'app.x' hoạt động
    backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    # Cấu hình tham số pytest
    args = [
        "tests/backend_tests/test_api.py",
        "-v",
        "--tb=short",
        "-p", "no:warnings"
    ]
    
    # Chạy pytest
    exit_code = pytest.main(args)
    
    print("\n====================================================")
    if exit_code == 0:
        print("PASS: TAT CA CAC KIEM THU DA VUOT QUA THANH CONG!")
    else:
        print("FAIL: CO MOT SO KIEM THU THAT BAI. VUI LONG KIEM TRA LAI.")
    print("====================================================")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    run_backend_tests()
