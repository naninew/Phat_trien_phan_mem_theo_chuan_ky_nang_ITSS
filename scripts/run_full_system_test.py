import subprocess
import time
import sys
import os
import signal
from pathlib import Path

def run_command(command, cwd=None, name="Process", log_file=None):
    print(f"Starting {name}...")
    stdout = open(log_file, 'w') if log_file else subprocess.PIPE
    stderr = subprocess.STDOUT if log_file else subprocess.PIPE
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=stdout,
        stderr=stderr,
        shell=True,
        text=True
    )
    return process

def main():
    root_dir = Path(__file__).parent.parent.absolute()
    logs_dir = root_dir / "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # 1. Start Backend
    backend_proc = run_command(
        f"{sys.executable} -m uvicorn app.main:app --port 8000",
        cwd=root_dir / "backend",
        name="Backend",
        log_file=logs_dir / "backend.log"
    )
    
    # 2. Start Frontend
    frontend_proc = run_command(
        f"{sys.executable} frontend/main.py",
        cwd=root_dir,
        name="Frontend",
        log_file=logs_dir / "frontend.log"
    )
    
    print("Waiting for services to start (20s)...")
    time.sleep(20) # Give them more time
    
    # 3. Run Tests
    print("\n" + "="*50)
    print("RUNNING COMPREHENSIVE UI TESTS")
    print("="*50 + "\n")
    
    try:
        test_result = subprocess.run(
            [sys.executable, "tests/ui_tests/run_ui_tests.py", "--url", "http://localhost:8080"],
            cwd=root_dir,
            check=False
        )
        exit_code = test_result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        exit_code = 1
    
    # 4. Cleanup
    print("\nShutting down services...")
    if os.name == 'nt':
        subprocess.run(f"taskkill /F /T /PID {backend_proc.pid}", shell=True, stderr=subprocess.DEVNULL)
        subprocess.run(f"taskkill /F /T /PID {frontend_proc.pid}", shell=True, stderr=subprocess.DEVNULL)
    else:
        os.killpg(os.getpgid(backend_proc.pid), signal.SIGTERM)
        os.killpg(os.getpgid(frontend_proc.pid), signal.SIGTERM)
    
    print(f"Done. Exit code: {exit_code}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
