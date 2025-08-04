#!/usr/bin/env python3
"""
Script to run Alembic migrations for Roundtable.
This script runs all pending Alembic migrations to update the database schema.
"""

import os
import sys
import subprocess

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_migrations():
    """Run all pending Alembic migrations"""
    try:
        print("Running Alembic migrations...")
        
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Run Alembic upgrade command
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        
        print("Migration output:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)
        
        print("Database migrations completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")
        print("Command output:")
        print(e.stdout)
        print("Error output:")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error running migrations: {e}")
        return False


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
