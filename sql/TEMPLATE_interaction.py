import sqlite3

DB_PATH = '/var/lib/mysite/database.db'

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# --- READ (SELECT) ---
cursor.execute('SELECT * FROM users')
all_users = cursor.fetchall()  # Returns list of tuples

cursor.execute('SELECT * FROM users WHERE id = ?', (1,))
one_user = cursor.fetchone()  # Returns single tuple or None

# --- WRITE (INSERT) ---
cursor.execute(
    'INSERT INTO users (username, email) VALUES (?, ?)',
    ('john_doe', 'john@example.com')
)
conn.commit()  # IMPORTANT: Must commit to save changes

# Get the ID of inserted row
user_id = cursor.lastrowid

# --- UPDATE ---
cursor.execute(
    'UPDATE users SET email = ? WHERE id = ?',
    ('newemail@example.com', 1)
)
conn.commit()

# --- DELETE ---
cursor.execute('DELETE FROM users WHERE id = ?', (1,))
conn.commit()

# Close connection when done
conn.close()

def add_user(username, email):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, email) VALUES (?, ?)',
            (username, email)
        )
        conn.commit()
        return cursor.lastrowid

def get_users():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        return cursor.fetchall()