import sqlite3
import os

DB_PATH = "hubbops.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database not found, skipping migration (will be created fresh)")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("SELECT deleted_at FROM service LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding deleted_at column to service table...")
        try:
            cursor.execute("ALTER TABLE service ADD COLUMN deleted_at TIMESTAMP")
            conn.commit()
            print("Migration successful")
        except Exception as e:
            print(f"Migration failed: {e}")
    else:
        print("Column deleted_at already exists")
    
    conn.close()

if __name__ == "__main__":
    migrate()
