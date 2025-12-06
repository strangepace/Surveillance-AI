#!/usr/bin/env python3
"""
Start backend server and log monitor together.
This is a cross-platform solution that works reliably.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    """Start backend server and log monitor."""
    # Get backend directory
    backend_dir = Path(__file__).parent.absolute()
    log_monitor_script = backend_dir / "scripts" / "watch_cached_analysis_logs.py"
    start_backend_script = backend_dir / "start_backend.py"
    
    print("=" * 60)
    print("Starting Backend Server + Log Monitor")
    print("=" * 60)
    print()
    print("Terminal 1: Backend server (this window)")
    print("Terminal 2: Log monitor (will open automatically)")
    print()
    print("Press Ctrl+C in this window to stop the server")
    print("Press Ctrl+C in the log monitor window to stop monitoring")
    print()
    print("Starting log monitor in new window...")
    print()
    
    # Start log monitor in new window
    if sys.platform == "win32":
        # Windows: Use start command
        subprocess.Popen(
            ["start", "cmd", "/k", f"python {log_monitor_script}"],
            shell=True,
            cwd=str(backend_dir)
        )
    else:
        # Linux/Mac: Use xterm or gnome-terminal
        try:
            subprocess.Popen(
                ["gnome-terminal", "--", "python3", str(log_monitor_script)],
                cwd=str(backend_dir)
            )
        except:
            try:
                subprocess.Popen(
                    ["xterm", "-e", f"python3 {log_monitor_script}"],
                    cwd=str(backend_dir)
                )
            except:
                print("⚠️  Could not open new terminal. Run log monitor manually:")
                print(f"   python {log_monitor_script}")
    
    # Small delay to let log monitor window open
    time.sleep(1)
    
    print("Starting backend server...")
    print("=" * 60)
    print()
    
    # Start backend server in current window
    os.chdir(backend_dir)
    subprocess.run([sys.executable, str(start_backend_script)])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
        sys.exit(0)

