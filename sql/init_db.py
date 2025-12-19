import sqlite3
from pathlib import Path

# Database path - in the sql folder
DB_PATH = Path(__file__).parent / 'swipes.db'
# DB_PATH = os.path.expanduser('~/Documents/DATABASES/swipes.db')

def init_database():
    """Initialize the database with the swipes table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create swipes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS swipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_id INTEGER NOT NULL,
            date_title TEXT NOT NULL,
            product_name TEXT,
            price REAL,
            device_id TEXT,
            is_liked INTEGER DEFAULT 0,
            is_superliked INTEGER DEFAULT 0,
            is_passed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == '__main__':
    init_database()
