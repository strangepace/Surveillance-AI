"""
Live Log Monitor for Cached Re-Analysis Testing

Monitors backend logs in real-time and filters for:
- Cached re-analysis messages
- FAISS index operations
- Analysis progress
- Errors and warnings

Usage:
    cd backend
    python scripts/watch_cached_analysis_logs.py
"""

import os
import sys
import time
import re
from pathlib import Path
from datetime import datetime

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

# Keywords to highlight
KEYWORDS = {
    'cached': Colors.CYAN + Colors.BOLD,
    'FAISS': Colors.MAGENTA + Colors.BOLD,
    'index': Colors.MAGENTA,
    're-analysis': Colors.CYAN + Colors.BOLD,
    'Skipping full pipeline': Colors.GREEN + Colors.BOLD,
    'Loaded FAISS index': Colors.GREEN + Colors.BOLD,
    'CACHED RE-ANALYSIS MODE': Colors.CYAN + Colors.BOLD,
    '✅': Colors.GREEN,
    '⚠️': Colors.YELLOW,
    '❌': Colors.RED,
    'ERROR': Colors.RED + Colors.BOLD,
    'WARNING': Colors.YELLOW + Colors.BOLD,
    'Step': Colors.BLUE,
    'Match at': Colors.GREEN,
    'Analysis complete': Colors.GREEN + Colors.BOLD,
}

def get_latest_log_file(logs_dir: str) -> str:
    """Get the most recent log file."""
    log_files = list(Path(logs_dir).glob("backend_*.log"))
    if not log_files:
        return None
    return str(max(log_files, key=lambda p: p.stat().st_mtime))

def highlight_keywords(line: str) -> str:
    """Highlight keywords in log line."""
    highlighted = line
    for keyword, color in KEYWORDS.items():
        if keyword.lower() in line.lower():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            highlighted = pattern.sub(
                f"{color}{keyword}{Colors.RESET}",
                highlighted
            )
    return highlighted

def should_show_line(line: str) -> bool:
    """Filter lines to show only relevant ones."""
    line_lower = line.lower()
    
    # Always show errors and warnings
    if 'error' in line_lower or 'warning' in line_lower or '❌' in line or '⚠️' in line:
        return True
    
    # Show cached re-analysis related messages
    cached_keywords = [
        'cached',
        'faiss',
        're-analysis',
        'skipping full pipeline',
        'loaded faiss index',
        'cached re-analysis mode',
        'step 1:',
        'step 2:',
        'step 3:',
        'step 4:',
        'step 5:',
        'step 6:',
        'match at',
        'analysis complete',
        'media_id',
        'video id',
    ]
    
    if any(keyword in line_lower for keyword in cached_keywords):
        return True
    
    # Show analysis start/end
    if 'starting video analysis' in line_lower or 'analysis complete' in line_lower:
        return True
    
    return False

def watch_log_file(log_file: str):
    """Watch log file and print filtered lines."""
    if not os.path.exists(log_file):
        print(f"{Colors.RED}Log file not found: {log_file}{Colors.RESET}")
        return
    
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}Watching: {log_file}{Colors.RESET}")
    print(f"{Colors.BOLD}Filtering for: Cached Re-Analysis, FAISS, Analysis Progress{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")
    
    # Read from end of file
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        # Go to end of file
        f.seek(0, 2)
        
        try:
            while True:
                line = f.readline()
                if line:
                    line = line.rstrip()
                    if should_show_line(line):
                        highlighted = highlight_keywords(line)
                        print(highlighted)
                else:
                    time.sleep(0.1)  # Small delay when no new lines
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Stopped watching logs.{Colors.RESET}")

def main():
    """Main entry point."""
    # Get backend directory
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    logs_dir = backend_dir / "logs"
    
    if not logs_dir.exists():
        print(f"{Colors.RED}Logs directory not found: {logs_dir}{Colors.RESET}")
        sys.exit(1)
    
    # Get latest log file
    latest_log = get_latest_log_file(str(logs_dir))
    
    if not latest_log:
        print(f"{Colors.YELLOW}No log files found in {logs_dir}{Colors.RESET}")
        sys.exit(1)
    
    print(f"{Colors.BLUE}Latest log file: {latest_log}{Colors.RESET}")
    print(f"{Colors.BLUE}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}\n")
    
    try:
        watch_log_file(latest_log)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Monitoring stopped by user.{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()

