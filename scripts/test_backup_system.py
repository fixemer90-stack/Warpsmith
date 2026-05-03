#!/usr/bin/env python3
"""
Test script to verify backup system functionality.
"""
import os
from pathlib import Path
from backend.db.database import db

def test_backup_system():
    """Test that the backup system components are in place."""
    print("Testing backup system...")
    
    # Check that required directories exist
    backups_dir = Path("backups")
    scripts_dir = Path("scripts")
    
    print(f"Backups directory exists: {backups_dir.exists()}")
    print(f"Scripts directory exists: {scripts_dir.exists()}")
    
    # Check that our scripts exist
    backup_script = scripts_dir / "backup_db.py"
    restore_script = scripts_dir / "restore_db.py"
    
    print(f"Backup script exists: {backup_script.exists()}")
    print(f"Restore script exists: {restore_script.exists()}")
    
    # Check database file exists
    db_path = Path(db.db_path)
    print(f"Database file exists: {db_path.exists()}")
    if db_path.exists():
        print(f"Database size: {db_path.stat().st_size} bytes")
    
    print("Backup system test completed")

if __name__ == "__main__":
    test_backup_system()
