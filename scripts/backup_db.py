#!/usr/bin/env python3
"""
SQLite backup strategy for Warpsmith simulator.
Handles backing up and restoring the simulator database.
"""

import os
import sqlite3
import shutil
import gzip
import json
from datetime import datetime
from pathlib import Path
from backend.db.database import db

def backup_database():
    """Create a backup of the SQLite database."""
    # Ensure backups directory exists
    backups_dir = Path("backups")
    backups_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backups_dir / f"simulator_backup_{timestamp}.db"
    
    # Perform the backup
    try:
        # Close any existing connections to ensure clean backup
        db.close()
        
        # Copy the database file
        shutil.copy2(db.db_path, backup_file)
        
        # Also create a compressed version
        compressed_file = backups_dir / f"simulator_backup_{timestamp}.db.gz"
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Create metadata file
        metadata = {
            "timestamp": timestamp,
            "original_path": str(db.db_path),
            "backup_path": str(backup_file),
            "compressed_path": str(compressed_file),
            "size_bytes": os.path.getsize(backup_file),
            "compressed_size_bytes": os.path.getsize(compressed_file)
        }
        
        metadata_file = backups_dir / f"simulator_backup_{timestamp}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        print(f"Backup created successfully:")
        print(f"  - Database: {backup_file}")
        print(f"  - Compressed: {compressed_file}")
        print(f"  - Metadata: {metadata_file}")
        
        return backup_file
        
    except Exception as e:
        print(f"Error during backup: {e}")
        return None

def restore_database(backup_path=None, compressed=False):
    """Restore the SQLite database from a backup."""
    if backup_path is None:
        # Find the most recent backup
        backups_dir = Path("backups")
        if not backups_dir.exists():
            print("No backups directory found")
            return False
            
        backup_files = list(backups_dir.glob("simulator_backup_*.db"))
        if not backup_files:
            print("No backup files found")
            return False
            
        # Sort by modification time (most recent first)
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        backup_path = backup_files[0]
        compressed = backup_path.suffix == '.gz'
    
    backup_path = Path(backup_path)
    
    if not backup_path.exists():
        print(f"Backup file not found: {backup_path}")
        return False
    
    try:
        # If it's a compressed file, decompress it first
        if compressed or backup_path.suffix == '.gz':
            temp_db = Path("temp_restore.db")
            with gzip.open(backup_path, 'rb') as f_in:
                with open(temp_db, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            db_path_to_use = temp_db
        else:
            db_path_to_use = backup_path
        
        # Close existing connection
        db.close()
        
        # Backup current database (just in case)
        current_backup = Path(db.db_path).with_suffix('.db.pre_restore')
        if Path(db.db_path).exists():
            shutil.copy2(db.db_path, current_backup)
            print(f"Current database backed up to: {current_backup}")
        
        # Copy the backup to the database location
        shutil.copy2(db_path_to_use, db.db_path)
        
        # Clean up temp file if we created one
        if compressed or backup_path.suffix == '.gz':
            temp_db.unlink(missing_ok=True)
        
        # Verify the restored database
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM rosters")
        roster_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"Database restored successfully from: {backup_path}")
        print(f"  - Users: {user_count}")
        print(f"  - Rosters: {roster_count}")
        
        return True
        
    except Exception as e:
        print(f"Error during restore: {e}")
        return False

def list_backups():
    """List all available backups."""
    backups_dir = Path("backups")
    if not backups_dir.exists():
        print("No backups directory found")
        return
    
    # Find all backup files and metadata
    backup_files = list(backups_dir.glob("simulator_backup_*.db")) + \
                   list(backups_dir.glob("simulator_backup_*.db.gz"))
    
    if not backup_files:
        print("No backup files found")
        return
    
    print("Available backups:")
    print("-" * 80)
    
    for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
        stat = backup_file.stat()
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size_mb = stat.st_size / (1024 * 1024)
        
        # Check if there's metadata
        metadata_file = backups_dir / f"{backup_file.stem}_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                timestamp = metadata.get("timestamp", "unknown")
            except:
                timestamp = "unknown"
        else:
            timestamp = "unknown"
        
        backup_type = "Compressed" if backup_file.suffix == '.gz' else "Database"
        print(f"{backup_file.name}")
        print(f"  Type: {backup_type}")
        print(f"  Timestamp: {timestamp}")
        print(f"  Modified: {modified}")
        print(f"  Size: {size_mb:.2f} MB")
        print()

def cleanup_old_backups(keep_count=10):
    """Remove old backups, keeping only the most recent ones."""
    backups_dir = Path("backups")
    if not backups_dir.exists():
        print("No backups directory found")
        return
    
    # Find all backup files and metadata
    backup_files = list(backups_dir.glob("simulator_backup_*.db")) + \
                   list(backups_dir.glob("simulator_backup_*.db.gz"))
    metadata_files = list(backups_dir.glob("simulator_backup_*_metadata.json"))
    
    all_files = backup_files + metadata_files
    
    if len(all_files) <= keep_count * 3:  # Each backup has db, .gz, and metadata
        print(f"Only {len(all_files)} files found, keeping all")
        return
    
    # Sort by modification time (oldest first)
    all_files.sort(key=lambda x: x.stat().st_mtime)
    
    # Files to remove (oldest ones)
    to_remove = all_files[:-keep_count * 3]
    
    removed_count = 0
    for file_path in to_remove:
        try:
            file_path.unlink()
            removed_count += 1
        except Exception as e:
            print(f"Error removing {file_path}: {e}")
    
    print(f"Cleaned up {removed_count} old backup files")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/backup_db.py backup     - Create a new backup")
        print("  python scripts/backup_db.py restore    - Restore from most recent backup")
        print("  python scripts/backup_db.py restore <backup_file> - Restore from specific backup")
        print("  python scripts/backup_db.py list       - List all available backups")
        print("  python scripts/backup_db.py cleanup    - Remove old backups (keep 10)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "backup":
        backup_database()
    elif command == "restore":
        backup_path = sys.argv[2] if len(sys.argv) > 2 else None
        restore_database(backup_path)
    elif command == "list":
        list_backups()
    elif command == "cleanup":
        cleanup_old_backups()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
