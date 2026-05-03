#!/usr/bin/env python3
"""
Simple restore script for SQLite database.
"""
import os
import shutil
import gzip
from pathlib import Path
from backend.db.database import db

def restore_latest_backup():
    """Restore from the most recent backup."""
    backups_dir = Path("backups")
    if not backups_dir.exists():
        print("No backups directory found")
        return False
    
    # Find most recent backup
    backups = list(backups_dir.glob("simulator_backup_*.db"))
    if not backups:
        print("No backup files found")
        return False
    
    latest_backup = max(backups, key=lambda x: x.stat().st_mtime)
    print(f"Restoring from: {latest_backup}")
    
    # Close connection
    db.close()
    
    # Backup current DB
    current_backup = Path(f"{db.db_path}.pre_restore")
    if Path(db.db_path).exists():
        shutil.copy2(db.db_path, current_backup)
        print(f"Backed up current DB to: {current_backup}")
    
    # Restore
    shutil.copy2(latest_backup, db.db_path)
    print("Restore completed successfully")
    return True

if __name__ == "__main__":
    restore_latest_backup()
