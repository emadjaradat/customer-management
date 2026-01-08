import sqlite3
import os
from datetime import datetime

def create_backup():
    """Create a backup of the database."""
    db_path = 'customers.db'
    if not os.path.exists(db_path):
        print("Database file not found.")
        return

    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'customers_backup_{timestamp}.sql')

    conn = sqlite3.connect(db_path)
    with open(backup_path, 'w') as f:
        for line in conn.iterdump():
            f.write('%s\n' % line)
    conn.close()

    print(f"Backup created: {backup_path}")

if __name__ == '__main__':
    create_backup()
