#!/usr/bin/env python3
"""Test script for using Firebase emulators with SQL/CSV data.

This script:
1. Starts Firebase emulator
2. Loads data from SQLite/CSV into the emulator
3. Optionally starts backend API and frontend

Usage:
    python test_with_emulators.py [--no-backend] [--no-frontend] [--data-source sqlite|csv]
"""

import argparse
import os
import sys
import subprocess
import time
import signal
import atexit
from pathlib import Path
from typing import Optional

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_status(message: str, color: str = Colors.CYAN):
    """Print status message with color."""
    print(f"{color}{Colors.BOLD}▶ {message}{Colors.END}")

def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def check_command(command: str) -> bool:
    """Check if a command is available."""
    try:
        subprocess.run(
            [command, '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_prerequisites():
    """Check if required tools are installed."""
    print_status("Checking prerequisites...")
    
    missing = []
    
    if not check_command('firebase'):
        missing.append('firebase-tools (npm install -g firebase-tools)')
    
    if not check_command('python3'):
        missing.append('python3')
    
    if missing:
        print_error("Missing required tools:")
        for tool in missing:
            print(f"  - {tool}")
        return False
    
    print_success("All prerequisites met")
    return True

def check_data_files(data_dir: str = "data") -> dict:
    """Check if data files exist."""
    data_path = Path(data_dir)
    files = {
        'sqlite': data_path / "spendsense.db",
        'csv': {
            'users': data_path / "users.json",
            'accounts': data_path / "accounts.csv",
            'transactions': data_path / "transactions.csv",
        }
    }
    
    results = {
        'sqlite_exists': files['sqlite'].exists(),
        'csv_exists': all(f.exists() for f in files['csv'].values()),
        'sqlite_path': str(files['sqlite']),
        'csv_paths': {k: str(v) for k, v in files['csv'].items()}
    }
    
    return results

def start_firebase_emulator():
    """Start Firebase emulator."""
    print_status("Starting Firebase emulator...")
    
    # Check if firebase.json exists
    if not Path("firebase.json").exists():
        print_error("firebase.json not found. Please ensure Firebase is initialized.")
        return None
    
    try:
        # Start emulator in background
        process = subprocess.Popen(
            ['firebase', 'emulators:start'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for emulator to start
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print_success(f"Firebase emulator started (PID: {process.pid})")
            print(f"  Emulator UI: http://localhost:4000")
            print(f"  Firestore: localhost:8080")
            return process
        else:
            stdout, stderr = process.communicate()
            print_error("Failed to start Firebase emulator")
            print(stderr)
            return None
    except Exception as e:
        print_error(f"Failed to start Firebase emulator: {e}")
        return None

def load_data_to_emulator(data_source: str = "sqlite"):
    """Load data from SQLite or CSV into Firebase emulator."""
    print_status(f"Loading data from {data_source.upper()} into Firebase emulator...")
    
    # Note: Emulator will be auto-detected by firestore.py if running on port 8080
    # We can explicitly set it here for clarity, but it's not required anymore
    if not os.getenv('FIRESTORE_EMULATOR_HOST'):
        # Wait a moment for emulator to be fully ready
        time.sleep(2)
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    if data_source == "sqlite":
        # Check if SQLite database exists
        db_path = Path("data/spendsense.db")
        if not db_path.exists():
            print_error(f"SQLite database not found: {db_path}")
            print_warning("Would you like to load CSV data into SQLite first?")
            return False
        
        # Import push_from_sqlite module
        try:
            from src.ingest.push_from_sqlite import push_all_from_sqlite
            
            print("  Pushing data from SQLite to Firebase emulator...")
            results = push_all_from_sqlite(
                collections=None,  # Push all collections
                dry_run=False,
                batch_size=500,
                delay=0.1,
                max_retries=3
            )
            
            print_success(f"Loaded data into emulator:")
            for collection, count in results.items():
                print(f"  - {collection}: {count} documents")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to load data from SQLite: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    elif data_source == "csv":
        # First load CSV into SQLite, then push to emulator
        print("  Step 1: Loading CSV data into SQLite...")
        try:
            from src.ingest.data_loader import load_data_to_db
            
            load_data_to_db(data_dir="data")
            print_success("CSV data loaded into SQLite")
            
            # Now push from SQLite to emulator
            print("  Step 2: Pushing SQLite data to Firebase emulator...")
            from src.ingest.push_from_sqlite import push_all_from_sqlite
            
            results = push_all_from_sqlite(
                collections=None,
                dry_run=False,
                batch_size=500,
                delay=0.1,
                max_retries=3
            )
            
            print_success(f"Loaded data into emulator:")
            for collection, count in results.items():
                print(f"  - {collection}: {count} documents")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to load data from CSV: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    else:
        print_error(f"Unknown data source: {data_source}")
        return False

def start_backend_api():
    """Start the backend API server."""
    print_status("Starting backend API server...")
    
    # Note: Emulator will be auto-detected by firestore.py if running on port 8080
    # No need to set environment variables manually
    
    try:
        process = subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 'src.api.main:app', '--reload', '--port', '8000'],
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for server to start
        time.sleep(3)
        
        if process.poll() is None:
            print_success(f"Backend API started (PID: {process.pid})")
            print(f"  API: http://localhost:8000")
            print(f"  Docs: http://localhost:8000/docs")
            return process
        else:
            stdout, stderr = process.communicate()
            print_error("Failed to start backend API")
            print(stderr)
            return None
    except Exception as e:
        print_error(f"Failed to start backend API: {e}")
        return None

def start_frontend():
    """Start the frontend development server."""
    print_status("Starting frontend development server...")
    
    frontend_dir = Path("consumer_ui")
    if not frontend_dir.exists():
        print_error(f"Frontend directory not found: {frontend_dir}")
        return None
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print_warning("node_modules not found. Installing dependencies...")
        try:
            subprocess.run(
                ['npm', 'install'],
                cwd=frontend_dir,
                check=True
            )
            print_success("Dependencies installed")
        except subprocess.CalledProcessError:
            print_error("Failed to install dependencies")
            return None
    
    try:
        # Set API URL environment variable
        env = os.environ.copy()
        env['VITE_API_URL'] = 'http://localhost:8000'
        
        process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=frontend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for server to start
        time.sleep(5)
        
        if process.poll() is None:
            print_success(f"Frontend started (PID: {process.pid})")
            print(f"  Frontend: http://localhost:5173")
            return process
        else:
            stdout, stderr = process.communicate()
            print_error("Failed to start frontend")
            print(stderr)
            return None
    except Exception as e:
        print_error(f"Failed to start frontend: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Test SpendSense with Firebase emulators using SQL/CSV data"
    )
    parser.add_argument(
        '--data-source',
        choices=['sqlite', 'csv'],
        default='sqlite',
        help='Data source to use (default: sqlite)'
    )
    parser.add_argument(
        '--no-backend',
        action='store_true',
        help='Do not start backend API'
    )
    parser.add_argument(
        '--no-frontend',
        action='store_true',
        help='Do not start frontend'
    )
    parser.add_argument(
        '--skip-load',
        action='store_true',
        help='Skip loading data (assumes emulator already has data)'
    )
    
    args = parser.parse_args()
    
    # Track processes for cleanup
    processes = []
    
    def cleanup():
        """Cleanup function to stop all processes."""
        print_status("Stopping all processes...")
        for process in processes:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        print_success("All processes stopped")
    
    atexit.register(cleanup)
    
    # Handle Ctrl+C
    def signal_handler(sig, frame):
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}")
    print("SpendSense Emulator Test Setup")
    print("="*60 + Colors.END)
    print()
    
    # Step 1: Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Step 2: Check data files
    print_status("Checking data files...")
    data_status = check_data_files()
    
    if args.data_source == "sqlite" and not data_status['sqlite_exists']:
        print_error("SQLite database not found")
        print_warning("Try running: python -m src.ingest.regenerate_data")
        sys.exit(1)
    
    if args.data_source == "csv" and not data_status['csv_exists']:
        print_error("CSV files not found")
        print_warning("Try running: python -m src.ingest.regenerate_data")
        sys.exit(1)
    
    print_success("Data files found")
    print()
    
    # Step 3: Start Firebase emulator
    emulator_process = start_firebase_emulator()
    if not emulator_process:
        sys.exit(1)
    processes.append(emulator_process)
    print()
    
    # Step 4: Load data into emulator
    if not args.skip_load:
        if not load_data_to_emulator(args.data_source):
            print_error("Failed to load data into emulator")
            cleanup()
            sys.exit(1)
        print()
    
    # Step 5: Start backend API
    backend_process = None
    if not args.no_backend:
        backend_process = start_backend_api()
        if backend_process:
            processes.append(backend_process)
        print()
    
    # Step 6: Start frontend
    frontend_process = None
    if not args.no_frontend:
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(frontend_process)
        print()
    
    # Summary
    print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}")
    print("Setup Complete!")
    print("="*60 + Colors.END)
    print()
    print("Services running:")
    print(f"  - Firebase Emulator UI: http://localhost:4000")
    print(f"  - Firestore: localhost:8080")
    if backend_process:
        print(f"  - Backend API: http://localhost:8000")
        print(f"  - API Docs: http://localhost:8000/docs")
    if frontend_process:
        print(f"  - Frontend: http://localhost:5173")
    print()
    print(f"{Colors.YELLOW}Press Ctrl+C to stop all services{Colors.END}")
    print()
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
            # Check if any process died
            for i, process in enumerate(processes):
                if process and process.poll() is not None:
                    stdout, stderr = process.communicate()
                    print_error(f"Process {i} died unexpectedly")
                    if stderr:
                        print(stderr)
                    cleanup()
                    sys.exit(1)
    except KeyboardInterrupt:
        cleanup()
        sys.exit(0)

if __name__ == "__main__":
    main()

